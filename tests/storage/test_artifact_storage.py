import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from minio.error import S3Error

from src.storage.artifact_storage import ArtifactStorage


class TestArtifactStorage:
    """Test cases for artifact storage functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.storage = ArtifactStorage(self.mock_client)

    def test_upload_artifact_success(self):
        """Test successful artifact upload."""
        # Mock file data
        file_data = io.BytesIO(b"test file content")
        filename = "test.txt"
        
        # Mock MinIO client operations
        self.mock_client.client.put_object.return_value = None
        
        # Test upload
        result = self.storage.upload_artifact(
            file_data=file_data,
            filename=filename,
            user_id="user123"
        )
        
        # Verify result structure
        assert 'file_id' in result
        assert 'object_name' in result
        assert 'bucket' in result
        assert 'content_hash' in result
        assert 'content_type' in result
        assert 'file_size' in result
        assert 'metadata' in result
        
        # Verify object name format
        assert result['object_name'].startswith('user123/')
        assert result['object_name'].endswith('.txt')
        
        # Verify put_object was called
        self.mock_client.client.put_object.assert_called_once()
        call_args = self.mock_client.client.put_object.call_args
        assert call_args[1]['bucket_name'] == 'artifacts'
        assert call_args[1]['content_type'] == 'text/plain'

    def test_upload_artifact_public(self):
        """Test artifact upload without user_id (public)."""
        # Mock file data
        file_data = io.BytesIO(b"test file content")
        filename = "test.txt"
        
        # Mock MinIO client operations
        self.mock_client.client.put_object.return_value = None
        
        # Test upload
        result = self.storage.upload_artifact(
            file_data=file_data,
            filename=filename
        )
        
        # Verify object name format for public files
        assert result['object_name'].startswith('public/')
        assert result['object_name'].endswith('.txt')

    def test_upload_artifact_with_custom_content_type(self):
        """Test artifact upload with custom content type."""
        # Mock file data
        file_data = io.BytesIO(b"test file content")
        filename = "test.txt"
        content_type = "application/custom"
        
        # Mock MinIO client operations
        self.mock_client.client.put_object.return_value = None
        
        # Test upload
        result = self.storage.upload_artifact(
            file_data=file_data,
            filename=filename,
            content_type=content_type
        )
        
        # Verify custom content type was used
        assert result['content_type'] == content_type

    def test_upload_artifact_with_metadata(self):
        """Test artifact upload with custom metadata."""
        # Mock file data
        file_data = io.BytesIO(b"test file content")
        filename = "test.txt"
        metadata = {"custom_key": "custom_value"}
        
        # Mock MinIO client operations
        self.mock_client.client.put_object.return_value = None
        
        # Test upload
        result = self.storage.upload_artifact(
            file_data=file_data,
            filename=filename,
            metadata=metadata
        )
        
        # Verify metadata was included
        assert 'custom_key' in result['metadata']
        assert result['metadata']['custom_key'] == 'custom_value'

    def test_upload_artifact_error(self):
        """Test artifact upload with error."""
        # Mock file data
        file_data = io.BytesIO(b"test file content")
        filename = "test.txt"
        
        # Mock MinIO client to raise error
        self.mock_client.client.put_object.side_effect = S3Error("Upload failed")
        
        # Test that error is raised
        with pytest.raises(S3Error, match="Upload failed"):
            self.storage.upload_artifact(
                file_data=file_data,
                filename=filename
            )

    def test_download_artifact_success(self):
        """Test successful artifact download."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client response
        mock_response = io.BytesIO(b"downloaded content")
        self.mock_client.client.get_object.return_value = mock_response
        
        # Test download
        result = self.storage.download_artifact(object_name)
        
        # Verify result
        assert result == mock_response
        self.mock_client.client.get_object.assert_called_once_with('artifacts', object_name)

    def test_download_artifact_not_found(self):
        """Test artifact download when file not found."""
        object_name = "user123/nonexistent.txt"
        
        # Mock MinIO client to raise NoSuchKey error
        error = S3Error("NoSuchKey")
        error.code = 'NoSuchKey'
        self.mock_client.client.get_object.side_effect = error
        
        # Test download
        result = self.storage.download_artifact(object_name)
        
        # Verify result is None
        assert result is None

    def test_download_artifact_error(self):
        """Test artifact download with error."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client to raise error
        self.mock_client.client.get_object.side_effect = S3Error("Download failed")
        
        # Test that error is raised
        with pytest.raises(S3Error, match="Download failed"):
            self.storage.download_artifact(object_name)

    def test_get_artifact_metadata_success(self):
        """Test successful metadata retrieval."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client response
        mock_stat = Mock()
        mock_stat.size = 1024
        mock_stat.etag = "test-etag"
        mock_stat.content_type = "text/plain"
        mock_stat.last_modified = "2023-01-01T00:00:00Z"
        mock_stat.metadata = {"key": "value"}
        
        self.mock_client.client.stat_object.return_value = mock_stat
        
        # Test metadata retrieval
        result = self.storage.get_artifact_metadata(object_name)
        
        # Verify result
        assert result['size'] == 1024
        assert result['etag'] == "test-etag"
        assert result['content_type'] == "text/plain"
        assert result['last_modified'] == "2023-01-01T00:00:00Z"
        assert result['metadata'] == {"key": "value"}

    def test_get_artifact_metadata_not_found(self):
        """Test metadata retrieval when file not found."""
        object_name = "user123/nonexistent.txt"
        
        # Mock MinIO client to raise NoSuchKey error
        error = S3Error("NoSuchKey")
        error.code = 'NoSuchKey'
        self.mock_client.client.stat_object.side_effect = error
        
        # Test metadata retrieval
        result = self.storage.get_artifact_metadata(object_name)
        
        # Verify result is None
        assert result is None

    def test_generate_presigned_url_success(self):
        """Test successful presigned URL generation."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client response
        expected_url = "https://minio.example.com/presigned-url"
        self.mock_client.client.presigned_get_object.return_value = expected_url
        
        # Test URL generation
        result = self.storage.generate_presigned_url(object_name)
        
        # Verify result
        assert result == expected_url
        self.mock_client.client.presigned_get_object.assert_called_once()

    def test_generate_presigned_url_error(self):
        """Test presigned URL generation with error."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client to raise error
        self.mock_client.client.presigned_get_object.side_effect = S3Error("URL generation failed")
        
        # Test URL generation
        result = self.storage.generate_presigned_url(object_name)
        
        # Verify result is None
        assert result is None

    def test_calculate_hash(self):
        """Test hash calculation."""
        # Create test data
        test_content = b"test content for hashing"
        file_data = io.BytesIO(test_content)
        
        # Calculate hash
        result = self.storage._calculate_hash(file_data)
        
        # Verify hash is a valid hex string
        assert len(result) == 64  # SHA-256 hash length
        assert all(c in '0123456789abcdef' for c in result)
