"""
MinIO client for object storage operations.

This module provides a client for interacting with MinIO object storage
for storing and retrieving artifacts and files.
"""

import io
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, BinaryIO
from urllib.parse import urlparse
import hashlib

from minio import Minio
from minio.error import S3Error
import structlog

from ..core.config import settings
from ..core.utils import get_logger, generate_uuid, clean_filename

logger = get_logger(__name__)


class MinIOClient:
    """MinIO client for object storage operations."""
    
    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
        self.bucket_name = settings.minio_bucket_name
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the default bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Failed to create bucket {self.bucket_name}: {e}")
            raise
    
    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload a file to MinIO.
        
        Args:
            file_path: Path to the file to upload
            object_name: Name for the object in MinIO (optional)
            content_type: MIME type of the file (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            str: Object name in MinIO
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Generate object name if not provided
            if not object_name:
                filename = clean_filename(os.path.basename(file_path))
                object_name = f"{generate_uuid()}/{filename}"
            
            # Determine content type if not provided
            if not content_type:
                content_type = self._get_content_type(file_path)
            
            # Upload file
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
                metadata=metadata
            )
            
            logger.info(f"Uploaded file {file_path} as {object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading file {file_path}: {e}")
            raise
    
    def upload_data(
        self,
        data: bytes,
        object_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Upload data bytes to MinIO.
        
        Args:
            data: Data bytes to upload
            object_name: Name for the object in MinIO
            content_type: MIME type of the data (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            str: Object name in MinIO
        """
        try:
            data_stream = io.BytesIO(data)
            
            # Determine content type if not provided
            if not content_type:
                content_type = "application/octet-stream"
            
            # Upload data
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=data_stream,
                length=len(data),
                content_type=content_type,
                metadata=metadata
            )
            
            logger.info(f"Uploaded data as {object_name} ({len(data)} bytes)")
            return object_name
            
        except S3Error as e:
            logger.error(f"Failed to upload data as {object_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading data as {object_name}: {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Download a file from MinIO.
        
        Args:
            object_name: Name of the object in MinIO
            file_path: Path where to save the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Download file
            self.client.fget_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=file_path
            )
            
            logger.info(f"Downloaded {object_name} to {file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to download {object_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {object_name}: {e}")
            return False
    
    def download_data(self, object_name: str) -> Optional[bytes]:
        """
        Download data from MinIO as bytes.
        
        Args:
            object_name: Name of the object in MinIO
            
        Returns:
            Optional[bytes]: Data bytes or None if failed
        """
        try:
            # Download data
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded {object_name} ({len(data)} bytes)")
            return data
            
        except S3Error as e:
            logger.error(f"Failed to download {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading {object_name}: {e}")
            return None
    
    def delete_object(self, object_name: str) -> bool:
        """
        Delete an object from MinIO.
        
        Args:
            object_name: Name of the object to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            logger.info(f"Deleted object: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to delete {object_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting {object_name}: {e}")
            return False
    
    def list_objects(
        self,
        prefix: Optional[str] = None,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List objects in the bucket.
        
        Args:
            prefix: Object name prefix to filter by (optional)
            recursive: Whether to list recursively (optional)
            
        Returns:
            List[Dict[str, Any]]: List of object information
        """
        try:
            objects = []
            for obj in self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=recursive
            ):
                objects.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                })
            
            logger.info(f"Listed {len(objects)} objects")
            return objects
            
        except S3Error as e:
            logger.error(f"Failed to list objects: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing objects: {e}")
            return []
    
    def get_object_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an object.
        
        Args:
            object_name: Name of the object
            
        Returns:
            Optional[Dict[str, Any]]: Object information or None
        """
        try:
            stat = self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            return {
                "name": object_name,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata,
            }
            
        except S3Error as e:
            logger.error(f"Failed to get info for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting info for {object_name}: {e}")
            return None
    
    def object_exists(self, object_name: str) -> bool:
        """
        Check if an object exists.
        
        Args:
            object_name: Name of the object
            
        Returns:
            bool: True if object exists, False otherwise
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True
        except S3Error:
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking existence of {object_name}: {e}")
            return False
    
    def get_presigned_url(
        self,
        object_name: str,
        method: str = "GET",
        expires: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for an object.
        
        Args:
            object_name: Name of the object
            method: HTTP method (GET, PUT, POST)
            expires: URL expiration time in seconds
            
        Returns:
            Optional[str]: Presigned URL or None
        """
        try:
            url = self.client.presigned_url(
                method=method,
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            
            logger.info(f"Generated presigned URL for {object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL for {object_name}: {e}")
            return None
    
    def _get_content_type(self, file_path: str) -> str:
        """
        Get content type based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: MIME type
        """
        extension = Path(file_path).suffix.lower()
        
        content_types = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".html": "text/html",
            ".htm": "text/html",
            ".json": "application/json",
            ".xml": "application/xml",
            ".csv": "text/csv",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        
        return content_types.get(extension, "application/octet-stream")
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[str]: SHA256 hash or None
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return None


# Global MinIO client instance
minio_client = MinIOClient()
