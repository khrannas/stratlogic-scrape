"""
Storage tests configuration.
This conftest.py is specific to storage tests and doesn't require database connection.
"""

import pytest
from unittest.mock import Mock, patch
from minio.error import S3Error

@pytest.fixture
def mock_minio_client():
    """Mock MinIO client for testing."""
    mock_client = Mock()
    return mock_client

@pytest.fixture
def mock_s3_error():
    """Mock S3Error for testing."""
    error = S3Error("Test error")
    error.code = 'TestError'
    return error

@pytest.fixture
def mock_s3_error_no_such_key():
    """Mock S3Error for NoSuchKey."""
    error = S3Error("NoSuchKey")
    error.code = 'NoSuchKey'
    return error
