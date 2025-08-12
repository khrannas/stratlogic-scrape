import os
import hashlib
import mimetypes
import logging
from typing import Optional, Dict, Any, BinaryIO, List
from pathlib import Path
import magic

class StorageUtils:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Allowed file extensions for security
        self.allowed_extensions = {
            # Documents
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
            # Archives
            '.zip', '.tar', '.gz', '.rar', '.7z',
            # Data files
            '.csv', '.json', '.xml', '.yaml', '.yml',
            # Web content
            '.html', '.htm', '.css', '.js',
            # Audio/Video
            '.mp3', '.mp4', '.avi', '.mov', '.wav',
            # Code files
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go'
        }
        
        # Maximum file size (100MB)
        self.max_file_size = 100 * 1024 * 1024
        
        # Dangerous file extensions to block
        self.blocked_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js',
            '.jar', '.msi', '.dmg', '.app', '.deb', '.rpm'
        }

    def validate_file_extension(self, filename: str) -> bool:
        """Validate if file extension is allowed"""
        file_ext = Path(filename).suffix.lower()
        
        if file_ext in self.blocked_extensions:
            self.logger.warning(f"Blocked file extension: {file_ext}")
            return False
            
        if file_ext not in self.allowed_extensions:
            self.logger.warning(f"Unsupported file extension: {file_ext}")
            return False
            
        return True

    def validate_file_size(self, file_size: int) -> bool:
        """Validate if file size is within limits"""
        if file_size > self.max_file_size:
            self.logger.warning(f"File size {file_size} exceeds maximum {self.max_file_size}")
            return False
        return True

    def validate_file_content(self, file_data: BinaryIO, filename: str) -> bool:
        """Validate file content using magic numbers"""
        try:
            # Reset file pointer
            file_data.seek(0)
            
            # Read first 2048 bytes for magic number detection
            header = file_data.read(2048)
            file_data.seek(0)
            
            if not header:
                self.logger.warning("Empty file detected")
                return False
            
            # Use python-magic to detect MIME type
            mime_type = magic.from_buffer(header, mime=True)
            
            # Get expected MIME type from filename
            expected_mime, _ = mimetypes.guess_type(filename)
            
            # Basic validation - check if detected type matches expected
            if expected_mime and mime_type and mime_type != expected_mime:
                self.logger.warning(f"MIME type mismatch: expected {expected_mime}, got {mime_type}")
                # Don't fail for this, just log warning
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating file content: {e}")
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:255-len(ext)] + ext
            
        return sanitized

    def calculate_file_hash(self, file_data: BinaryIO, algorithm: str = 'sha256') -> str:
        """Calculate file hash using specified algorithm"""
        file_data.seek(0)
        
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha1':
            hash_obj = hashlib.sha1()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        for chunk in iter(lambda: file_data.read(4096), b""):
            hash_obj.update(chunk)
        
        file_data.seek(0)
        return hash_obj.hexdigest()

    def get_file_info(self, file_data: BinaryIO, filename: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        file_data.seek(0, os.SEEK_END)
        file_size = file_data.tell()
        file_data.seek(0)
        
        # Calculate hashes
        md5_hash = self.calculate_file_hash(file_data, 'md5')
        file_data.seek(0)
        sha256_hash = self.calculate_file_hash(file_data, 'sha256')
        file_data.seek(0)
        
        # Get MIME type
        mime_type, encoding = mimetypes.guess_type(filename)
        
        return {
            'filename': filename,
            'sanitized_filename': self.sanitize_filename(filename),
            'file_size': file_size,
            'mime_type': mime_type or 'application/octet-stream',
            'encoding': encoding,
            'extension': Path(filename).suffix.lower(),
            'md5_hash': md5_hash,
            'sha256_hash': sha256_hash,
            'is_valid': self.validate_file_extension(filename) and self.validate_file_size(file_size)
        }

    def chunk_file(self, file_data: BinaryIO, chunk_size: int = 8 * 1024 * 1024) -> List[bytes]:
        """Split file into chunks for multipart upload"""
        chunks = []
        file_data.seek(0)
        
        while True:
            chunk = file_data.read(chunk_size)
            if not chunk:
                break
            chunks.append(chunk)
        
        file_data.seek(0)
        return chunks

    def validate_upload_request(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Comprehensive validation of upload request"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_info': None
        }
        
        try:
            # Get file info
            file_info = self.get_file_info(file_data, filename)
            validation_result['file_info'] = file_info
            
            # Validate file extension
            if not self.validate_file_extension(filename):
                validation_result['valid'] = False
                validation_result['errors'].append(f"Invalid file extension: {file_info['extension']}")
            
            # Validate file size
            max_allowed = max_size or self.max_file_size
            if not self.validate_file_size(file_info['file_size']):
                validation_result['valid'] = False
                validation_result['errors'].append(f"File size {file_info['file_size']} exceeds maximum {max_allowed}")
            
            # Validate content type if provided
            if content_type and file_info['mime_type'] != content_type:
                validation_result['warnings'].append(f"MIME type mismatch: expected {content_type}, detected {file_info['mime_type']}")
            
            # Validate file content
            if not self.validate_file_content(file_data, filename):
                validation_result['warnings'].append("File content validation failed")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            self.logger.error(f"Error during upload validation: {e}")
        
        return validation_result

    def create_metadata_dict(
        self,
        file_info: Dict[str, Any],
        user_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Create metadata dictionary for MinIO upload"""
        metadata = {
            'x-amz-meta-original-filename': file_info['filename'],
            'x-amz-meta-file-size': str(file_info['file_size']),
            'x-amz-meta-content-type': file_info['mime_type'],
            'x-amz-meta-md5-hash': file_info['md5_hash'],
            'x-amz-meta-sha256-hash': file_info['sha256_hash'],
            'x-amz-meta-file-extension': file_info['extension'],
        }
        
        if user_id:
            metadata['x-amz-meta-user-id'] = user_id
        
        if additional_metadata:
            for key, value in additional_metadata.items():
                metadata[f'x-amz-meta-{key}'] = str(value)
        
        return metadata

storage_utils = StorageUtils()
