import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from minio.error import S3Error

from .minio_client import minio_client

class AccessControl:
    def __init__(self, client=minio_client):
        self.minio_client = client
        self.logger = logging.getLogger(__name__)

    def set_artifact_visibility(
        self,
        object_name: str,
        is_public: bool,
        bucket_name: str = "artifacts"
    ) -> bool:
        """Set artifact visibility (public/private)"""
        try:
            # Get current metadata
            stat = self.minio_client.client.stat_object(bucket_name, object_name)
            metadata = stat.metadata.copy() if stat.metadata else {}

            # Update visibility
            metadata['x-amz-meta-is-public'] = str(is_public).lower()

            # Update object with new metadata
            self.minio_client.client.copy_object(
                bucket_name, object_name,
                bucket_name, object_name,
                metadata=metadata,
                metadata_directive='REPLACE'
            )

            self.logger.info(f"Set artifact {object_name} visibility to {'public' if is_public else 'private'}")
            return True

        except S3Error as e:
            self.logger.error(f"Failed to set artifact visibility: {e}")
            return False

    def check_access_permission(
        self,
        object_name: str,
        user_id: Optional[str],
        bucket_name: str = "artifacts"
    ) -> bool:
        """Check if user has access to artifact"""
        try:
            stat = self.minio_client.client.stat_object(bucket_name, object_name)
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

    def generate_presigned_url(
        self,
        object_name: str,
        bucket_name: str = "artifacts",
        expires_sec: int = 3600,
        method: str = 'GET'
    ) -> Optional[str]:
        """Generate a presigned URL for secure access"""
        try:
            if method.upper() == 'GET':
                url = self.minio_client.client.presigned_get_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    expires=timedelta(seconds=expires_sec)
                )
            elif method.upper() == 'PUT':
                url = self.minio_client.client.presigned_put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    expires=timedelta(seconds=expires_sec)
                )
            else:
                url = self.minio_client.client.get_presigned_url(
                    method=method,
                    bucket_name=bucket_name,
                    object_name=object_name,
                    expires=timedelta(seconds=expires_sec)
                )
            
            return url

        except S3Error as e:
            self.logger.error(f"Failed to generate presigned URL: {e}")
            return None

    def set_bucket_policy(
        self,
        bucket_name: str,
        policy: Dict[str, Any]
    ) -> bool:
        """Set bucket policy for access control"""
        try:
            import json
            policy_json = json.dumps(policy)
            self.minio_client.client.set_bucket_policy(bucket_name, policy_json)
            self.logger.info(f"Set bucket policy for {bucket_name}")
            return True

        except S3Error as e:
            self.logger.error(f"Failed to set bucket policy: {e}")
            return False

    def get_bucket_policy(self, bucket_name: str) -> Optional[Dict[str, Any]]:
        """Get bucket policy"""
        try:
            import json
            policy_json = self.minio_client.client.get_bucket_policy(bucket_name)
            return json.loads(policy_json)

        except S3Error as e:
            self.logger.error(f"Failed to get bucket policy: {e}")
            return None

    def create_public_read_policy(self, bucket_name: str) -> Dict[str, Any]:
        """Create a public read policy for a bucket"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                    "Resource": f"arn:aws:s3:::{bucket_name}"
                },
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }

    def create_private_policy(self, bucket_name: str) -> Dict[str, Any]:
        """Create a private policy for a bucket"""
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }

access_control_service = AccessControl()
