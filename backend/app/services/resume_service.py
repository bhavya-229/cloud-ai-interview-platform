import io
import logging
from typing import Optional
from pypdf import PdfReader
from sqlalchemy.orm import Session
from app.models.resume import Resume
from app.services.storage_service import StorageService, get_storage_service

logger = logging.getLogger(__name__)


class ResumeService:
    def __init__(self, storage_service: Optional[StorageService] = None):
        self.storage = storage_service or get_storage_service()

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract plain text from PDF bytes using pypdf."""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text_parts = []
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())

            extracted = "\n\n".join(text_parts).strip()
            if not extracted:
                return "No readable text could be extracted from this PDF. (Scanned document or empty pages)"
            return extracted
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise ValueError(f"Could not parse PDF content: {str(e)}")

    def process_and_save_resume(
        self,
        db: Session,
        candidate_id: int,
        filename: str,
        file_bytes: bytes
    ) -> Resume:
        """Persist resume using storage abstraction and record in database."""
        # 1. Extract text
        extracted_text = self.extract_text_from_pdf(file_bytes)

        # 2. Store file via storage abstraction
        stored_path = self.storage.upload_file(
            file_bytes=file_bytes,
            filename=filename,
            subfolder=f"candidate_{candidate_id}"
        )

        # 3. Create or update resume in database
        resume = Resume(
            candidate_id=candidate_id,
            file_name=filename,
            file_path=stored_path,
            extracted_text=extracted_text
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume

    def get_candidate_latest_resume(self, db: Session, candidate_id: int) -> Optional[Resume]:
        """Fetch the most recently uploaded resume for a candidate."""
        return db.query(Resume).filter(
            Resume.candidate_id == candidate_id
        ).order_by(Resume.uploaded_at.desc()).first()
