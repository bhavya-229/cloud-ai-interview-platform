from pydantic import BaseModel, Field, ConfigDict


class QuestionBase(BaseModel):
    question_text: str
    question_type: str = "technical"
    difficulty: str = "medium"
    sequence_number: int


class QuestionCreate(QuestionBase):
    interview_id: int


class QuestionResponse(QuestionBase):
    id: int
    interview_id: int

    model_config = ConfigDict(from_attributes=True)


class LLMQuestionOutput(BaseModel):
    question: str = Field(description="The interview question text")
    question_type: str = Field(default="technical", description="Type: technical, behavioral, or situational")
    difficulty: str = Field(default="medium", description="Difficulty: easy, medium, or hard")
    topic: str = Field(default="General", description="Subject or skill area addressed by the question")
