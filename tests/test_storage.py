"""
Tests for storage components.

This module tests MinIO client, artifact storage, and metadata manager.
"""

import pytest
import io
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, mock_open

from src.storage.minio_client import MinIOClient
from src.storage.artifact_storage import ArtifactStorage
from src.storage.metadata_manager import MetadataManager


class TestMinIOClient:
    """Test MinIO client operations."""
    
    @pytest.fixture
    def mock_minio_client(self):
        """Create a mock MinIO client."""
        with patch('src.storage.minio_client.Minio') as mock_minio:
            client = MinIOClient()
            client.client = mock_minio.return_value
            yield client
    
    @pytest.mark.unit
    def test_minio_client_initialization(self, mock_minio_client):
        """Test MinIO client initialization."""
        assert mock_minio_client.client is not None
        assert mock_minio_client.bucket_name is not None
    
    @pytest.mark.unit
    def test_upload_file_success(self, mock_minio_client):
        """Test successful file upload."""
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            # Mock file operations
            with patch('builtins.open', mock_open(read_data=b'test content')):
                result = mock_minio_client.upload_file(
                    file_path="/tmp/test.txt",
                    object_name="test/test.txt",
                    content_type="text/plain"
                )
                
                assert result == "test/test.txt"
                mock_minio_client.client.fput_object.assert_called_once()
    
    @pytest.mark.unit
    def test_upload_file_not_found(self, mock_minio_client):
        """Test file upload with non-existent file."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                mock_minio_client.upload_file("/tmp/nonexistent.txt")
    
    @pytest.mark.unit
    def test_upload_data_success(self, mock_minio_client):
        """Test successful data upload."""
        test_data = b"test content"
        result = mock_minio_client.upload_data(
            data=test_data,
            object_name="test/data.txt",
            content_type="text/plain"
        )
        
        assert result == "test/data.txt"
        mock_minio_client.client.put_object.assert_called_once()
    
    @pytest.mark.unit
    def test_download_file_success(self, mock_minio_client):
        """Test successful file download."""
        # Mock successful download
        mock_minio_client.client.fget_object.return_value = None
        
        result = mock_minio_client.download_file(
            object_name="test/test.txt",
            file_path="/tmp/downloaded.txt"
        )
        
        assert result is True
        mock_minio_client.client.fget_object.assert_called_once()
    
    @pytest.mark.unit
    def test_download_data_success(self, mock_minio_client):
        """Test successful data download."""
        # Mock response object
        mock_response = MagicMock()
        mock_response.read.return_value = b"test content"
        mock_minio_client.client.get_object.return_value = mock_response
        
        result = mock_minio_client.download_data("test/data.txt")
        
        assert result == b"test content"
        mock_minio_client.client.get_object.assert_called_once()
    
    @pytest.mark.unit
    def test_delete_object_success(self, mock_minio_client):
        """Test successful object deletion."""
        result = mock_minio_client.delete_object("test/test.txt")
        
        assert result is True
        mock_minio_client.client.remove_object.assert_called_once()
    
    @pytest.mark.unit
    def test_list_objects_success(self, mock_minio_client):
        """Test successful object listing."""
        # Mock objects
        mock_objects = [
            MagicMock(name="test1.txt", size=100, last_modified=datetime.now()),
            MagicMock(name="test2.txt", size=200, last_modified=datetime.now())
        ]
        mock_minio_client.client.list_objects.return_value = mock_objects
        
        result = mock_minio_client.list_objects(prefix="test/")
        
        assert len(result) == 2
        assert result[0]['name'] == "test1.txt"
        assert result[1]['name'] == "test2.txt"
    
    @pytest.mark.unit
    def test_get_object_info_success(self, mock_minio_client):
        """Test successful object info retrieval."""
        # Mock object stat
        mock_stat = MagicMock()
        mock_stat.size = 100
        mock_stat.etag = "test-etag"
        mock_stat.content_type = "text/plain"
        mock_stat.last_modified = datetime.now()
        mock_stat.metadata = {"key": "value"}
        
        mock_minio_client.client.stat_object.return_value = mock_stat
        
        result = mock_minio_client.get_object_info("test/test.txt")
        
        assert result is not None
        assert result['size'] == 100
        assert result['etag'] == "test-etag"
        assert result['content_type'] == "text/plain"
    
    @pytest.mark.unit
    def test_object_exists_true(self, mock_minio_client):
        """Test object existence check (exists)."""
        # Mock successful stat
        mock_minio_client.client.stat_object.return_value = MagicMock()
        
        result = mock_minio_client.object_exists("test/test.txt")
        
        assert result is True
    
    @pytest.mark.unit
    def test_object_exists_false(self, mock_minio_client):
        """Test object existence check (not exists)."""
        # Mock NoSuchKey error
        from minio.error import S3Error
        mock_minio_client.client.stat_object.side_effect = S3Error(
            code="NoSuchKey",
            message="Object does not exist",
            resource="test/test.txt",
            request_id="test"
        )
        
        result = mock_minio_client.object_exists("test/test.txt")
        
        assert result is False
    
    @pytest.mark.unit
    def test_get_presigned_url_success(self, mock_minio_client):
        """Test successful presigned URL generation."""
        mock_minio_client.client.presigned_get_object.return_value = "https://test-url.com"
        
        result = mock_minio_client.get_presigned_url(
            object_name="test/test.txt",
            method="GET",
            expires=3600
        )
        
        assert result == "https://test-url.com"
        mock_minio_client.client.presigned_get_object.assert_called_once()
    
    @pytest.mark.unit
    def test_health_check_success(self, mock_minio_client):
        """Test successful health check."""
        mock_minio_client.client.list_buckets.return_value = []
        
        result = mock_minio_client.health_check()
        
        assert result is True
    
    @pytest.mark.unit
    def test_health_check_failure(self, mock_minio_client):
        """Test failed health check."""
        mock_minio_client.client.list_buckets.side_effect = Exception("Connection failed")
        
        result = mock_minio_client.health_check()
        
        assert result is False


class TestArtifactStorage:
    """Test artifact storage operations."""
    
    @pytest.fixture
    def mock_artifact_storage(self):
        """Create a mock artifact storage."""
        with patch('src.storage.artifact_storage.MinIOClient') as mock_minio:
            storage = ArtifactStorage()
            storage.minio_client = mock_minio.return_value
            yield storage
    
    @pytest.mark.unit
    async def test_upload_artifact_success(self, mock_artifact_storage):
        """Test successful artifact upload."""
        # Mock file data
        file_data = io.BytesIO(b"test content")
        
        # Mock MinIO operations
        mock_artifact_storage.minio_client.upload_data.return_value = "users/test-user/test-file.txt"
        mock_artifact_storage.minio_client.object_exists.return_value = True
        
        result = await mock_artifact_storage.upload_artifact(
            file_data=file_data,
            filename="test.txt",
            content_type="text/plain",
            user_id="test-user",
            is_public=False
        )
        
        assert result is not None
        assert result['file_path'] == "users/test-user/test-file.txt"
        assert result['user_id'] == "test-user"
        assert result['is_public'] is False
        assert 'content_hash' in result
    
    @pytest.mark.unit
    async def test_upload_public_artifact(self, mock_artifact_storage):
        """Test public artifact upload."""
        file_data = io.BytesIO(b"test content")
        
        mock_artifact_storage.minio_client.upload_data.return_value = "public/test-file.txt"
        
        result = await mock_artifact_storage.upload_artifact(
            file_data=file_data,
            filename="test.txt",
            is_public=True
        )
        
        assert result is not None
        assert result['file_path'] == "public/test-file.txt"
        assert result['is_public'] is True
    
    @pytest.mark.unit
    async def test_download_artifact_success(self, mock_artifact_storage):
        """Test successful artifact download."""
        # Mock object exists and access control
        mock_artifact_storage.minio_client.object_exists.return_value = True
        mock_artifact_storage.minio_client.get_object_info.return_value = {
            'metadata': {
                'user_id': 'test-user',
                'is_public': 'false'
            }
        }
        mock_artifact_storage.minio_client.download_data.return_value = b"test content"
        
        result = await mock_artifact_storage.download_artifact(
            file_path="users/test-user/test-file.txt",
            user_id="test-user"
        )
        
        assert result is not None
        assert result.read() == b"test content"
    
    @pytest.mark.unit
    async def test_download_artifact_access_denied(self, mock_artifact_storage):
        """Test artifact download with access denied."""
        mock_artifact_storage.minio_client.object_exists.return_value = True
        mock_artifact_storage.minio_client.get_object_info.return_value = {
            'metadata': {
                'user_id': 'owner-user',
                'is_public': 'false'
            }
        }
        
        result = await mock_artifact_storage.download_artifact(
            file_path="users/owner-user/test-file.txt",
            user_id="other-user"
        )
        
        assert result is None
    
    @pytest.mark.unit
    async def test_download_public_artifact(self, mock_artifact_storage):
        """Test public artifact download."""
        mock_artifact_storage.minio_client.object_exists.return_value = True
        mock_artifact_storage.minio_client.get_object_info.return_value = {
            'metadata': {
                'user_id': 'owner-user',
                'is_public': 'true'
            }
        }
        mock_artifact_storage.minio_client.download_data.return_value = b"test content"
        
        result = await mock_artifact_storage.download_artifact(
            file_path="public/test-file.txt",
            user_id="any-user"
        )
        
        assert result is not None
        assert result.read() == b"test content"
    
    @pytest.mark.unit
    async def test_delete_artifact_success(self, mock_artifact_storage):
        """Test successful artifact deletion."""
        mock_artifact_storage.minio_client.object_exists.return_value = True
        mock_artifact_storage.minio_client.get_object_info.return_value = {
            'metadata': {
                'user_id': 'test-user'
            }
        }
        mock_artifact_storage.minio_client.delete_object.return_value = True
        
        result = await mock_artifact_storage.delete_artifact(
            file_path="users/test-user/test-file.txt",
            user_id="test-user"
        )
        
        assert result is True
    
    @pytest.mark.unit
    async def test_delete_artifact_access_denied(self, mock_artifact_storage):
        """Test artifact deletion with access denied."""
        mock_artifact_storage.minio_client.object_exists.return_value = True
        mock_artifact_storage.minio_client.get_object_info.return_value = {
            'metadata': {
                'user_id': 'owner-user'
            }
        }
        
        result = await mock_artifact_storage.delete_artifact(
            file_path="users/owner-user/test-file.txt",
            user_id="other-user"
        )
        
        assert result is False
    
    @pytest.mark.unit
    async def test_get_artifact_metadata_success(self, mock_artifact_storage):
        """Test successful metadata retrieval."""
        mock_artifact_storage.minio_client.object_exists.return_value = True
        mock_artifact_storage.minio_client.get_object_info.return_value = {
            'size': 100,
            'etag': 'test-etag',
            'content_type': 'text/plain',
            'last_modified': datetime.now(),
            'metadata': {
                'user_id': 'test-user',
                'is_public': 'false'
            }
        }
        
        result = await mock_artifact_storage.get_artifact_metadata(
            file_path="users/test-user/test-file.txt",
            user_id="test-user"
        )
        
        assert result is not None
        assert result['size'] == 100
        assert result['etag'] == 'test-etag'
        assert result['content_type'] == 'text/plain'
    
    @pytest.mark.unit
    async def test_list_user_artifacts(self, mock_artifact_storage):
        """Test listing user artifacts."""
        mock_artifact_storage.minio_client.list_objects.return_value = [
            {'name': 'users/test-user/file1.txt'},
            {'name': 'users/test-user/file2.txt'}
        ]
        
        # Mock get_artifact_metadata for each file
        with patch.object(mock_artifact_storage, 'get_artifact_metadata') as mock_get_meta:
            mock_get_meta.return_value = {'file_path': 'test', 'metadata': {}}
            
            result = await mock_artifact_storage.list_user_artifacts(
                user_id="test-user",
                limit=10
            )
            
            assert len(result) == 2
    
    @pytest.mark.unit
    async def test_get_presigned_url_success(self, mock_artifact_storage):
        """Test successful presigned URL generation."""
        mock_artifact_storage.minio_client.object_exists.return_value = True
        mock_artifact_storage.minio_client.get_object_info.return_value = {
            'metadata': {
                'user_id': 'test-user',
                'is_public': 'false'
            }
        }
        mock_artifact_storage.minio_client.get_presigned_url.return_value = "https://test-url.com"
        
        result = await mock_artifact_storage.get_presigned_url(
            file_path="users/test-user/test-file.txt",
            user_id="test-user"
        )
        
        assert result == "https://test-url.com"
    
    @pytest.mark.unit
    async def test_backup_artifact_success(self, mock_artifact_storage):
        """Test successful artifact backup."""
        mock_artifact_storage.minio_client.object_exists.return_value = True
        
        result = await mock_artifact_storage.backup_artifact(
            file_path="users/test-user/test-file.txt"
        )
        
        assert result is True
        mock_artifact_storage.minio_client.client.copy_object.assert_called_once()
    
    @pytest.mark.unit
    def test_health_check_success(self, mock_artifact_storage):
        """Test successful health check."""
        mock_artifact_storage.minio_client.health_check.return_value = True
        mock_artifact_storage.minio_client.client.bucket_exists.return_value = True
        
        result = mock_artifact_storage.health_check()
        
        assert result['status'] == 'healthy'
        assert result['minio_connection'] is True


class TestMetadataManager:
    """Test metadata manager operations."""
    
    @pytest.fixture
    def mock_metadata_manager(self):
        """Create a mock metadata manager."""
        with patch('src.storage.metadata_manager.MinIOClient') as mock_minio:
            manager = MetadataManager()
            manager.minio_client = mock_minio.return_value
            yield manager
    
    @pytest.mark.unit
    async def test_store_metadata_success(self, mock_metadata_manager):
        """Test successful metadata storage."""
        test_metadata = {
            'title': 'Test Document',
            'content_type': 'text/plain',
            'tags': ['test', 'document']
        }
        
        mock_metadata_manager.minio_client.upload_data.return_value = "artifacts/test-id/metadata.json"
        
        result = await mock_metadata_manager.store_metadata(
            artifact_id="test-id",
            metadata=test_metadata,
            user_id="test-user"
        )
        
        assert result is True
        mock_metadata_manager.minio_client.upload_data.assert_called_once()
    
    @pytest.mark.unit
    async def test_get_metadata_success(self, mock_metadata_manager):
        """Test successful metadata retrieval."""
        # Mock metadata JSON
        metadata_record = {
            'artifact_id': 'test-id',
            'user_id': 'test-user',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'version': '1.0',
            'data': {'title': 'Test Document'},
            'hash': 'test-hash'
        }
        
        mock_metadata_manager.minio_client.object_exists.return_value = True
        mock_metadata_manager.minio_client.get_object_info.return_value = {
            'metadata': {
                'user_id': 'test-user'
            }
        }
        mock_metadata_manager.minio_client.download_data.return_value = json.dumps(metadata_record).encode('utf-8')
        
        # Mock hash calculation
        with patch.object(mock_metadata_manager, '_calculate_metadata_hash', return_value='test-hash'):
            result = await mock_metadata_manager.get_metadata(
                artifact_id="test-id",
                user_id="test-user"
            )
            
            assert result is not None
            assert result['artifact_id'] == 'test-id'
            assert result['user_id'] == 'test-user'
            assert 'data' in result
    
    @pytest.mark.unit
    async def test_get_metadata_access_denied(self, mock_metadata_manager):
        """Test metadata retrieval with access denied."""
        mock_metadata_manager.minio_client.object_exists.return_value = True
        mock_metadata_manager.minio_client.get_object_info.return_value = {
            'metadata': {
                'user_id': 'owner-user'
            }
        }
        
        result = await mock_metadata_manager.get_metadata(
            artifact_id="test-id",
            user_id="other-user"
        )
        
        assert result is None
    
    @pytest.mark.unit
    async def test_update_metadata_success(self, mock_metadata_manager):
        """Test successful metadata update."""
        # Mock existing metadata
        existing_metadata = {
            'artifact_id': 'test-id',
            'user_id': 'test-user',
            'data': {'title': 'Old Title'},
            'hash': 'old-hash'
        }
        
        with patch.object(mock_metadata_manager, 'get_metadata', return_value=existing_metadata):
            with patch.object(mock_metadata_manager, '_calculate_metadata_hash', return_value='new-hash'):
                result = await mock_metadata_manager.update_metadata(
                    artifact_id="test-id",
                    updates={'title': 'New Title'},
                    user_id="test-user"
                )
                
                assert result is True
    
    @pytest.mark.unit
    async def test_add_tags_success(self, mock_metadata_manager):
        """Test successful tag addition."""
        existing_metadata = {
            'artifact_id': 'test-id',
            'user_id': 'test-user',
            'data': {'tags': ['existing']},
            'hash': 'old-hash'
        }
        
        with patch.object(mock_metadata_manager, 'get_metadata', return_value=existing_metadata):
            with patch.object(mock_metadata_manager, 'update_metadata', return_value=True):
                result = await mock_metadata_manager.add_tags(
                    artifact_id="test-id",
                    tags=['new', 'tags'],
                    user_id="test-user"
                )
                
                assert result is True
    
    @pytest.mark.unit
    async def test_remove_tags_success(self, mock_metadata_manager):
        """Test successful tag removal."""
        existing_metadata = {
            'artifact_id': 'test-id',
            'user_id': 'test-user',
            'data': {'tags': ['tag1', 'tag2', 'tag3']},
            'hash': 'old-hash'
        }
        
        with patch.object(mock_metadata_manager, 'get_metadata', return_value=existing_metadata):
            with patch.object(mock_metadata_manager, 'update_metadata', return_value=True):
                result = await mock_metadata_manager.remove_tags(
                    artifact_id="test-id",
                    tags=['tag2'],
                    user_id="test-user"
                )
                
                assert result is True
    
    @pytest.mark.unit
    async def test_search_metadata_success(self, mock_metadata_manager):
        """Test successful metadata search."""
        # Mock metadata objects
        mock_metadata_manager.minio_client.list_objects.return_value = [
            {'name': 'artifacts/test-id1/metadata.json'},
            {'name': 'artifacts/test-id2/metadata.json'}
        ]
        
        # Mock metadata for each artifact
        test_metadata = {
            'artifact_id': 'test-id',
            'user_id': 'test-user',
            'data': {'title': 'Test Document', 'tags': ['test']}
        }
        
        with patch.object(mock_metadata_manager, 'get_metadata', return_value=test_metadata):
            result = await mock_metadata_manager.search_metadata(
                query={'title': 'Test Document'},
                user_id="test-user"
            )
            
            assert len(result) == 2
    
    @pytest.mark.unit
    async def test_search_by_tags_success(self, mock_metadata_manager):
        """Test successful tag-based search."""
        with patch.object(mock_metadata_manager, 'search_metadata', return_value=[]) as mock_search:
            await mock_metadata_manager.search_by_tags(
                tags=['test', 'document'],
                user_id="test-user"
            )
            
            mock_search.assert_called_once_with(
                query={'tags': ['test', 'document']},
                user_id="test-user",
                limit=100
            )
    
    @pytest.mark.unit
    async def test_backup_metadata_success(self, mock_metadata_manager):
        """Test successful metadata backup."""
        mock_metadata_manager.minio_client.object_exists.return_value = True
        
        result = await mock_metadata_manager.backup_metadata(
            artifact_id="test-id"
        )
        
        assert result is True
        mock_metadata_manager.minio_client.client.copy_object.assert_called_once()
    
    @pytest.mark.unit
    def test_calculate_metadata_hash(self, mock_metadata_manager):
        """Test metadata hash calculation."""
        test_record = {
            'artifact_id': 'test-id',
            'data': {'title': 'Test'},
            'hash': 'old-hash'  # This should be ignored
        }
        
        result = mock_metadata_manager._calculate_metadata_hash(test_record)
        
        assert result is not None
        assert len(result) == 64  # SHA-256 hash length
        assert result != 'old-hash'
    
    @pytest.mark.unit
    def test_matches_query_success(self, mock_metadata_manager):
        """Test successful query matching."""
        metadata = {
            'data': {
                'title': 'Test Document',
                'tags': ['test', 'document'],
                'content_type': 'text/plain'
            }
        }
        
        # Test exact match
        assert mock_metadata_manager._matches_query(metadata, {'title': 'Test Document'}) is True
        
        # Test tag match
        assert mock_metadata_manager._matches_query(metadata, {'tags': ['test']}) is True
        
        # Test content type match
        assert mock_metadata_manager._matches_query(metadata, {'content_type': 'text/plain'}) is True
    
    @pytest.mark.unit
    def test_matches_query_failure(self, mock_metadata_manager):
        """Test failed query matching."""
        metadata = {
            'data': {
                'title': 'Test Document',
                'tags': ['test'],
                'content_type': 'text/plain'
            }
        }
        
        # Test non-matching title
        assert mock_metadata_manager._matches_query(metadata, {'title': 'Wrong Title'}) is False
        
        # Test non-matching tag
        assert mock_metadata_manager._matches_query(metadata, {'tags': ['nonexistent']}) is False
        
        # Test non-matching content type
        assert mock_metadata_manager._matches_query(metadata, {'content_type': 'image/jpeg'}) is False
    
    @pytest.mark.unit
    def test_health_check_success(self, mock_metadata_manager):
        """Test successful health check."""
        mock_metadata_manager.minio_client.client.bucket_exists.return_value = True
        mock_metadata_manager.minio_client.list_objects.return_value = [
            {'name': 'artifacts/test-id/metadata.json'}
        ]
        
        result = mock_metadata_manager.health_check()
        
        assert result['status'] == 'healthy'
        assert result['metadata_bucket_exists'] is True
        assert result['metadata_objects_count'] == 1


class TestStorageIntegration:
    """Integration tests for storage components."""
    
    @pytest.mark.integration
    async def test_artifact_upload_with_metadata(self):
        """Test complete artifact upload with metadata workflow."""
        # This would test the full workflow of uploading an artifact
        # and storing its metadata
        pass
    
    @pytest.mark.integration
    async def test_artifact_search_and_retrieval(self):
        """Test complete artifact search and retrieval workflow."""
        # This would test searching for artifacts and retrieving them
        pass
    
    @pytest.mark.integration
    async def test_backup_and_restore_workflow(self):
        """Test complete backup and restore workflow."""
        # This would test backing up artifacts and metadata,
        # then restoring them
        pass
