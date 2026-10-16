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
    """Amazon S3 implementation of StorageService using boto3.
    
    Uses IAM role credentials automatically when running on EC2 or Lambda,
    or standard AWS CLI environment credentials locally.
    """

    def __init__(self, bucket_name: Optional[str] = None, region_name: Optional[str] = None):
        import boto3
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.region_name = region_name or settings.AWS_REGION
        self.s3_client = boto3.client("s3", region_name=self.region_name)

    def _extract_key(self, file_path: str) -> str:
        """Helper to extract S3 object key from full S3 URI or relative path."""
        if file_path.startswith("s3://"):
            parts = file_path[5:].split("/", 1)
            return parts[1] if len(parts) > 1 else parts[0]
        return file_path

    def upload_file(self, file_bytes: bytes, filename: str, subfolder: Optional[str] = None) -> str:
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME is not configured in settings or environment.")

        safe_name = os.path.basename(filename).replace(" ", "_")
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        object_key = f"{subfolder}/{unique_name}" if subfolder else unique_name

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=file_bytes,
            ContentType="application/pdf"
        )
        return f"s3://{self.bucket_name}/{object_key}"

    def get_file(self, file_path: str) -> bytes:
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME is not configured.")

        key = self._extract_key(file_path)
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()

    def delete_file(self, file_path: str) -> bool:
        if not self.bucket_name:
            return False
        try:
            key = self._extract_key(file_path)
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    def generate_presigned_url(self, file_path: str, expiration_seconds: int = 3600) -> str:
        """Generate a temporary presigned URL for secure candidate/recruiter PDF downloads."""
        key = self._extract_key(file_path)
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expiration_seconds
        )


# Factory provider for storage service
def get_storage_service() -> StorageService:
    if settings.STORAGE_BACKEND.lower() == "s3":
        return S3StorageService()
    return LocalStorageService()
