from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.interview import Interview
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.interview import InterviewResponse
from app.schemas.resume import ResumeResponse
from app.api.dependencies import get_current_candidate

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.get("/dashboard")
def get_candidate_dashboard(
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Candidate dashboard summary stats, recent interviews, latest resume, available jobs count."""
    interviews = db.query(Interview).filter(
        Interview.candidate_id == current_candidate.id
    ).order_by(Interview.started_at.desc()).all()

    completed_count = sum(1 for i in interviews if i.status == "completed")
    in_progress_count = sum(1 for i in interviews if i.status == "in_progress")
    available_jobs_count = db.query(Job).count()

    latest_resume = db.query(Resume).filter(
        Resume.candidate_id == current_candidate.id
    ).order_by(Resume.uploaded_at.desc()).first()

    return {
        "candidate": {
            "id": current_candidate.id,
            "name": current_candidate.name,
            "email": current_candidate.email
        },
        "stats": {
            "total_interviews": len(interviews),
            "completed_interviews": completed_count,
            "in_progress_interviews": in_progress_count,
            "available_jobs": available_jobs_count,
            "has_resume": latest_resume is not None
        },
        "latest_resume": ResumeResponse.model_validate(latest_resume) if latest_resume else None,
        "recent_interviews": [InterviewResponse.model_validate(i) for i in interviews[:5]]
    }


@router.get("/interviews", response_model=List[InterviewResponse])
def get_candidate_interviews(
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """List all interviews undertaken by the candidate."""
    interviews = db.query(Interview).filter(
        Interview.candidate_id == current_candidate.id
    ).order_by(Interview.started_at.desc()).all()
    return interviews
