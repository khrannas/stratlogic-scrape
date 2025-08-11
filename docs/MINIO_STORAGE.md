# MinIO Storage System Documentation

## Overview

The StratLogic Scraping System uses MinIO as its primary object storage solution for storing scraped artifacts, metadata, and system files. This document provides comprehensive information about the storage architecture, configuration, and usage.

## Architecture

### Storage Components

1. **MinIO Client** (`src/storage/minio_client.py`)
   - Low-level MinIO operations
   - File upload/download/delete
   - Object listing and metadata retrieval
   - Presigned URL generation
   - Health checks

2. **Artifact Storage** (`src/storage/artifact_storage.py`)
   - High-level artifact management
   - Access control and permissions
   - User-based file organization
   - Backup and restore operations
   - Content validation

3. **Metadata Manager** (`src/storage/metadata_manager.py`)
   - Metadata storage and retrieval
   - Tagging system
   - Search functionality
   - Metadata integrity verification
   - Backup and recovery

### Bucket Structure

```
minio/
├── artifacts/          # Main artifact storage
│   ├── users/         # User-specific artifacts
│   │   └── {user_id}/
│   └── public/        # Public artifacts
├── metadata/          # Metadata storage
│   └── artifacts/
│       └── {artifact_id}/
├── temp/              # Temporary files
└── backup/            # Backup storage
    ├── artifacts/
    └── metadata/
```

## Configuration

### Environment Variables

```bash
# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_USE_SSL=false
MINIO_BUCKET_NAME=artifacts

# Storage Limits
MINIO_MAX_FILE_SIZE=104857600  # 100MB
MINIO_CHUNK_SIZE=8388608       # 8MB
```

### Docker Compose Configuration

```yaml
services:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  minio_data:
```

## Usage Examples

### Basic Artifact Operations

```python
from src.storage import artifact_storage, metadata_manager
import io

# Upload an artifact
file_data = io.BytesIO(b"Hello, World!")
result = await artifact_storage.upload_artifact(
    file_data=file_data,
    filename="hello.txt",
    content_type="text/plain",
    user_id="user123",
    is_public=False,
    metadata={"description": "A test file"}
)

print(f"Uploaded: {result['file_path']}")
print(f"Content hash: {result['content_hash']}")

# Download an artifact
downloaded_data = await artifact_storage.download_artifact(
    file_path=result['file_path'],
    user_id="user123"
)

if downloaded_data:
    content = downloaded_data.read()
    print(f"Downloaded: {content}")

# Get artifact metadata
metadata = await artifact_storage.get_artifact_metadata(
    file_path=result['file_path'],
    user_id="user123"
)

print(f"File size: {metadata['size']} bytes")
print(f"Content type: {metadata['content_type']}")
```

### Metadata Management

```python
# Store metadata
metadata = {
    "title": "Research Paper",
    "authors": ["John Doe", "Jane Smith"],
    "keywords": ["AI", "Machine Learning"],
    "content_type": "application/pdf",
    "language": "en"
}

success = await metadata_manager.store_metadata(
    artifact_id="artifact123",
    metadata=metadata,
    user_id="user123"
)

# Add tags
await metadata_manager.add_tags(
    artifact_id="artifact123",
    tags=["research", "academic", "AI"],
    user_id="user123"
)

# Search by tags
results = await metadata_manager.search_by_tags(
    tags=["AI", "research"],
    user_id="user123"
)

for result in results:
    print(f"Found: {result['data']['title']}")

# Search by content type
pdf_results = await metadata_manager.search_by_content_type(
    content_type="application/pdf",
    user_id="user123"
)
```

### Access Control

```python
# Public artifact (accessible by anyone)
public_result = await artifact_storage.upload_artifact(
    file_data=io.BytesIO(b"Public content"),
    filename="public.txt",
    is_public=True
)

# Private artifact (only owner can access)
private_result = await artifact_storage.upload_artifact(
    file_data=io.BytesIO(b"Private content"),
    filename="private.txt",
    user_id="user123",
    is_public=False
)

# Access control is enforced automatically
# This will return None (access denied)
unauthorized_data = await artifact_storage.download_artifact(
    file_path=private_result['file_path'],
    user_id="other_user"
)

# This will work (owner access)
authorized_data = await artifact_storage.download_artifact(
    file_path=private_result['file_path'],
    user_id="user123"
)
```

### Presigned URLs

