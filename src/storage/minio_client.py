import logging
from minio import Minio
from minio.error import S3Error

from src.core.config import settings

class MinIOClient:
    def __init__(self):
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self.logger = logging.getLogger(__name__)
            # Only ensure buckets exist if not in test mode
            if not hasattr(settings, 'TESTING') or not settings.TESTING:
                self._ensure_buckets_exist()
        except Exception as e:
            logging.error(f"Failed to initialize MinIO client: {e}")
            raise

    def _ensure_buckets_exist(self):
        """Ensure required buckets exist"""
        buckets = ['artifacts', 'temp', 'backup']
        for bucket in buckets:
            try:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    self.logger.info(f"Created MinIO bucket: {bucket}")
            except S3Error as e:
                self.logger.error(f"Failed to create bucket {bucket}: {e}")
                raise

    def health_check(self) -> bool:
        """Check MinIO connection health"""
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            self.logger.error(f"MinIO health check failed: {e}")
            return False

# Lazy initialization to avoid connection issues during import
_minio_client_instance = None

def get_minio_client():
    """Get or create MinIO client instance"""
    global _minio_client_instance
    if _minio_client_instance is None:
        _minio_client_instance = MinIOClient()
    return _minio_client_instance

# For backward compatibility
minio_client = get_minio_client()
