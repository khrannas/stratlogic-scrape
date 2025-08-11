"""
Utility functions for StratLogic Scraping System.

This module contains common utility functions used throughout the application
including logging, validation, file handling, and helper functions.
"""

import hashlib
import json
import logging
import os
import re
import structlog
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse, urljoin
import uuid

from .config import settings


# Configure structured logging
def setup_logging():
    """Setup structured logging configuration."""
    if settings.log_format == "json":
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        structlog.BoundLogger: Configured logger
    """
    return structlog.get_logger(name)


def generate_uuid() -> str:
    """
    Generate a UUID string.
    
    Returns:
        str: UUID string
    """
    return str(uuid.uuid4())


def generate_hash(content: str, algorithm: str = "sha256") -> str:
    """
    Generate hash of content.
    
    Args:
        content: Content to hash
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        str: Hash string
    """
    hash_func = getattr(hashlib, algorithm)
    return hash_func(content.encode()).hexdigest()


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def clean_filename(filename: str) -> str:
    """
    Clean filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Cleaned filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores and dots
    filename = filename.strip('_.')
    return filename


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Filename
        
    Returns:
        str: File extension (without dot)
    """
    return Path(filename).suffix.lower().lstrip('.')


def is_allowed_file_type(filename: str) -> bool:
    """
    Check if file type is allowed.
    
    Args:
        filename: Filename to check
        
    Returns:
        bool: True if allowed, False otherwise
    """
    extension = get_file_extension(filename)
    return extension in settings.allowed_file_types


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def parse_file_size(size_str: str) -> int:
    """
    Parse file size string to bytes.
    
    Args:
        size_str: Size string (e.g., "100MB", "1.5GB")
        
    Returns:
        int: Size in bytes
    """
    size_str = size_str.upper().strip()
    if size_str.endswith("B"):
        size_str = size_str[:-1]
    
    multipliers = {
        "K": 1024,
        "M": 1024 ** 2,
        "G": 1024 ** 3,
        "T": 1024 ** 4,
    }
    
    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            return int(float(size_str[:-1]) * multiplier)
    
    return int(float(size_str))


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path
        
    Returns:
        Path: Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_json_dumps(obj: Any) -> str:
    """
    Safely serialize object to JSON string.
    
    Args:
        obj: Object to serialize
        
    Returns:
        str: JSON string
    """
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    return json.dumps(obj, default=default_serializer, ensure_ascii=False)


def parse_datetime(datetime_str: str) -> Optional[datetime]:
    """
    Parse datetime string to datetime object.
    
    Args:
        datetime_str: Datetime string
        
    Returns:
        Optional[datetime]: Parsed datetime or None
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    
    return None


def get_current_timestamp() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        datetime: Current UTC datetime
    """
    return datetime.now(timezone.utc)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List[List[Any]]: List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL string
        
    Returns:
        Optional[str]: Domain or None
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    Normalize URL by resolving relative URLs.
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs
        
    Returns:
        str: Normalized URL
    """
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Remove fragments
    url = url.split('#')[0]
    
    # Ensure scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url


# Initialize logging
setup_logging()
