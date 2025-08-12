import uuid
import logging
import mimetypes
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, BinaryIO

from minio.error import S3Error

from .minio_client import minio_client

class ArtifactStorage:
    def __init__(self, client=minio_client):
        self.minio_client = client
        self.logger = logging.getLogger(__name__)

    def upload_artifact(
        self,
        file_data: BinaryIO,
        filename: str,
        bucket_name: str = "artifacts",
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload an artifact to MinIO"""

        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1]
        object_name = f"{user_id}/{file_id}{file_extension}" if user_id else f"public/{file_id}{file_extension}"

        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'

        file_data.seek(0, os.SEEK_END)
        file_size = file_data.tell()
        file_data.seek(0)

        content_hash = self._calculate_hash(file_data)
        file_data.seek(0)

        upload_metadata = {
            'original-filename': filename,
            'content-hash': content_hash,
            'upload-timestamp': datetime.utcnow().isoformat(),
        }
        if user_id:
            upload_metadata['user-id'] = user_id
        if metadata:
            upload_metadata.update(metadata)

        try:
            self.minio_client.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
                metadata=upload_metadata
            )

            return {
                'file_id': file_id,
                'object_name': object_name,
                'bucket': bucket_name,
                'content_hash': content_hash,
                'content_type': content_type,
                'file_size': file_size,
                'metadata': upload_metadata
            }

        except S3Error as e:
            self.logger.error(f"Failed to upload artifact: {e}")
            raise

    def download_artifact(self, object_name: str, bucket_name: str = "artifacts") -> Optional[BinaryIO]:
        """Download an artifact from MinIO"""
        try:
            response = self.minio_client.client.get_object(bucket_name, object_name)
            return response
        except S3Error as e:
            if e.code == 'NoSuchKey':
                self.logger.warning(f"Artifact not found: {object_name}")
                return None
            else:
                self.logger.error(f"Failed to download artifact: {e}")
                raise

    def get_artifact_metadata(self, object_name: str, bucket_name: str = "artifacts") -> Optional[Dict[str, Any]]:
        """Get metadata for an artifact"""
        try:
            stat = self.minio_client.client.stat_object(bucket_name, object_name)
            return {
                'size': stat.size,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified,
                'metadata': stat.metadata
            }
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            else:
                self.logger.error(f"Failed to get artifact metadata: {e}")
                raise

    def generate_presigned_url(self, object_name: str, bucket_name: str = "artifacts", expires_sec: int = 3600) -> Optional[str]:
        """Generate a presigned URL for secure access"""
        try:
            url = self.minio_client.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires_sec)
            )
            return url
        except S3Error as e:
            self.logger.error(f"Failed to generate presigned URL: {e}")
            return None

    def _calculate_hash(self, file_data: BinaryIO) -> str:
        """Calculate SHA-256 hash of file content"""
        hash_sha256 = hashlib.sha256()
        for chunk in iter(lambda: file_data.read(4096), b""):
            hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

artifact_storage_service = ArtifactStorage()
