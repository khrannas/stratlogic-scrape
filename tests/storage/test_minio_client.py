import pytest
from unittest.mock import Mock, patch, MagicMock
from minio.error import S3Error

from src.storage.minio_client import MinIOClient


class TestMinIOClient:
    """Test cases for MinIO client functionality."""

    @patch('src.storage.minio_client.Minio')
    @patch('src.storage.minio_client.settings')
    def test_minio_client_initialization(self, mock_settings, mock_minio):
        """Test MinIO client initialization."""
        # Mock settings
        mock_settings.MINIO_ENDPOINT = "localhost:9000"
        mock_settings.MINIO_ACCESS_KEY = "test_key"
        mock_settings.MINIO_SECRET_KEY = "test_secret"
        mock_settings.MINIO_SECURE = False

        # Mock MinIO client
        mock_client = Mock()
        mock_minio.return_value = mock_client

        # Mock bucket operations
        mock_client.bucket_exists.return_value = False
        mock_client.make_bucket.return_value = None

        # Create client
        client = MinIOClient()

        # Verify MinIO client was created with correct parameters
        mock_minio.assert_called_once_with(
            endpoint="localhost:9000",
            access_key="test_key",
            secret_key="test_secret",
            secure=False
        )

        # Verify buckets were checked and created
        expected_buckets = ['artifacts', 'temp', 'backup']
        for bucket in expected_buckets:
            mock_client.bucket_exists.assert_any_call(bucket)
            mock_client.make_bucket.assert_any_call(bucket)

    @patch('src.storage.minio_client.Minio')
    @patch('src.storage.minio_client.settings')
    def test_minio_client_initialization_existing_buckets(self, mock_settings, mock_minio):
        """Test MinIO client initialization with existing buckets."""
        # Mock settings
        mock_settings.MINIO_ENDPOINT = "localhost:9000"
        mock_settings.MINIO_ACCESS_KEY = "test_key"
        mock_settings.MINIO_SECRET_KEY = "test_secret"
        mock_settings.MINIO_SECURE = False

        # Mock MinIO client
        mock_client = Mock()
        mock_minio.return_value = mock_client

        # Mock existing buckets
        mock_client.bucket_exists.return_value = True

        # Create client
        client = MinIOClient()

        # Verify buckets were checked but not created
        expected_buckets = ['artifacts', 'temp', 'backup']
        for bucket in expected_buckets:
            mock_client.bucket_exists.assert_any_call(bucket)
            mock_client.make_bucket.assert_not_called()

    @patch('src.storage.minio_client.Minio')
    @patch('src.storage.minio_client.settings')
    def test_minio_client_initialization_error(self, mock_settings, mock_minio):
        """Test MinIO client initialization with error."""
        # Mock settings
        mock_settings.MINIO_ENDPOINT = "localhost:9000"
        mock_settings.MINIO_ACCESS_KEY = "test_key"
        mock_settings.MINIO_SECRET_KEY = "test_secret"
        mock_settings.MINIO_SECURE = False

        # Mock MinIO client to raise exception
        mock_minio.side_effect = Exception("Connection failed")

        # Test that exception is raised
        with pytest.raises(Exception, match="Connection failed"):
            MinIOClient()

    @patch('src.storage.minio_client.Minio')
    @patch('src.storage.minio_client.settings')
    def test_health_check_success(self, mock_settings, mock_minio):
        """Test successful health check."""
        # Mock settings
        mock_settings.MINIO_ENDPOINT = "localhost:9000"
        mock_settings.MINIO_ACCESS_KEY = "test_key"
        mock_settings.MINIO_SECRET_KEY = "test_secret"
        mock_settings.MINIO_SECURE = False

        # Mock MinIO client
        mock_client = Mock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.list_buckets.return_value = []

        # Create client
        client = MinIOClient()

        # Test health check
        result = client.health_check()

        # Verify result
        assert result is True
        mock_client.list_buckets.assert_called_once()

    @patch('src.storage.minio_client.Minio')
    @patch('src.storage.minio_client.settings')
    def test_health_check_failure(self, mock_settings, mock_minio):
        """Test failed health check."""
        # Mock settings
        mock_settings.MINIO_ENDPOINT = "localhost:9000"
        mock_settings.MINIO_ACCESS_KEY = "test_key"
        mock_settings.MINIO_SECRET_KEY = "test_secret"
        mock_settings.MINIO_SECURE = False

        # Mock MinIO client
        mock_client = Mock()
        mock_minio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.list_buckets.side_effect = Exception("Connection failed")

        # Create client
        client = MinIOClient()

        # Test health check
        result = client.health_check()

        # Verify result
        assert result is False
        mock_client.list_buckets.assert_called_once()

    @patch('src.storage.minio_client.Minio')
    @patch('src.storage.minio_client.settings')
    def test_bucket_creation_error(self, mock_settings, mock_minio):
        """Test bucket creation error handling."""
        # Mock settings
        mock_settings.MINIO_ENDPOINT = "localhost:9000"
        mock_settings.MINIO_ACCESS_KEY = "test_key"
        mock_settings.MINIO_SECRET_KEY = "test_secret"
        mock_settings.MINIO_SECURE = False

        # Mock MinIO client
        mock_client = Mock()
        mock_minio.return_value = mock_client

        # Mock bucket operations
        mock_client.bucket_exists.return_value = False
        mock_client.make_bucket.side_effect = S3Error("Bucket creation failed")

        # Test that exception is raised
        with pytest.raises(S3Error, match="Bucket creation failed"):
            MinIOClient()
