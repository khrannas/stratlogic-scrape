"""
Artifact storage manager for MinIO operations.

This module provides high-level artifact storage operations including
metadata management, access control, and content validation.
"""

import uuid
import hashlib
import mimetypes
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, BinaryIO, List
from pathlib import Path

from minio.error import S3Error
import structlog

from .minio_client import MinIOClient
from ..core.config import settings
from ..core.utils import get_logger, generate_uuid, clean_filename

logger = get_logger(__name__)


class ArtifactStorage:
    """Artifact storage manager for MinIO operations."""
    
    def __init__(self, minio_client: Optional[MinIOClient] = None):
        """Initialize artifact storage manager."""
        self.minio_client = minio_client or MinIOClient()
        self.artifacts_bucket = settings.minio_bucket_name
        self.temp_bucket = "temp"
        self.backup_bucket = "backup"
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self):
        """Ensure all required buckets exist."""
        buckets = [self.artifacts_bucket, self.temp_bucket, self.backup_bucket]
        for bucket in buckets:
            try:
                if not self.minio_client.client.bucket_exists(bucket):
                    self.minio_client.client.make_bucket(bucket)
                    logger.info(f"Created bucket: {bucket}")
            except S3Error as e:
                logger.error(f"Failed to create bucket {bucket}: {e}")
                raise
    
    async def upload_artifact(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        is_public: bool = False,
        job_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload an artifact to MinIO with metadata.
        
        Args:
            file_data: File data to upload
            filename: Original filename
            content_type: MIME type of the file
            metadata: Additional metadata
            user_id: User ID who owns the artifact
            is_public: Whether the artifact is public
            job_id: Associated job ID
            
        Returns:
            Dict containing upload information
        """
        try:
            # Generate unique file path
            file_id = str(generate_uuid())
            file_extension = Path(filename).suffix
            clean_name = clean_filename(filename)
            
            # Create path based on user and visibility
            if user_id:
                file_path = f"users/{user_id}/{file_id}{file_extension}"
            else:
                file_path = f"public/{file_id}{file_extension}"
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or 'application/octet-stream'
            
            # Calculate content hash
            content_hash = self._calculate_hash(file_data)
            
            # Prepare metadata
            upload_metadata = {
                'original_filename': clean_name,
                'content_hash': content_hash,
                'upload_timestamp': datetime.now(timezone.utc).isoformat(),
                'user_id': user_id or '',
                'is_public': str(is_public),
                'job_id': job_id or '',
                'file_extension': file_extension,
                'content_type': content_type
            }
            
            if metadata:
                upload_metadata.update(metadata)
            
            # Reset file pointer for upload
            file_data.seek(0)
            
            # Upload to MinIO
            self.minio_client.upload_data(
                data=file_data.read(),
                object_name=file_path,
                content_type=content_type,
                metadata=upload_metadata
            )
            
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            
            result = {
                'file_id': file_id,
                'file_path': file_path,
                'bucket': self.artifacts_bucket,
                'content_hash': content_hash,
                'content_type': content_type,
                'file_size': file_size,
                'original_filename': clean_name,
                'metadata': upload_metadata,
                'is_public': is_public,
                'user_id': user_id,
                'job_id': job_id
            }
            
            logger.info(f"Uploaded artifact: {file_path} (size: {file_size} bytes)")
            return result
            
        except S3Error as e:
            logger.error(f"Failed to upload artifact: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading artifact: {e}")
            raise
    
    async def download_artifact(
        self,
        file_path: str,
        user_id: Optional[str] = None
    ) -> Optional[BinaryIO]:
        """
        Download an artifact from MinIO.
        
        Args:
            file_path: Path to the artifact in MinIO
            user_id: User ID requesting the download (for access control)
            
        Returns:
            File data as BinaryIO or None if not found/unauthorized
        """
        try:
            # Check if object exists
            if not self.minio_client.object_exists(file_path):
                logger.warning(f"Artifact not found: {file_path}")
                return None
            
            # Get object info for access control
            object_info = self.minio_client.get_object_info(file_path)
            if object_info and object_info.get('metadata'):
                metadata = object_info['metadata']
                artifact_user_id = metadata.get('user_id', '')
                is_public = metadata.get('is_public', 'false').lower() == 'true'
                
                # Check access control
                if not is_public and user_id != artifact_user_id:
                    logger.warning(f"Access denied for artifact: {file_path}")
                    return None
            
            # Download the artifact
            data = self.minio_client.download_data(file_path)
            if data:
                return BinaryIO(data)
            else:
                logger.error(f"Failed to download artifact: {file_path}")
                return None
                
        except S3Error as e:
            logger.error(f"Failed to download artifact {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading artifact {file_path}: {e}")
            return None
    
    async def delete_artifact(
        self,
        file_path: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete an artifact from MinIO.
        
        Args:
            file_path: Path to the artifact in MinIO
            user_id: User ID requesting the deletion (for access control)
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Check if object exists
            if not self.minio_client.object_exists(file_path):
                logger.warning(f"Artifact not found for deletion: {file_path}")
                return False
            
            # Get object info for access control
            object_info = self.minio_client.get_object_info(file_path)
            if object_info and object_info.get('metadata'):
                metadata = object_info['metadata']
                artifact_user_id = metadata.get('user_id', '')
                
                # Check access control (only owner can delete)
                if user_id and user_id != artifact_user_id:
                    logger.warning(f"Access denied for artifact deletion: {file_path}")
                    return False
            
            # Delete the artifact
            success = self.minio_client.delete_object(file_path)
            if success:
                logger.info(f"Deleted artifact: {file_path}")
            else:
                logger.error(f"Failed to delete artifact: {file_path}")
            
            return success
            
        except S3Error as e:
            logger.error(f"Failed to delete artifact {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting artifact {file_path}: {e}")
            return False
    
    async def get_artifact_metadata(
        self,
        file_path: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an artifact.
        
        Args:
            file_path: Path to the artifact in MinIO
            user_id: User ID requesting the metadata (for access control)
            
        Returns:
            Metadata dictionary or None if not found/unauthorized
        """
        try:
            # Check if object exists
            if not self.minio_client.object_exists(file_path):
                logger.warning(f"Artifact not found for metadata: {file_path}")
                return None
            
            # Get object info
            object_info = self.minio_client.get_object_info(file_path)
            if not object_info:
                return None
            
            metadata = object_info.get('metadata', {})
            artifact_user_id = metadata.get('user_id', '')
            is_public = metadata.get('is_public', 'false').lower() == 'true'
            
            # Check access control
            if not is_public and user_id != artifact_user_id:
                logger.warning(f"Access denied for artifact metadata: {file_path}")
                return None
            
            return {
                'file_path': file_path,
                'size': object_info.get('size'),
                'etag': object_info.get('etag'),
                'content_type': object_info.get('content_type'),
                'last_modified': object_info.get('last_modified'),
                'metadata': metadata
            }
            
        except S3Error as e:
            logger.error(f"Failed to get artifact metadata {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting artifact metadata {file_path}: {e}")
            return None
    
    async def list_user_artifacts(
        self,
        user_id: str,
        prefix: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List artifacts for a specific user.
        
        Args:
            user_id: User ID to list artifacts for
            prefix: Optional prefix filter
            limit: Maximum number of artifacts to return
            
        Returns:
            List of artifact information
        """
        try:
            user_prefix = f"users/{user_id}/"
            if prefix:
                user_prefix += prefix
            
            objects = self.minio_client.list_objects(prefix=user_prefix, recursive=True)
            
            artifacts = []
            for obj in objects[:limit]:
                metadata = await self.get_artifact_metadata(obj['name'], user_id)
                if metadata:
                    artifacts.append(metadata)
            
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to list artifacts for user {user_id}: {e}")
            return []
    
    async def list_public_artifacts(
        self,
        prefix: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List public artifacts.
        
        Args:
            prefix: Optional prefix filter
            limit: Maximum number of artifacts to return
            
        Returns:
            List of public artifact information
        """
        try:
            public_prefix = "public/"
            if prefix:
                public_prefix += prefix
            
            objects = self.minio_client.list_objects(prefix=public_prefix, recursive=True)
            
            artifacts = []
            for obj in objects[:limit]:
                metadata = await self.get_artifact_metadata(obj['name'])
                if metadata:
                    artifacts.append(metadata)
            
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to list public artifacts: {e}")
            return []
    
    async def get_presigned_url(
        self,
        file_path: str,
        user_id: Optional[str] = None,
        expires: int = 3600,
        method: str = "GET"
    ) -> Optional[str]:
        """
        Get a presigned URL for secure access to an artifact.
        
        Args:
            file_path: Path to the artifact in MinIO
            user_id: User ID requesting the URL (for access control)
            expires: URL expiration time in seconds
            method: HTTP method (GET, PUT, DELETE)
            
        Returns:
            Presigned URL or None if not found/unauthorized
        """
        try:
            # Check if object exists
            if not self.minio_client.object_exists(file_path):
                logger.warning(f"Artifact not found for presigned URL: {file_path}")
                return None
            
            # Get object info for access control
            object_info = self.minio_client.get_object_info(file_path)
            if object_info and object_info.get('metadata'):
                metadata = object_info['metadata']
                artifact_user_id = metadata.get('user_id', '')
                is_public = metadata.get('is_public', 'false').lower() == 'true'
                
                # Check access control
                if not is_public and user_id != artifact_user_id:
                    logger.warning(f"Access denied for presigned URL: {file_path}")
                    return None
            
            # Generate presigned URL
            url = self.minio_client.get_presigned_url(
                object_name=file_path,
                method=method,
                expires=expires
            )
            
            if url:
                logger.info(f"Generated presigned URL for: {file_path}")
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {file_path}: {e}")
            return None
    
    async def backup_artifact(
        self,
        file_path: str,
        backup_name: Optional[str] = None
    ) -> bool:
        """
        Create a backup of an artifact.
        
        Args:
            file_path: Path to the artifact to backup
            backup_name: Optional custom backup name
            
        Returns:
            True if backup successful, False otherwise
        """
        try:
            # Check if object exists
            if not self.minio_client.object_exists(file_path):
                logger.warning(f"Artifact not found for backup: {file_path}")
                return False
            
            # Generate backup name
            if not backup_name:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}_{Path(file_path).name}"
            
            backup_path = f"backups/{backup_name}"
            
            # Copy object to backup bucket
            self.minio_client.client.copy_object(
                bucket_name=self.backup_bucket,
                object_name=backup_path,
                source=f"{self.artifacts_bucket}/{file_path}"
            )
            
            logger.info(f"Backed up artifact {file_path} to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup artifact {file_path}: {e}")
            return False
    
    async def restore_artifact(
        self,
        backup_path: str,
        restore_path: Optional[str] = None
    ) -> bool:
        """
        Restore an artifact from backup.
        
        Args:
            backup_path: Path to the backup in backup bucket
            restore_path: Optional custom restore path
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            # Check if backup exists
            if not self.minio_client.client.bucket_exists(self.backup_bucket):
                logger.error(f"Backup bucket does not exist: {self.backup_bucket}")
                return False
            
            # Generate restore path
            if not restore_path:
                restore_path = f"restored/{Path(backup_path).name}"
            
            # Copy backup to artifacts bucket
            self.minio_client.client.copy_object(
                bucket_name=self.artifacts_bucket,
                object_name=restore_path,
                source=f"{self.backup_bucket}/{backup_path}"
            )
            
            logger.info(f"Restored artifact from {backup_path} to {restore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore artifact from {backup_path}: {e}")
            return False
    
    def _calculate_hash(self, file_data: BinaryIO) -> str:
        """Calculate SHA-256 hash of file content."""
        hash_sha256 = hashlib.sha256()
        
        # Save current position
        current_pos = file_data.tell()
        
        # Reset to beginning
        file_data.seek(0)
        
        # Calculate hash
        for chunk in iter(lambda: file_data.read(4096), b""):
            hash_sha256.update(chunk)
        
        # Restore position
        file_data.seek(current_pos)
        
        return hash_sha256.hexdigest()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on storage system."""
        try:
            # Check MinIO client health
            minio_health = self.minio_client.health_check()
            
            # Check bucket access
            buckets_accessible = []
            for bucket in [self.artifacts_bucket, self.temp_bucket, self.backup_bucket]:
                try:
                    if self.minio_client.client.bucket_exists(bucket):
                        buckets_accessible.append(bucket)
                except Exception:
                    pass
            
            return {
                'status': 'healthy' if minio_health else 'unhealthy',
                'minio_connection': minio_health,
                'buckets_accessible': buckets_accessible,
                'total_buckets': len(buckets_accessible),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }


# Global artifact storage instance
artifact_storage = ArtifactStorage()
