from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.interview import Interview, InterviewStatus
from app.models.question import Question
from app.models.answer import Answer
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class AssessmentService:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    def finalize_interview(self, db: Session, interview: Interview) -> Interview:
        """Calculate aggregate performance score and synthesize final LLM assessment report."""
        # 1. Fetch questions and answers for this interview
        questions = db.query(Question).filter(
            Question.interview_id == interview.id
        ).order_by(Question.sequence_number).all()

        history: List[Dict[str, Any]] = []
        scores: List[float] = []

        for q in questions:
            ans = db.query(Answer).filter(Answer.question_id == q.id).first()
            if ans:
                scores.append(ans.score)
                history.append({
                    "question": q.question_text,
                    "difficulty": q.difficulty,
                    "question_type": q.question_type,
                    "answer": ans.answer_text,
                    "score": ans.score,
                    "feedback": ans.feedback
                })

        # Calculate average overall score (0.0 to 10.0 scale)
        overall_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        # Retrieve resume text for context
        resume_text = ""
        if interview.candidate and interview.candidate.resumes:
            resume_text = interview.candidate.resumes[-1].extracted_text

        # Call LLM for comprehensive structured final assessment
        job_title = interview.job.title if interview.job else "Target Role"
        required_skills = interview.job.required_skills if interview.job else ""

        report_output = self.llm.generate_final_feedback(
            job_title=job_title,
            required_skills=required_skills,
            resume_text=resume_text,
            interview_history=history,
            overall_score=overall_score
        )

        interview.overall_score = overall_score
        interview.final_feedback = json.dumps(report_output.model_dump())
        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.now(timezone.utc)

        db.add(interview)
        db.commit()
        db.refresh(interview)

        # Dispatch real-time alert via Amazon SNS (if configured)
        try:
            from app.services.notification_service import notification_service
            cand_name = interview.candidate.name if interview.candidate else f"Candidate #{interview.candidate_id}"
            notification_service.notify_interview_completed(
                candidate_name=cand_name,
                job_title=job_title,
                overall_score=overall_score,
                recommendation=report_output.recommendation,
                interview_id=interview.id
            )
        except Exception as e:
            logger.warning(f"Could not dispatch interview completion alert: {e}")

        return interview
