from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.schemas.resume import ResumeResponse
from app.api.dependencies import get_current_user, get_current_candidate
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["Resumes"])
resume_service = ResumeService()


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Candidate: Upload PDF resume, extract text locally, and store file securely."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF resume files are supported."
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty."
        )

    # Max 10MB limit check
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 10MB limit."
        )

    try:
        resume = resume_service.process_and_save_resume(
            db=db,
            candidate_id=current_candidate.id,
            filename=file.filename,
            file_bytes=content
        )
        return resume
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process PDF resume: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while uploading resume: {str(e)}"
        )


@router.get("/latest", response_model=ResumeResponse)
def get_candidate_latest_resume(
    current_candidate: User = Depends(get_current_candidate),
    db: Session = Depends(get_db)
):
    """Candidate: Retrieve their most recently uploaded resume."""
    resume = resume_service.get_candidate_latest_resume(db, current_candidate.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume has been uploaded yet."
        )
    return resume


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume_by_id(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Candidate/Recruiter: Retrieve resume details by ID."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")

    # Authorization: Candidate can only view their own resume, Recruiters can view candidate resumes
    if current_user.role == UserRole.CANDIDATE and resume.candidate_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden.")

    return resume
