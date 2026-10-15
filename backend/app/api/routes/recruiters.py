from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.interview import Interview
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.schemas.job import JobResponse
from app.schemas.interview import InterviewResponse
from app.schemas.resume import ResumeResponse
from app.schemas.user import UserResponse
from app.api.dependencies import get_current_recruiter

router = APIRouter(prefix="/recruiters", tags=["Recruiters"])


@router.get("/dashboard")
def get_recruiter_dashboard(
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Recruiter dashboard stats: posted jobs, candidate interviews, completed assessments."""
    recruiter_jobs = db.query(Job).filter(Job.recruiter_id == current_recruiter.id).all()
    job_ids = [j.id for j in recruiter_jobs]

    interviews = []
    if job_ids:
        interviews = db.query(Interview).filter(Interview.job_id.in_(job_ids)).order_by(Interview.started_at.desc()).all()

    completed_count = sum(1 for i in interviews if i.status == "completed")
    in_progress_count = sum(1 for i in interviews if i.status == "in_progress")

    return {
        "recruiter": {
            "id": current_recruiter.id,
            "name": current_recruiter.name,
            "email": current_recruiter.email
        },
        "stats": {
            "jobs_posted": len(recruiter_jobs),
            "total_interviews": len(interviews),
            "completed_assessments": completed_count,
            "in_progress_interviews": in_progress_count
        },
        "recent_interviews": [InterviewResponse.model_validate(i) for i in interviews[:5]],
        "jobs": [JobResponse.model_validate(j) for j in recruiter_jobs[:5]]
    }


@router.get("/interviews", response_model=List[InterviewResponse])
def get_recruiter_interviews(
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """List all interviews associated with the recruiter's job postings."""
    recruiter_jobs = db.query(Job).filter(Job.recruiter_id == current_recruiter.id).all()
    job_ids = [j.id for j in recruiter_jobs]
    if not job_ids:
        return []

    interviews = db.query(Interview).filter(
        Interview.job_id.in_(job_ids)
    ).order_by(Interview.started_at.desc()).all()
    return interviews


@router.get("/candidates")
def get_recruiter_candidates(
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """List all unique candidates who took interviews for this recruiter's jobs."""
    recruiter_jobs = db.query(Job).filter(Job.recruiter_id == current_recruiter.id).all()
    job_ids = [j.id for j in recruiter_jobs]
    if not job_ids:
        return []

    interviews = db.query(Interview).filter(Interview.job_id.in_(job_ids)).all()
    candidate_map = {}
    for i in interviews:
        cid = i.candidate_id
        if cid not in candidate_map:
            latest_resume = db.query(Resume).filter(Resume.candidate_id == cid).order_by(Resume.uploaded_at.desc()).first()
            candidate_map[cid] = {
                "candidate": UserResponse.model_validate(i.candidate),
                "latest_resume": ResumeResponse.model_validate(latest_resume) if latest_resume else None,
                "interviews_count": 0,
                "completed_count": 0,
                "highest_score": None
            }
        candidate_map[cid]["interviews_count"] += 1
        if i.status == "completed":
            candidate_map[cid]["completed_count"] += 1
            if i.overall_score is not None:
                current_high = candidate_map[cid]["highest_score"]
                if current_high is None or i.overall_score > current_high:
                    candidate_map[cid]["highest_score"] = i.overall_score

    return list(candidate_map.values())


@router.get("/candidates/{candidate_id}")
def get_candidate_profile(
    candidate_id: int,
    current_recruiter: User = Depends(get_current_recruiter),
    db: Session = Depends(get_db)
):
    """Recruiter: View candidate profile, uploaded resume, and interview history for recruiter's jobs."""
    candidate = db.query(User).filter(User.id == candidate_id, User.role == "candidate").first()
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    latest_resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).order_by(Resume.uploaded_at.desc()).first()

    recruiter_jobs = db.query(Job).filter(Job.recruiter_id == current_recruiter.id).all()
    job_ids = [j.id for j in recruiter_jobs]

    candidate_interviews = []
    if job_ids:
        candidate_interviews = db.query(Interview).filter(
            Interview.candidate_id == candidate_id,
            Interview.job_id.in_(job_ids)
        ).order_by(Interview.started_at.desc()).all()

    return {
        "candidate": UserResponse.model_validate(candidate),
        "latest_resume": ResumeResponse.model_validate(latest_resume) if latest_resume else None,
        "interviews": [InterviewResponse.model_validate(i) for i in candidate_interviews]
    }
