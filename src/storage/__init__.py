"""
Storage package for StratLogic Scraping System.

This package provides MinIO object storage integration for artifact storage,
including upload/download operations, metadata management, access control,
and utility functions for file validation and processing.
"""

from .minio_client import MinIOClient, get_minio_client
from .artifact_storage import ArtifactStorage
from .metadata_manager import MetadataManager
from .access_control import AccessControl
from .utils import StorageUtils

# Lazy initialization functions
def get_artifact_storage_service():
    """Get or create artifact storage service instance."""
    from .artifact_storage import artifact_storage_service
    return artifact_storage_service

def get_metadata_manager_service():
    """Get or create metadata manager service instance."""
    from .metadata_manager import metadata_manager_service
    return metadata_manager_service

def get_access_control_service():
    """Get or create access control service instance."""
    from .access_control import access_control_service
    return access_control_service

def get_storage_utils():
    """Get or create storage utils instance."""
    from .utils import storage_utils
    return storage_utils

__all__ = [
    # Client
    'MinIOClient',
    'get_minio_client',
    
    # Services
    'ArtifactStorage',
    'MetadataManager',
    'AccessControl',
    'StorageUtils',
    
    # Lazy initialization functions
    'get_artifact_storage_service',
    'get_metadata_manager_service',
    'get_access_control_service',
    'get_storage_utils',
]

# Version info
__version__ = "1.0.0"
