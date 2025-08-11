# Task 03: MinIO Storage Integration

## Overview
Implement MinIO object storage integration for storing scraped artifacts, with proper bucket management, metadata handling, and access control.

## Priority: High
## Estimated Time: 2-3 days
## Dependencies: Task 01 (Project Setup), Task 02 (Database Schema)

## Checklist

### 3.1 MinIO Client Setup
- [ ] Install and configure MinIO Python client
- [ ] Create MinIO connection manager
- [ ] Implement bucket management
- [ ] Set up error handling and retry logic
- [ ] Add connection health checks

### 3.2 Storage Operations
- [ ] Implement artifact upload functionality
- [ ] Implement artifact download functionality
- [ ] Implement artifact deletion functionality
- [ ] Add file validation and sanitization
- [ ] Implement chunked upload for large files

### 3.3 Metadata Management
- [ ] Create metadata storage system
- [ ] Implement metadata tagging
- [ ] Add content hash verification
- [ ] Create metadata search functionality
- [ ] Implement metadata backup and recovery

### 3.4 Access Control
- [ ] Implement bucket policies
- [ ] Set up user-based access control
- [ ] Add public/private artifact support
- [ ] Implement signed URLs for secure access
- [ ] Add audit logging for storage operations

## Subtasks

### Subtask 3.1.1: MinIO Client Configuration
```python
# src/storage/minio_client.py
from minio import Minio
from minio.error import S3Error
import logging
from typing import Optional, BinaryIO, Dict, Any
import hashlib
import os

class MinIOClient:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = True):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.logger = logging.getLogger(__name__)
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self):
        """Ensure required buckets exist"""
        buckets = ['artifacts', 'temp', 'backup']
        for bucket in buckets:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                self.logger.info(f"Created bucket: {bucket}")
    
    def health_check(self) -> bool:
        """Check MinIO connection health"""
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            self.logger.error(f"MinIO health check failed: {e}")
            return False
```

### Subtask 3.1.2: Artifact Upload Implementation
```python
# src/storage/artifact_storage.py
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import mimetypes

class ArtifactStorage:
    def __init__(self, minio_client: MinIOClient):
        self.minio_client = minio_client
        self.logger = logging.getLogger(__name__)
    
    async def upload_artifact(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """Upload an artifact to MinIO"""
        
        # Generate unique file path
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1]
        file_path = f"{user_id}/{file_id}{file_extension}" if user_id else f"public/{file_id}{file_extension}"
        
        # Determine content type
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or 'application/octet-stream'
        
        # Calculate content hash
        content_hash = self._calculate_hash(file_data)
        
        # Prepare metadata
        upload_metadata = {
            'original_filename': filename,
            'content_hash': content_hash,
            'upload_timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'is_public': str(is_public)
        }
        if metadata:
            upload_metadata.update(metadata)
        
        try:
            # Upload to MinIO
            bucket_name = 'artifacts'
            self.minio_client.client.put_object(
                bucket_name=bucket_name,
                object_name=file_path,
                data=file_data,
                length=len(file_data.read()),
                content_type=content_type,
                metadata=upload_metadata
            )
            
            return {
                'file_id': file_id,
                'file_path': file_path,
                'bucket': bucket_name,
                'content_hash': content_hash,
                'content_type': content_type,
                'file_size': len(file_data.read()),
                'metadata': upload_metadata
            }
            
        except S3Error as e:
            self.logger.error(f"Failed to upload artifact: {e}")
            raise
    
    def _calculate_hash(self, file_data: BinaryIO) -> str:
        """Calculate SHA-256 hash of file content"""
        hash_sha256 = hashlib.sha256()
        for chunk in iter(lambda: file_data.read(4096), b""):
            hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
```

### Subtask 3.1.3: Artifact Download Implementation
```python
    async def download_artifact(
        self,
        file_path: str,
        bucket: str = 'artifacts'
    ) -> Optional[BinaryIO]:
        """Download an artifact from MinIO"""
        
        try:
            response = self.minio_client.client.get_object(bucket, file_path)
            return response
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                self.logger.warning(f"Artifact not found: {file_path}")
                return None
            else:
                self.logger.error(f"Failed to download artifact: {e}")
                raise
    
    async def get_artifact_metadata(
        self,
        file_path: str,
        bucket: str = 'artifacts'
    ) -> Optional[Dict[str, Any]]:
        """Get metadata for an artifact"""
        
        try:
            stat = self.minio_client.client.stat_object(bucket, file_path)
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
```

