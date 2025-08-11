"""
Tests for MinIO connection and operations.

This module tests MinIO connectivity and basic operations.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os

from src.storage.minio_client import MinIOClient


class TestMinIOClient:
    """Test MinIO client functionality."""
    
    @pytest.fixture
    def mock_minio_client(self):
        """Create a mock MinIO client."""
        with patch('src.storage.minio_client.Minio') as mock_minio:
            client = MinIOClient()
            yield client
    
    @pytest.mark.unit
    def test_minio_client_initialization(self, mock_minio_client):
        """Test MinIO client initialization."""
        assert mock_minio_client.bucket_name == "stratlogic-artifacts"
    
    @pytest.mark.unit
    def test_upload_file_success(self, mock_minio_client):
        """Test successful file upload."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=b"test data")):
                result = mock_minio_client.upload_file(
                    file_path="/tmp/test.txt",
                    object_name="test/test.txt"
                )
                assert result == "test/test.txt"
    
    @pytest.mark.unit
    def test_upload_file_not_found(self, mock_minio_client):
        """Test file upload with non-existent file."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                mock_minio_client.upload_file("/tmp/nonexistent.txt")
    
    @pytest.mark.unit
    def test_upload_data_success(self, mock_minio_client):
        """Test successful data upload."""
        test_data = b"test data"
        result = mock_minio_client.upload_data(
            data=test_data,
            object_name="test/data.txt"
        )
        assert result == "test/data.txt"
    
    @pytest.mark.unit
    def test_download_file_success(self, mock_minio_client):
        """Test successful file download."""
        with patch('os.makedirs'):
            result = mock_minio_client.download_file(
                object_name="test/test.txt",
                file_path="/tmp/downloaded.txt"
            )
            assert result is True
    
    @pytest.mark.unit
    def test_download_data_success(self, mock_minio_client):
        """Test successful data download."""
        test_data = b"test data"
        mock_response = MagicMock()
        mock_response.read.return_value = test_data
        mock_response.close = MagicMock()
        mock_response.release_conn = MagicMock()
        
        mock_minio_client.client.get_object.return_value = mock_response
        
        result = mock_minio_client.download_data("test/data.txt")
        assert result == test_data
    
    @pytest.mark.unit
    def test_delete_object_success(self, mock_minio_client):
        """Test successful object deletion."""
        result = mock_minio_client.delete_object("test/test.txt")
        assert result is True
    
    @pytest.mark.unit
    def test_list_objects_success(self, mock_minio_client):
        """Test successful object listing."""
        mock_object = MagicMock()
        mock_object.object_name = "test/test.txt"
        mock_object.size = 1024
        mock_object.last_modified = "2024-01-01T00:00:00Z"
        mock_object.etag = "test-etag"
        
        mock_minio_client.client.list_objects.return_value = [mock_object]
        
        result = mock_minio_client.list_objects()
        assert len(result) == 1
        assert result[0]["name"] == "test/test.txt"
        assert result[0]["size"] == 1024
    
    @pytest.mark.unit
    def test_object_exists_true(self, mock_minio_client):
        """Test object existence check - exists."""
        result = mock_minio_client.object_exists("test/test.txt")
        assert result is True
    
    @pytest.mark.unit
    def test_object_exists_false(self, mock_minio_client):
        """Test object existence check - doesn't exist."""
        mock_minio_client.client.stat_object.side_effect = Exception("Not found")
        
        result = mock_minio_client.object_exists("test/nonexistent.txt")
        assert result is False
    
    @pytest.mark.unit
    def test_get_presigned_url_success(self, mock_minio_client):
        """Test successful presigned URL generation."""
        mock_minio_client.client.presigned_url.return_value = "https://example.com/presigned-url"
        
        result = mock_minio_client.get_presigned_url("test/test.txt")
        assert result == "https://example.com/presigned-url"
    
    @pytest.mark.unit
    def test_get_content_type(self, mock_minio_client):
        """Test content type detection."""
        test_cases = [
            ("test.pdf", "application/pdf"),
            ("test.txt", "text/plain"),
            ("test.html", "text/html"),
            ("test.json", "application/json"),
            ("test.jpg", "image/jpeg"),
            ("test.unknown", "application/octet-stream"),
        ]
        
        for filename, expected_type in test_cases:
            result = mock_minio_client._get_content_type(filename)
            assert result == expected_type
    
    @pytest.mark.unit
    def test_calculate_file_hash(self, mock_minio_client):
        """Test file hash calculation."""
        test_data = b"test data for hashing"
        
        with patch('builtins.open', mock_open(read_data=test_data)):
            result = mock_minio_client.calculate_file_hash("/tmp/test.txt")
            assert result is not None
            assert len(result) == 64  # SHA256 hash length