```python
# Generate a presigned URL for secure access
url = await artifact_storage.get_presigned_url(
    file_path=result['file_path'],
    user_id="user123",
    expires=3600,  # 1 hour
    method="GET"
)

print(f"Secure URL: {url}")

# Generate upload URL
upload_url = await artifact_storage.get_presigned_url(
    file_path="users/user123/upload.txt",
    user_id="user123",
    expires=1800,  # 30 minutes
    method="PUT"
)
```

### Backup and Recovery

```python
# Create backup
backup_success = await artifact_storage.backup_artifact(
    file_path=result['file_path']
)

# Backup metadata
metadata_backup = await metadata_manager.backup_metadata(
    artifact_id="artifact123"
)

# Restore from backup
restore_success = await artifact_storage.restore_artifact(
    backup_path="backups/backup_20231201_120000_artifact123.txt",
    restore_path="restored/artifact123.txt"
)

# Restore metadata
metadata_restore = await metadata_manager.restore_metadata(
    backup_key="backups/metadata_backup_20231201_120000_artifact123.json"
)
```

## File Organization

### User Artifacts

User artifacts are organized by user ID:

```
artifacts/users/{user_id}/{file_id}{extension}
```

Example:
```
artifacts/users/user123/abc123-def456-ghi789.txt
```

### Public Artifacts

Public artifacts are stored in a shared location:

```
artifacts/public/{file_id}{extension}
```

Example:
```
artifacts/public/xyz789-abc123-def456.pdf
```

### Metadata Storage

Metadata is stored separately for better performance:

```
metadata/artifacts/{artifact_id}/metadata.json
```

Example:
```
metadata/artifacts/abc123-def456-ghi789/metadata.json
```

## Security Features

### Access Control

- **User-based access**: Artifacts are tied to specific users
- **Public/Private visibility**: Control artifact visibility
- **Owner-only operations**: Only artifact owners can delete or modify
- **Presigned URLs**: Time-limited secure access

### Data Integrity

- **Content hashing**: SHA-256 hashes for content verification
- **Metadata hashing**: Integrity checks for metadata
- **Version control**: Metadata versioning for tracking changes

### Encryption

- **TLS/SSL**: Encrypted communication with MinIO
- **At-rest encryption**: MinIO supports server-side encryption
- **Client-side encryption**: Optional client-side encryption

## Performance Optimization

### Chunked Uploads

Large files are uploaded in chunks for better performance:

```python
# Automatic chunked upload for files > 8MB
result = await artifact_storage.upload_artifact(
    file_data=large_file_data,
    filename="large_file.zip"
)
```

### Caching

- **Metadata caching**: Frequently accessed metadata is cached
- **Object caching**: MinIO supports object-level caching
- **CDN integration**: Can be integrated with CDN for global distribution

### Compression

- **Automatic compression**: Text files are automatically compressed
- **Image optimization**: Images can be optimized before storage
- **Archive handling**: Automatic extraction and compression of archives

## Monitoring and Health Checks

### Health Check Endpoints

```python
# Check MinIO client health
minio_health = minio_client.health_check()

# Check artifact storage health
storage_health = artifact_storage.health_check()

# Check metadata system health
metadata_health = metadata_manager.health_check()
```

### Metrics

- **Storage usage**: Track bucket and object counts
- **Performance metrics**: Upload/download speeds
- **Error rates**: Failed operations and retry counts
- **Access patterns**: User activity and file access

### Logging

Comprehensive logging for all operations:

```python
# Log levels
logger.debug("Detailed operation information")
logger.info("Normal operation events")
logger.warning("Potential issues")
logger.error("Operation failures")
logger.critical("System failures")
```

## Backup and Disaster Recovery

### Backup Strategy

1. **Automated backups**: Daily automated backups of all data
2. **Incremental backups**: Only changed data is backed up
3. **Cross-region replication**: Backup copies in different regions
4. **Version retention**: Multiple versions of important files

### Recovery Procedures

1. **Point-in-time recovery**: Restore to specific timestamps
2. **Selective recovery**: Restore specific files or users
3. **Full system recovery**: Complete system restoration
4. **Metadata recovery**: Separate metadata recovery procedures

### Testing

- **Regular backup testing**: Verify backup integrity
- **Recovery drills**: Practice recovery procedures
- **Performance testing**: Ensure recovery meets RTO/RPO requirements

## Troubleshooting

### Common Issues

#### Connection Problems

```bash
# Check MinIO service status
docker-compose ps minio

# Check MinIO logs
docker-compose logs minio

# Test connectivity
curl -I http://localhost:9000/minio/health/live
```

