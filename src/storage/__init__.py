"""
Storage module for StratLogic Scraping System.

This module provides object storage functionality using MinIO,
including artifact storage, metadata management, and access control.
"""

from .minio_client import MinIOClient
from .artifact_storage import ArtifactStorage, artifact_storage
from .metadata_manager import MetadataManager, metadata_manager

__all__ = [
    'MinIOClient',
    'ArtifactStorage',
    'artifact_storage',
    'MetadataManager',
    'metadata_manager'
]
