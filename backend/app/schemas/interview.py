from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.job import JobResponse
from app.schemas.user import UserResponse
from app.schemas.question import QuestionResponse
from app.schemas.answer import AnswerResponse


class InterviewCreate(BaseModel):
    job_id: int


class QuestionWithAnswerResponse(QuestionResponse):
    answers: List[AnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)


class InterviewResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    status: str
    overall_score: Optional[float] = None
    final_feedback: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    job: Optional[JobResponse] = None
    candidate: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewDetailResponse(InterviewResponse):
    questions: List[QuestionWithAnswerResponse] = []

    model_config = ConfigDict(from_attributes=True)
