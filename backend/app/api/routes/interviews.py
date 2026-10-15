from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.interview import Interview, InterviewStatus
from app.models.user import User, UserRole
from app.schemas.interview import InterviewCreate, InterviewResponse, InterviewDetailResponse
from app.schemas.answer import AnswerSubmit
from app.api.dependencies import get_current_user, get_current_candidate
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["Interviews"])
interview_service = InterviewService()


@router.post("", response_model=InterviewDetailResponse, status_code=status.HTTP_201_CREATED)
def start_interview(
    interview_in: InterviewCreate,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Candidate: Initiate an interview for a specific job. LLM generates Question 1."""
    try:
        interview = interview_service.start_interview(
            db=db,
            candidate_id=current_candidate.id,
            job_id=interview_in.job_id
        )
        return interview
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Interview initiation error: {str(e)}")


@router.get("/{interview_id}", response_model=InterviewDetailResponse)
def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Candidate/Recruiter: Retrieve interview details with questions and submitted answers."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    # Access check: Candidate must own it; Recruiter must own the job or have recruiter role
    if current_user.role == UserRole.CANDIDATE and interview.candidate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if current_user.role == UserRole.RECRUITER and interview.job.recruiter_id != current_user.id:
        # Check if this recruiter owns the job
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to other recruiters' jobs.")

    return interview


@router.post("/{interview_id}/answer")
def submit_interview_answer(
    interview_id: int,
    answer_in: AnswerSubmit,
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Candidate: Submit an answer to a question. Evaluates answer and generates follow-up question or finalizes."""
    try:
        result = interview_service.submit_answer(
            db=db,
            interview_id=interview_id,
            candidate_id=current_candidate.id,
            question_id=answer_in.question_id,
            answer_text=answer_in.answer_text
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Evaluation failed: {str(e)}")


@router.get("/{interview_id}/results")
def get_interview_results(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Candidate/Recruiter: Fetch synthesized assessment report and question-by-question evaluations."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found.")

    if current_user.role == UserRole.CANDIDATE and interview.candidate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    if current_user.role == UserRole.RECRUITER and interview.job.recruiter_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if interview.status != InterviewStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment report is only available after interview completion."
        )

    import json
    feedback_data = json.loads(interview.final_feedback) if interview.final_feedback else {}

    # Format question-by-question breakdown
    breakdown = []
    for q in interview.questions:
        ans = q.answers[0] if q.answers else None
        ans_feedback = json.loads(ans.feedback) if (ans and ans.feedback) else {}
        breakdown.append({
            "sequence_number": q.sequence_number,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "answer_text": ans.answer_text if ans else None,
            "score": ans.score if ans else 0.0,
            "evaluation": ans_feedback
        })

    return {
        "interview_id": interview.id,
        "candidate_id": interview.candidate_id,
        "candidate_name": interview.candidate.name if interview.candidate else None,
        "job_title": interview.job.title if interview.job else None,
        "overall_score": interview.overall_score,
        "completed_at": interview.completed_at,
        "assessment_report": feedback_data,
        "breakdown": breakdown
    }
