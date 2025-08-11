"""
Metadata manager for artifact metadata operations.

This module provides metadata management functionality including
tagging, search, validation, and backup operations.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Set
from pathlib import Path

from minio.error import S3Error
import structlog

from .minio_client import MinIOClient
from ..core.config import settings
from ..core.utils import get_logger, generate_uuid

logger = get_logger(__name__)


class MetadataManager:
    """Metadata manager for artifact metadata operations."""
    
    def __init__(self, minio_client: Optional[MinIOClient] = None):
        """Initialize metadata manager."""
        self.minio_client = minio_client or MinIOClient()
        self.metadata_bucket = "metadata"
        self._ensure_metadata_bucket_exists()
    
    def _ensure_metadata_bucket_exists(self):
        """Ensure metadata bucket exists."""
        try:
            if not self.minio_client.client.bucket_exists(self.metadata_bucket):
                self.minio_client.client.make_bucket(self.metadata_bucket)
                logger.info(f"Created metadata bucket: {self.metadata_bucket}")
        except S3Error as e:
            logger.error(f"Failed to create metadata bucket {self.metadata_bucket}: {e}")
            raise
    
    async def store_metadata(
        self,
        artifact_id: str,
        metadata: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Store metadata for an artifact.
        
        Args:
            artifact_id: Unique identifier for the artifact
            metadata: Metadata dictionary to store
            user_id: User ID who owns the metadata
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Add metadata management fields
            metadata_record = {
                'artifact_id': artifact_id,
                'user_id': user_id,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'version': '1.0',
                'data': metadata
            }
            
            # Calculate metadata hash for integrity
            metadata_hash = self._calculate_metadata_hash(metadata_record)
            metadata_record['hash'] = metadata_hash
            
            # Store in metadata bucket
            metadata_key = f"artifacts/{artifact_id}/metadata.json"
            metadata_json = json.dumps(metadata_record, indent=2)
            
            self.minio_client.upload_data(
                data=metadata_json.encode('utf-8'),
                object_name=metadata_key,
                content_type='application/json',
                metadata={
                    'artifact_id': artifact_id,
                    'user_id': user_id or '',
                    'metadata_hash': metadata_hash,
                    'created_at': metadata_record['created_at']
                }
            )
            
            logger.info(f"Stored metadata for artifact: {artifact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store metadata for artifact {artifact_id}: {e}")
            return False
    
    async def get_metadata(
        self,
        artifact_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for an artifact.
        
        Args:
            artifact_id: Unique identifier for the artifact
            user_id: User ID requesting the metadata (for access control)
            
        Returns:
            Metadata dictionary or None if not found/unauthorized
        """
        try:
            metadata_key = f"artifacts/{artifact_id}/metadata.json"
            
            # Check if metadata exists
            if not self.minio_client.object_exists(metadata_key):
                logger.warning(f"Metadata not found for artifact: {artifact_id}")
                return None
            
            # Get metadata object info for access control
            object_info = self.minio_client.get_object_info(metadata_key)
            if object_info and object_info.get('metadata'):
                metadata_info = object_info['metadata']
                metadata_user_id = metadata_info.get('user_id', '')
                
                # Check access control (only owner can access metadata)
                if user_id and user_id != metadata_user_id:
                    logger.warning(f"Access denied for metadata: {artifact_id}")
                    return None
            
            # Download metadata
            metadata_data = self.minio_client.download_data(metadata_key)
            if not metadata_data:
                logger.error(f"Failed to download metadata for artifact: {artifact_id}")
                return None
            
            # Parse metadata
            metadata_record = json.loads(metadata_data.decode('utf-8'))
            
            # Verify metadata hash
            stored_hash = metadata_record.get('hash')
            calculated_hash = self._calculate_metadata_hash(metadata_record)
            
            if stored_hash != calculated_hash:
                logger.error(f"Metadata hash mismatch for artifact: {artifact_id}")
                return None
            
            return metadata_record
            
        except Exception as e:
            logger.error(f"Failed to get metadata for artifact {artifact_id}: {e}")
            return None
    
    async def update_metadata(
        self,
        artifact_id: str,
        updates: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Update metadata for an artifact.
        
        Args:
            artifact_id: Unique identifier for the artifact
            updates: Metadata updates to apply
            user_id: User ID requesting the update (for access control)
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Get existing metadata
            existing_metadata = await self.get_metadata(artifact_id, user_id)
            if not existing_metadata:
                return False
            
            # Update metadata
            existing_data = existing_metadata.get('data', {})
            existing_data.update(updates)
            
            # Update metadata record
            existing_metadata['data'] = existing_data
            existing_metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Recalculate hash
            existing_metadata['hash'] = self._calculate_metadata_hash(existing_metadata)
            
            # Store updated metadata
            metadata_key = f"artifacts/{artifact_id}/metadata.json"
            metadata_json = json.dumps(existing_metadata, indent=2)
            
            self.minio_client.upload_data(
                data=metadata_json.encode('utf-8'),
                object_name=metadata_key,
                content_type='application/json',
                metadata={
                    'artifact_id': artifact_id,
                    'user_id': user_id or '',
                    'metadata_hash': existing_metadata['hash'],
                    'updated_at': existing_metadata['updated_at']
                }
            )
            
            logger.info(f"Updated metadata for artifact: {artifact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata for artifact {artifact_id}: {e}")
            return False
    
    async def add_tags(
        self,
        artifact_id: str,
        tags: List[str],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Add tags to an artifact.
        
        Args:
            artifact_id: Unique identifier for the artifact
            tags: List of tags to add
            user_id: User ID requesting the operation (for access control)
            
        Returns:
            True if tags added successfully, False otherwise
        """
        try:
            # Get existing metadata
            existing_metadata = await self.get_metadata(artifact_id, user_id)
            if not existing_metadata:
                return False
            
            # Get existing tags
            existing_data = existing_metadata.get('data', {})
            existing_tags = set(existing_data.get('tags', []))
            
            # Add new tags
            existing_tags.update(tags)
            
            # Update metadata
            existing_data['tags'] = list(existing_tags)
            
            # Store updated metadata
            return await self.update_metadata(artifact_id, existing_data, user_id)
            
        except Exception as e:
            logger.error(f"Failed to add tags for artifact {artifact_id}: {e}")
            return False
    
    async def remove_tags(
        self,
        artifact_id: str,
        tags: List[str],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Remove tags from an artifact.
        
        Args:
            artifact_id: Unique identifier for the artifact
            tags: List of tags to remove
            user_id: User ID requesting the operation (for access control)
            
        Returns:
            True if tags removed successfully, False otherwise
        """
        try:
            # Get existing metadata
            existing_metadata = await self.get_metadata(artifact_id, user_id)
            if not existing_metadata:
                return False
            
            # Get existing tags
            existing_data = existing_metadata.get('data', {})
            existing_tags = set(existing_data.get('tags', []))
            
            # Remove tags
            existing_tags.difference_update(tags)
            
            # Update metadata
            existing_data['tags'] = list(existing_tags)
            
            # Store updated metadata
            return await self.update_metadata(artifact_id, existing_data, user_id)
            
        except Exception as e:
            logger.error(f"Failed to remove tags for artifact {artifact_id}: {e}")
            return False
    
    async def search_metadata(
        self,
        query: Dict[str, Any],
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search metadata based on query criteria.
        
        Args:
            query: Search query dictionary
            user_id: User ID requesting the search (for access control)
            limit: Maximum number of results to return
            
        Returns:
            List of matching metadata records
        """
        try:
            # List all metadata objects
            metadata_objects = self.minio_client.list_objects(
                prefix="artifacts/",
                recursive=True
            )
            
            results = []
            for obj in metadata_objects:
                if obj['name'].endswith('/metadata.json'):
                    artifact_id = obj['name'].split('/')[1]
                    
                    # Get metadata for this artifact
                    metadata = await self.get_metadata(artifact_id, user_id)
                    if metadata and self._matches_query(metadata, query):
                        results.append(metadata)
                        
                        if len(results) >= limit:
                            break
            
            logger.info(f"Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search metadata: {e}")
            return []
    
    async def search_by_tags(
        self,
        tags: List[str],
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search artifacts by tags.
        
        Args:
            tags: List of tags to search for
            user_id: User ID requesting the search (for access control)
            limit: Maximum number of results to return
            
        Returns:
            List of matching metadata records
        """
        query = {'tags': tags}
        return await self.search_metadata(query, user_id, limit)
    
    async def search_by_content_type(
        self,
        content_type: str,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search artifacts by content type.
        
        Args:
            content_type: Content type to search for
            user_id: User ID requesting the search (for access control)
            limit: Maximum number of results to return
            
        Returns:
            List of matching metadata records
        """
        query = {'content_type': content_type}
        return await self.search_metadata(query, user_id, limit)
    
    async def backup_metadata(
        self,
        artifact_id: str,
        backup_name: Optional[str] = None
    ) -> bool:
        """
        Create a backup of metadata.
        
        Args:
            artifact_id: Unique identifier for the artifact
            backup_name: Optional custom backup name
            
        Returns:
            True if backup successful, False otherwise
        """
        try:
            metadata_key = f"artifacts/{artifact_id}/metadata.json"
            
            # Check if metadata exists
            if not self.minio_client.object_exists(metadata_key):
                logger.warning(f"Metadata not found for backup: {artifact_id}")
                return False
            
            # Generate backup name
            if not backup_name:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                backup_name = f"metadata_backup_{timestamp}_{artifact_id}.json"
            
            backup_key = f"backups/{backup_name}"
            
            # Copy metadata to backup
            self.minio_client.client.copy_object(
                bucket_name=self.metadata_bucket,
                object_name=backup_key,
                source=f"{self.metadata_bucket}/{metadata_key}"
            )
            
            logger.info(f"Backed up metadata for artifact {artifact_id} to {backup_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup metadata for artifact {artifact_id}: {e}")
            return False
    
    async def restore_metadata(
        self,
        backup_key: str,
        artifact_id: Optional[str] = None
    ) -> bool:
        """
        Restore metadata from backup.
        
        Args:
            backup_key: Key of the backup in metadata bucket
            artifact_id: Optional custom artifact ID for restore
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            # Check if backup exists
            if not self.minio_client.object_exists(backup_key):
                logger.error(f"Metadata backup not found: {backup_key}")
                return False
            
            # Get backup metadata
            backup_data = self.minio_client.download_data(backup_key)
            if not backup_data:
                logger.error(f"Failed to download metadata backup: {backup_key}")
                return False
            
            backup_record = json.loads(backup_data.decode('utf-8'))
            
            # Use provided artifact ID or extract from backup
            restore_artifact_id = artifact_id or backup_record.get('artifact_id')
            if not restore_artifact_id:
                logger.error(f"No artifact ID found in backup: {backup_key}")
                return False
            
            # Restore metadata
            restore_key = f"artifacts/{restore_artifact_id}/metadata.json"
            
            self.minio_client.client.copy_object(
                bucket_name=self.metadata_bucket,
                object_name=restore_key,
                source=f"{self.metadata_bucket}/{backup_key}"
            )
            
            logger.info(f"Restored metadata for artifact {restore_artifact_id} from {backup_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore metadata from {backup_key}: {e}")
            return False
    
    def _calculate_metadata_hash(self, metadata_record: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of metadata record."""
        # Create a copy without the hash field for calculation
        record_copy = metadata_record.copy()
        record_copy.pop('hash', None)
        
        # Convert to JSON string and calculate hash
        record_json = json.dumps(record_copy, sort_keys=True)
        return hashlib.sha256(record_json.encode('utf-8')).hexdigest()
    
    def _matches_query(self, metadata: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if metadata matches the search query."""
        try:
            metadata_data = metadata.get('data', {})
            
            for key, value in query.items():
                if key == 'tags':
                    # Special handling for tag search
                    if isinstance(value, list):
                        metadata_tags = set(metadata_data.get('tags', []))
                        query_tags = set(value)
                        if not query_tags.issubset(metadata_tags):
                            return False
                    else:
                        if value not in metadata_data.get('tags', []):
                            return False
                else:
                    # Regular field matching
                    if metadata_data.get(key) != value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching query: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on metadata system."""
        try:
            # Check metadata bucket access
            bucket_exists = self.minio_client.client.bucket_exists(self.metadata_bucket)
            
            # Count metadata objects
            metadata_objects = self.minio_client.list_objects(
                prefix="artifacts/",
                recursive=True
            )
            metadata_count = len([obj for obj in metadata_objects if obj['name'].endswith('/metadata.json')])
            
            return {
                'status': 'healthy' if bucket_exists else 'unhealthy',
                'metadata_bucket_exists': bucket_exists,
                'metadata_objects_count': metadata_count,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Metadata health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }


# Global metadata manager instance
metadata_manager = MetadataManager()