### Subtask 3.1.4: Metadata Management
```python
# src/storage/metadata_manager.py
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

class MetadataManager:
    def __init__(self, minio_client: MinIOClient):
        self.minio_client = minio_client
        self.logger = logging.getLogger(__name__)
    
    async def add_metadata_tags(
        self,
        file_path: str,
        tags: Dict[str, Any],
        bucket: str = 'artifacts'
    ) -> bool:
        """Add metadata tags to an artifact"""
        
        try:
            # Get existing metadata
            stat = self.minio_client.client.stat_object(bucket, file_path)
            existing_metadata = stat.metadata or {}
            
            # Add new tags
            for key, value in tags.items():
                existing_metadata[f'x-amz-meta-{key}'] = str(value)
            
            # Update object with new metadata
            self.minio_client.client.copy_object(
                bucket, file_path,
                bucket, file_path,
                metadata=existing_metadata,
                metadata_directive='REPLACE'
            )
            
            return True
            
        except S3Error as e:
            self.logger.error(f"Failed to add metadata tags: {e}")
            return False
    
    async def search_artifacts_by_metadata(
        self,
        tags: Dict[str, Any],
        bucket: str = 'artifacts'
    ) -> List[str]:
        """Search artifacts by metadata tags"""
        
        matching_objects = []
        
        try:
            objects = self.minio_client.client.list_objects(bucket, recursive=True)
            
            for obj in objects:
                stat = self.minio_client.client.stat_object(bucket, obj.object_name)
                if stat.metadata:
                    # Check if all required tags match
                    matches = True
                    for key, value in tags.items():
                        meta_key = f'x-amz-meta-{key}'
                        if meta_key not in stat.metadata or stat.metadata[meta_key] != str(value):
                            matches = False
                            break
                    
                    if matches:
                        matching_objects.append(obj.object_name)
            
            return matching_objects
            
        except S3Error as e:
            self.logger.error(f"Failed to search artifacts: {e}")
            return []
```

### Subtask 3.1.5: Access Control Implementation
```python
# src/storage/access_control.py
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

class AccessControl:
    def __init__(self, minio_client: MinIOClient):
        self.minio_client = minio_client
        self.logger = logging.getLogger(__name__)
    
    async def generate_presigned_url(
        self,
        file_path: str,
        bucket: str = 'artifacts',
        expires: int = 3600,
        method: str = 'GET'
    ) -> Optional[str]:
        """Generate a presigned URL for secure access"""
        
        try:
            url = self.minio_client.client.presigned_url(
                method=method,
                bucket_name=bucket,
                object_name=file_path,
                expires=timedelta(seconds=expires)
            )
            return url
            
        except S3Error as e:
            self.logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    async def set_artifact_visibility(
        self,
        file_path: str,
        is_public: bool,
        bucket: str = 'artifacts'
    ) -> bool:
        """Set artifact visibility (public/private)"""
        
        try:
            # Get current metadata
            stat = self.minio_client.client.stat_object(bucket, file_path)
            metadata = stat.metadata or {}
            
            # Update visibility
            metadata['x-amz-meta-is-public'] = str(is_public)
            
            # Update object
            self.minio_client.client.copy_object(
                bucket, file_path,
                bucket, file_path,
                metadata=metadata,
                metadata_directive='REPLACE'
            )
            
            return True
            
        except S3Error as e:
            self.logger.error(f"Failed to set artifact visibility: {e}")
            return False
    
    async def check_access_permission(
        self,
        file_path: str,
        user_id: Optional[str],
        bucket: str = 'artifacts'
    ) -> bool:
        """Check if user has access to artifact"""
        
        try:
            stat = self.minio_client.client.stat_object(bucket, file_path)
            metadata = stat.metadata or {}
            
            # Check if artifact is public
            is_public = metadata.get('x-amz-meta-is-public', 'false').lower() == 'true'
            if is_public:
                return True
            
            # Check if user owns the artifact
            artifact_user_id = metadata.get('x-amz-meta-user-id')
            if user_id and artifact_user_id == user_id:
                return True
            
            return False
            
        except S3Error as e:
            self.logger.error(f"Failed to check access permission: {e}")
            return False
```

## Files to Create

1. `src/storage/__init__.py` - Storage package
2. `src/storage/minio_client.py` - MinIO client wrapper
3. `src/storage/artifact_storage.py` - Artifact storage operations
4. `src/storage/metadata_manager.py` - Metadata management
5. `src/storage/access_control.py` - Access control implementation
6. `src/storage/utils.py` - Storage utility functions
7. `config/minio_config.py` - MinIO configuration
8. `tests/storage/` - Storage tests directory

## Configuration

### MinIO Configuration
```python
# config/minio_config.py
from pydantic import BaseSettings

class MinIOSettings(BaseSettings):
    endpoint: str = "localhost:9000"
    access_key: str
    secret_key: str
    secure: bool = True
    region: str = "us-east-1"
    
    # Bucket configuration
    artifacts_bucket: str = "artifacts"
    temp_bucket: str = "temp"
    backup_bucket: str = "backup"
    
    # Upload configuration
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    chunk_size: int = 8 * 1024 * 1024  # 8MB
    
    class Config:
        env_prefix = "MINIO_"
```

## Testing

### Unit Tests
- [ ] Test MinIO client connection
- [ ] Test artifact upload/download
- [ ] Test metadata operations
- [ ] Test access control
- [ ] Test error handling

### Integration Tests
- [ ] Test with actual MinIO server
- [ ] Test large file uploads
- [ ] Test concurrent access
- [ ] Test bucket operations

## Documentation

- [ ] Create MinIO setup guide
- [ ] Document storage operations
- [ ] Create access control guide
- [ ] Document metadata schema

## Notes

- Use presigned URLs for secure access
- Implement proper error handling and retry logic
- Add content validation and sanitization
- Use chunked uploads for large files
- Implement proper logging for audit trails
- Consider implementing backup strategies

## Next Steps

After completing this task, proceed to:
- Task 04: Basic API Endpoints
- Task 05: User Authentication System
- Task 06: Web Scraper Implementation

## Completion Criteria

- [ ] MinIO client is properly configured
- [ ] Artifact upload/download operations work
- [ ] Metadata management is implemented
- [ ] Access control is working
- [ ] All tests are passing
- [ ] Documentation is complete
- [ ] Error handling is robust
