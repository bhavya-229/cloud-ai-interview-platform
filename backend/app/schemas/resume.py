from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    id: int
    candidate_id: int
    file_name: str
    file_path: str
    extracted_text: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
