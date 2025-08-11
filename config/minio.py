"""
MinIO configuration module.

This module contains MinIO-specific configuration and utilities.
"""

from minio import Minio
from minio.error import S3Error
from typing import Optional, Dict, Any

from ..src.core.config import settings


def create_minio_client():
    """Create MinIO client with configuration."""
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_use_ssl,
    )


def check_minio_health():
    """Check MinIO health and connectivity."""
    try:
        client = create_minio_client()
        # Try to list buckets to check connectivity
        client.list_buckets()
        return True
    except S3Error:
        return False
    except Exception:
        return False


def get_minio_info():
    """Get MinIO connection information."""
    return {
        "endpoint": settings.minio_endpoint,
        "bucket": settings.minio_bucket_name,
        "secure": settings.minio_use_ssl,
        "access_key": settings.minio_access_key[:8] + "***" if settings.minio_access_key else None,
    }


def ensure_bucket_exists(bucket_name: Optional[str] = None):
    """Ensure MinIO bucket exists."""
    if bucket_name is None:
        bucket_name = settings.minio_bucket_name
    
    try:
        client = create_minio_client()
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            return True
        return True
    except S3Error:
        return False
    except Exception:
        return False


def get_minio_policy():
    """Get MinIO bucket policy configuration."""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{settings.minio_bucket_name}",
                    f"arn:aws:s3:::{settings.minio_bucket_name}/*"
                ]
            }
        ]
    }
