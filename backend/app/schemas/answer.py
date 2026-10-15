from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str = Field(..., min_length=2)


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_text: str
    score: float
    feedback: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LLMEvaluationOutput(BaseModel):
    score: float = Field(..., ge=0.0, le=10.0, description="Evaluation score out of 10")
    correctness: str = Field(..., description="Assessment of correctness e.g. Excellent, Good, Partial, Poor")
    strengths: List[str] = Field(default_factory=list, description="Key candidate strengths observed")
    weaknesses: List[str] = Field(default_factory=list, description="Observed gaps or weaknesses")
    feedback: str = Field(..., description="Constructive feedback for the candidate")


class LLMFinalAssessmentOutput(BaseModel):
    overall_performance: str = Field(..., description="High-level performance summary")
    technical_strengths: List[str] = Field(default_factory=list, description="Candidate key strengths")
    weak_areas: List[str] = Field(default_factory=list, description="Candidate key weaknesses")
    topics_to_improve: List[str] = Field(default_factory=list, description="Specific topics or skills to review")
    interview_summary: str = Field(..., description="Concise assessment report summary")
    recommendation: str = Field(..., description="Hiring recommendation e.g. Strong Hire, Hire, Consider, Do Not Hire")