#### Permission Issues

```python
# Check bucket permissions
minio_client.client.bucket_exists("artifacts")

# Check object permissions
minio_client.object_exists("path/to/object")

# Verify access keys
minio_client.health_check()
```

#### Storage Issues

```python
# Check available space
storage_health = artifact_storage.health_check()

# List buckets
buckets = minio_client.client.list_buckets()

# Check object count
objects = minio_client.list_objects(prefix="users/")
```

### Error Handling

```python
try:
    result = await artifact_storage.upload_artifact(...)
except S3Error as e:
    if e.code == "NoSuchBucket":
        print("Bucket does not exist")
    elif e.code == "AccessDenied":
        print("Access denied")
    else:
        print(f"Storage error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

### File Management

1. **Use descriptive filenames**: Include relevant information in filenames
2. **Organize by user**: Keep user files separate
3. **Set appropriate content types**: Help with file handling
4. **Use tags for organization**: Make files easily searchable

### Performance

1. **Use chunked uploads**: For files larger than 8MB
2. **Compress when possible**: Reduce storage and transfer costs
3. **Cache frequently accessed data**: Improve response times
4. **Monitor usage patterns**: Optimize based on actual usage

### Security

1. **Use presigned URLs**: For secure temporary access
2. **Implement proper access control**: Restrict access appropriately
3. **Regular security audits**: Check for vulnerabilities
4. **Encrypt sensitive data**: Use encryption for confidential files

### Monitoring

1. **Set up alerts**: For storage issues and performance problems
2. **Monitor usage**: Track storage growth and access patterns
3. **Regular health checks**: Ensure system is functioning properly
4. **Log analysis**: Review logs for issues and optimization opportunities

## API Reference

### MinIOClient

```python
class MinIOClient:
    def upload_file(file_path, object_name=None, content_type=None, metadata=None) -> str
    def upload_data(data, object_name, content_type=None, metadata=None) -> str
    def download_file(object_name, file_path) -> bool
    def download_data(object_name) -> Optional[bytes]
    def delete_object(object_name) -> bool
    def list_objects(prefix=None, recursive=True) -> List[Dict]
    def get_object_info(object_name) -> Optional[Dict]
    def object_exists(object_name) -> bool
    def get_presigned_url(object_name, method="GET", expires=3600) -> Optional[str]
    def health_check() -> bool
```

### ArtifactStorage

```python
class ArtifactStorage:
    async def upload_artifact(file_data, filename, content_type=None, metadata=None, user_id=None, is_public=False, job_id=None) -> Dict
    async def download_artifact(file_path, user_id=None) -> Optional[BinaryIO]
    async def delete_artifact(file_path, user_id=None) -> bool
    async def get_artifact_metadata(file_path, user_id=None) -> Optional[Dict]
    async def list_user_artifacts(user_id, prefix=None, limit=100) -> List[Dict]
    async def list_public_artifacts(prefix=None, limit=100) -> List[Dict]
    async def get_presigned_url(file_path, user_id=None, expires=3600, method="GET") -> Optional[str]
    async def backup_artifact(file_path, backup_name=None) -> bool
    async def restore_artifact(backup_path, restore_path=None) -> bool
    def health_check() -> Dict
```

### MetadataManager

```python
class MetadataManager:
    async def store_metadata(artifact_id, metadata, user_id=None) -> bool
    async def get_metadata(artifact_id, user_id=None) -> Optional[Dict]
    async def update_metadata(artifact_id, updates, user_id=None) -> bool
    async def add_tags(artifact_id, tags, user_id=None) -> bool
    async def remove_tags(artifact_id, tags, user_id=None) -> bool
    async def search_metadata(query, user_id=None, limit=100) -> List[Dict]
    async def search_by_tags(tags, user_id=None, limit=100) -> List[Dict]
    async def search_by_content_type(content_type, user_id=None, limit=100) -> List[Dict]
    async def backup_metadata(artifact_id, backup_name=None) -> bool
    async def restore_metadata(backup_key, artifact_id=None) -> bool
    def health_check() -> Dict
```

## Conclusion

The MinIO storage system provides a robust, scalable, and secure solution for storing artifacts and metadata in the StratLogic Scraping System. With comprehensive access control, data integrity features, and backup capabilities, it ensures reliable storage operations for all scraping activities.

For additional support or questions, refer to the MinIO documentation or contact the development team.
