import logging
from typing import List, Dict, Any

from minio.error import S3Error

from .minio_client import minio_client

class MetadataManager:
    def __init__(self, client=minio_client):
        self.minio_client = client
        self.logger = logging.getLogger(__name__)

    def add_metadata_tags(self, object_name: str, tags: Dict[str, Any], bucket_name: str = "artifacts") -> bool:
        """Add metadata tags to an artifact. This requires a copy operation in S3/MinIO."""
        try:
            # Get existing metadata
            stat = self.minio_client.client.stat_object(bucket_name, object_name)
            existing_metadata = stat.metadata.copy() # Make a mutable copy

            # Add new tags, ensuring they are prefixed correctly for user metadata
            for key, value in tags.items():
                # S3/MinIO user metadata keys are case-insensitive and stored in lowercase
                # The http header will be x-amz-meta-yourkey
                existing_metadata[f"X-Amz-Meta-{key.lower()}"] = str(value)

            # Copy object to itself to apply new metadata
            self.minio_client.client.copy_object(
                bucket_name,
                object_name,
                f"/{bucket_name}/{object_name}",
                metadata=existing_metadata,
            )

            return True

        except S3Error as e:
            self.logger.error(f"Failed to add metadata tags: {e}")
            return False

    def search_artifacts_by_metadata(self, tags: Dict[str, Any], bucket_name: str = "artifacts") -> List[str]:
        """
        Search artifacts by metadata tags.
        Note: This is a very inefficient operation and should not be used in production
        on large buckets. It requires iterating over all objects. A real implementation
        would use a search index like Elasticsearch.
        """
        matching_objects = []
        try:
            objects = self.minio_client.client.list_objects(bucket_name, recursive=True)

            for obj in objects:
                stat = self.minio_client.client.stat_object(bucket_name, obj.object_name)

                # Metadata keys are stored in lowercase by MinIO/S3 standard
                metadata = {k.lower(): v for k, v in stat.metadata.items()}

                matches = True
                for key, value in tags.items():
                    meta_key = f"x-amz-meta-{key.lower()}"
                    if meta_key not in metadata or metadata[meta_key] != str(value):
                        matches = False
                        break

                if matches:
                    matching_objects.append(obj.object_name)

            return matching_objects

        except S3Error as e:
            self.logger.error(f"Failed to search artifacts: {e}")
            return []

metadata_manager_service = MetadataManager()
