import pytest
from unittest.mock import Mock, patch
from minio.error import S3Error

from src.storage.access_control import AccessControl


class TestAccessControl:
    """Test cases for access control functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.access_control = AccessControl(self.mock_client)

    def test_set_artifact_visibility_public(self):
        """Test setting artifact visibility to public."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client operations
        mock_stat = Mock()
        mock_stat.metadata = {"existing_key": "existing_value"}
        self.mock_client.client.stat_object.return_value = mock_stat
        self.mock_client.client.copy_object.return_value = None
        
        # Test setting visibility to public
        result = self.access_control.set_artifact_visibility(object_name, True)
        
        # Verify result
        assert result is True
        
        # Verify copy_object was called with correct metadata
        self.mock_client.client.copy_object.assert_called_once()
        call_args = self.mock_client.client.copy_object.call_args
        metadata = call_args[1]['metadata']
        assert metadata['x-amz-meta-is-public'] == 'true'
        assert metadata['existing_key'] == 'existing_value'

    def test_set_artifact_visibility_private(self):
        """Test setting artifact visibility to private."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client operations
        mock_stat = Mock()
        mock_stat.metadata = {"existing_key": "existing_value"}
        self.mock_client.client.stat_object.return_value = mock_stat
        self.mock_client.client.copy_object.return_value = None
        
        # Test setting visibility to private
        result = self.access_control.set_artifact_visibility(object_name, False)
        
        # Verify result
        assert result is True
        
        # Verify copy_object was called with correct metadata
        self.mock_client.client.copy_object.assert_called_once()
        call_args = self.mock_client.client.copy_object.call_args
        metadata = call_args[1]['metadata']
        assert metadata['x-amz-meta-is-public'] == 'false'

    def test_set_artifact_visibility_error(self):
        """Test setting artifact visibility with error."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client to raise error
        self.mock_client.client.stat_object.side_effect = S3Error("Operation failed")
        
        # Test setting visibility
        result = self.access_control.set_artifact_visibility(object_name, True)
        
        # Verify result is False
        assert result is False

    def test_check_access_permission_public_artifact(self):
        """Test access permission for public artifact."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client response
        mock_stat = Mock()
        mock_stat.metadata = {"x-amz-meta-is-public": "true"}
        self.mock_client.client.stat_object.return_value = mock_stat
        
        # Test access permission (should be allowed for any user)
        result = self.access_control.check_access_permission(object_name, "user456")
        
        # Verify result
        assert result is True

    def test_check_access_permission_owner_access(self):
        """Test access permission for artifact owner."""
        object_name = "user123/test-file.txt"
        user_id = "user123"
        
        # Mock MinIO client response
        mock_stat = Mock()
        mock_stat.metadata = {
            "x-amz-meta-is-public": "false",
            "x-amz-meta-user-id": "user123"
        }
        self.mock_client.client.stat_object.return_value = mock_stat
        
        # Test access permission (should be allowed for owner)
        result = self.access_control.check_access_permission(object_name, user_id)
        
        # Verify result
        assert result is True

    def test_check_access_permission_denied(self):
        """Test access permission denied for non-owner."""
        object_name = "user123/test-file.txt"
        user_id = "user456"
        
        # Mock MinIO client response
        mock_stat = Mock()
        mock_stat.metadata = {
            "x-amz-meta-is-public": "false",
            "x-amz-meta-user-id": "user123"
        }
        self.mock_client.client.stat_object.return_value = mock_stat
        
        # Test access permission (should be denied for non-owner)
        result = self.access_control.check_access_permission(object_name, user_id)
        
        # Verify result
        assert result is False

    def test_check_access_permission_no_user_id(self):
        """Test access permission with no user ID."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client response
        mock_stat = Mock()
        mock_stat.metadata = {
            "x-amz-meta-is-public": "false",
            "x-amz-meta-user-id": "user123"
        }
        self.mock_client.client.stat_object.return_value = mock_stat
        
        # Test access permission with no user ID
        result = self.access_control.check_access_permission(object_name, None)
        
        # Verify result
        assert result is False

    def test_check_access_permission_error(self):
        """Test access permission check with error."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client to raise error
        self.mock_client.client.stat_object.side_effect = S3Error("Operation failed")
        
        # Test access permission check
        result = self.access_control.check_access_permission(object_name, "user123")
        
        # Verify result is False
        assert result is False

    def test_generate_presigned_url_get(self):
        """Test generating presigned URL for GET operation."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client response
        expected_url = "https://minio.example.com/presigned-get-url"
        self.mock_client.client.presigned_get_object.return_value = expected_url
        
        # Test URL generation
        result = self.access_control.generate_presigned_url(object_name, method='GET')
        
        # Verify result
        assert result == expected_url
        self.mock_client.client.presigned_get_object.assert_called_once()

    def test_generate_presigned_url_put(self):
        """Test generating presigned URL for PUT operation."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client response
        expected_url = "https://minio.example.com/presigned-put-url"
        self.mock_client.client.presigned_put_object.return_value = expected_url
        
        # Test URL generation
        result = self.access_control.generate_presigned_url(object_name, method='PUT')
        
        # Verify result
        assert result == expected_url
        self.mock_client.client.presigned_put_object.assert_called_once()

    def test_generate_presigned_url_custom_method(self):
        """Test generating presigned URL for custom method."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client response
        expected_url = "https://minio.example.com/presigned-custom-url"
        self.mock_client.client.get_presigned_url.return_value = expected_url
        
        # Test URL generation
        result = self.access_control.generate_presigned_url(object_name, method='DELETE')
        
        # Verify result
        assert result == expected_url
        self.mock_client.client.get_presigned_url.assert_called_once()

    def test_generate_presigned_url_error(self):
        """Test presigned URL generation with error."""
        object_name = "user123/test-file.txt"
        
        # Mock MinIO client to raise error
        self.mock_client.client.presigned_get_object.side_effect = S3Error("URL generation failed")
        
        # Test URL generation
        result = self.access_control.generate_presigned_url(object_name)
        
        # Verify result is None
        assert result is None

    def test_set_bucket_policy_success(self):
        """Test setting bucket policy successfully."""
        bucket_name = "test-bucket"
        policy = {"Version": "2012-10-17", "Statement": []}
        
        # Mock MinIO client operations
        self.mock_client.client.set_bucket_policy.return_value = None
        
        # Test setting bucket policy
        result = self.access_control.set_bucket_policy(bucket_name, policy)
        
        # Verify result
        assert result is True
        self.mock_client.client.set_bucket_policy.assert_called_once()

    def test_set_bucket_policy_error(self):
        """Test setting bucket policy with error."""
        bucket_name = "test-bucket"
        policy = {"Version": "2012-10-17", "Statement": []}
        
        # Mock MinIO client to raise error
        self.mock_client.client.set_bucket_policy.side_effect = S3Error("Policy setting failed")
        
        # Test setting bucket policy
        result = self.access_control.set_bucket_policy(bucket_name, policy)
        
        # Verify result is False
        assert result is False

    def test_get_bucket_policy_success(self):
        """Test getting bucket policy successfully."""
        bucket_name = "test-bucket"
        expected_policy = {"Version": "2012-10-17", "Statement": []}
        
        # Mock MinIO client response
        self.mock_client.client.get_bucket_policy.return_value = '{"Version": "2012-10-17", "Statement": []}'
        
        # Test getting bucket policy
        result = self.access_control.get_bucket_policy(bucket_name)
        
        # Verify result
        assert result == expected_policy
        self.mock_client.client.get_bucket_policy.assert_called_once_with(bucket_name)

    def test_get_bucket_policy_error(self):
        """Test getting bucket policy with error."""
        bucket_name = "test-bucket"
        
        # Mock MinIO client to raise error
        self.mock_client.client.get_bucket_policy.side_effect = S3Error("Policy retrieval failed")
        
        # Test getting bucket policy
        result = self.access_control.get_bucket_policy(bucket_name)
        
        # Verify result is None
        assert result is None

    def test_create_public_read_policy(self):
        """Test creating public read policy."""
        bucket_name = "test-bucket"
        
        # Test policy creation
        policy = self.access_control.create_public_read_policy(bucket_name)
        
        # Verify policy structure
        assert policy["Version"] == "2012-10-17"
        assert len(policy["Statement"]) == 2
        
        # Verify first statement allows bucket operations
        bucket_statement = policy["Statement"][0]
        assert bucket_statement["Effect"] == "Allow"
        assert bucket_statement["Principal"]["AWS"] == "*"
        assert "s3:GetBucketLocation" in bucket_statement["Action"]
        assert "s3:ListBucket" in bucket_statement["Action"]
        assert bucket_statement["Resource"] == f"arn:aws:s3:::{bucket_name}"
        
        # Verify second statement allows object access
        object_statement = policy["Statement"][1]
        assert object_statement["Effect"] == "Allow"
        assert object_statement["Principal"]["AWS"] == "*"
        assert object_statement["Action"] == "s3:GetObject"
        assert object_statement["Resource"] == f"arn:aws:s3:::{bucket_name}/*"

    def test_create_private_policy(self):
        """Test creating private policy."""
        bucket_name = "test-bucket"
        
        # Test policy creation
        policy = self.access_control.create_private_policy(bucket_name)
        
        # Verify policy structure
        assert policy["Version"] == "2012-10-17"
        assert len(policy["Statement"]) == 1
        
        # Verify statement denies object access
        statement = policy["Statement"][0]
        assert statement["Effect"] == "Deny"
        assert statement["Principal"]["AWS"] == "*"
        assert statement["Action"] == ["s3:GetObject"]
        assert statement["Resource"] == f"arn:aws:s3:::{bucket_name}/*"
