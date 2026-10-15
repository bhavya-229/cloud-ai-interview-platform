import os
import uuid
import shutil
from abc import ABC, abstractmethod
from typing import Optional
from app.core.config import settings


class StorageService(ABC):
    """Abstract base storage service to decouple business logic from storage backends.
    
    This ensures switching from local disk storage to Amazon S3 in the cloud phase
    requires no modifications to consumer services.
    """

    @abstractmethod
    def upload_file(self, file_bytes: bytes, filename: str, subfolder: Optional[str] = None) -> str:
        """Uploads a file and returns its storage path or URI."""
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> bytes:
        """Retrieves raw bytes for a stored file."""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Deletes a file from storage."""
        pass


class LocalStorageService(StorageService):
    """Local disk implementation of StorageService for development and testing."""

    def __init__(self, base_dir: Optional[str] = None):
        # Anchor uploads directory relative to backend folder or configured path
        if base_dir:
            self.base_dir = base_dir
        else:
            # Resolve relative to current working directory or backend/uploads
            base = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), settings.UPLOAD_DIR)
            self.base_dir = os.path.abspath(base)
        os.makedirs(self.base_dir, exist_ok=True)

    def upload_file(self, file_bytes: bytes, filename: str, subfolder: Optional[str] = None) -> str:
        target_dir = self.base_dir
        if subfolder:
            target_dir = os.path.join(self.base_dir, subfolder)
            os.makedirs(target_dir, exist_ok=True)

        # Sanitize filename and add unique prefix to prevent collisions
        safe_name = os.path.basename(filename).replace(" ", "_")
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        full_path = os.path.join(target_dir, unique_name)

        with open(full_path, "wb") as f:
            f.write(file_bytes)

        return full_path

    def get_file(self, file_path: str) -> bytes:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Stored file not found: {file_path}")
        with open(file_path, "rb") as f:
            return f.read()

    def delete_file(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False


class S3StorageService(StorageService):
    """Placeholder S3 storage service abstraction for the upcoming AWS phase."""

    def __init__(self, bucket_name: str = "cloud-ai-interview-resumes"):
        self.bucket_name = bucket_name

    def upload_file(self, file_bytes: bytes, filename: str, subfolder: Optional[str] = None) -> str:
        raise NotImplementedError("S3StorageService will be activated in the AWS Cloud phase.")

    def get_file(self, file_path: str) -> bytes:
        raise NotImplementedError("S3StorageService will be activated in the AWS Cloud phase.")

    def delete_file(self, file_path: str) -> bool:
        raise NotImplementedError("S3StorageService will be activated in the AWS Cloud phase.")


# Factory/Singleton provider for storage service
def get_storage_service() -> StorageService:
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageService()
    return LocalStorageService()
