import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.interview import Interview, InterviewStatus
from app.models.job import Job
from app.models.question import Question
from app.models.answer import Answer
from app.models.user import User
from app.services.llm_service import LLMService
from app.services.assessment_service import AssessmentService
from app.services.resume_service import ResumeService

logger = logging.getLogger(__name__)


class InterviewService:
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        assessment_service: Optional[AssessmentService] = None,
        resume_service: Optional[ResumeService] = None
    ):
        self.llm = llm_service or LLMService()
        self.assessment = assessment_service or AssessmentService(llm_service=self.llm)
        self.resume = resume_service or ResumeService()

    def start_interview(self, db: Session, candidate_id: int, job_id: int) -> Interview:
        """Initialize an interview, load candidate/job context, and generate Question 1."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with id {job_id} does not exist.")

        # Check candidate latest resume
        resume = self.resume.get_candidate_latest_resume(db, candidate_id)
        resume_text = resume.extracted_text if resume else ""

        # Create Interview record
        interview = Interview(
            candidate_id=candidate_id,
            job_id=job_id,
            status=InterviewStatus.IN_PROGRESS
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)

        # Generate initial question via LLM
        q1_data = self.llm.generate_initial_question(
            job_title=job.title,
            job_description=job.description,
            required_skills=job.required_skills,
            resume_text=resume_text
        )

        q1 = Question(
            interview_id=interview.id,
            question_text=q1_data.question,
            question_type=q1_data.question_type,
            difficulty=q1_data.difficulty,
            sequence_number=1
        )
        db.add(q1)
        db.commit()
        db.refresh(interview)
        return interview

    def submit_answer(
        self,
        db: Session,
        interview_id: int,
        candidate_id: int,
        question_id: int,
        answer_text: str
    ) -> Dict[str, Any]:
        """Evaluate candidate answer, persist evaluation, and adaptively generate next question or finalize."""
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError("Interview not found.")

        if interview.candidate_id != candidate_id:
            raise PermissionError("Candidate not authorized for this interview.")

        if interview.status == InterviewStatus.COMPLETED:
            raise ValueError("This interview is already completed.")

        question = db.query(Question).filter(
            Question.id == question_id,
            Question.interview_id == interview.id
        ).first()
        if not question:
            raise ValueError("Question not found in this interview.")

        # Check if already answered
        existing_answer = db.query(Answer).filter(Answer.question_id == question.id).first()
        if existing_answer:
            raise ValueError("This question has already been answered.")

        job = interview.job
        resume = self.resume.get_candidate_latest_resume(db, candidate_id)
        resume_text = resume.extracted_text if resume else ""

        # 1. LLM evaluation of answer
        evaluation = self.llm.evaluate_answer(
            job_title=job.title if job else "",
            required_skills=job.required_skills if job else "",
            question_text=question.question_text,
            question_type=question.question_type,
            difficulty=question.difficulty,
            answer_text=answer_text,
            resume_text=resume_text
        )

        # 2. Persist answer record
        answer_record = Answer(
            question_id=question.id,
            answer_text=answer_text,
            score=evaluation.score,
            feedback=json.dumps(evaluation.model_dump())
        )
        db.add(answer_record)
        db.commit()
        db.refresh(answer_record)

        # 3. Determine if more questions are needed
        total_target = settings.INTERVIEW_QUESTION_COUNT
        answered_questions = db.query(Question).join(Answer).filter(
            Question.interview_id == interview.id
        ).all()
        answered_count = len(answered_questions)

        result: Dict[str, Any] = {
            "evaluation": evaluation.model_dump(),
            "answer_id": answer_record.id,
            "question_id": question.id,
            "answered_count": answered_count,
            "total_questions": total_target,
            "is_completed": False,
            "next_question": None
        }

        if answered_count < total_target:
            # Build history for adaptive follow-up
            history = []
            for q in answered_questions:
                ans = db.query(Answer).filter(Answer.question_id == q.id).first()
                if ans:
                    history.append({
                        "question": q.question_text,
                        "answer": ans.answer_text,
                        "score": ans.score,
                        "feedback": ans.feedback
                    })

            next_seq = answered_count + 1
            next_q_data = self.llm.generate_followup_question(
                job_title=job.title if job else "",
                job_description=job.description if job else "",
                required_skills=job.required_skills if job else "",
                resume_text=resume_text,
                previous_history=history,
                current_sequence=next_seq
            )

            next_q = Question(
                interview_id=interview.id,
                question_text=next_q_data.question,
                question_type=next_q_data.question_type,
                difficulty=next_q_data.difficulty,
                sequence_number=next_seq
            )
            db.add(next_q)
            db.commit()
            db.refresh(next_q)

            result["next_question"] = {
                "id": next_q.id,
                "question_text": next_q.question_text,
                "question_type": next_q.question_type,
                "difficulty": next_q.difficulty,
                "sequence_number": next_q.sequence_number
            }
        else:
            # Finalize interview
            completed_interview = self.assessment.finalize_interview(db, interview)
            result["is_completed"] = True
            result["overall_score"] = completed_interview.overall_score
            result["final_feedback"] = json.loads(completed_interview.final_feedback) if completed_interview.final_feedback else None

        return result
