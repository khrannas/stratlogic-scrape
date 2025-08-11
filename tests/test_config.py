"""
Tests for configuration management.

This module tests the configuration loading and validation.
"""

import pytest
import os
from unittest.mock import patch

from src.core.config import Settings, get_settings


class TestSettings:
    """Test Settings class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            
            assert settings.environment == "development"
            assert settings.debug is True
            assert settings.log_level == "INFO"
            assert settings.minio_bucket_name == "stratlogic-artifacts"
    
    def test_environment_variables(self):
        """Test environment variable loading."""
        test_env = {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "ERROR",
            "MINIO_BUCKET_NAME": "test-bucket",
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            
            assert settings.environment == "production"
            assert settings.debug is False
            assert settings.log_level == "ERROR"
            assert settings.minio_bucket_name == "test-bucket"
    
    def test_list_parsing(self):
        """Test list field parsing."""
        test_env = {
            "ALLOWED_HOSTS": "localhost,example.com,test.com",
            "CORS_ORIGINS": "http://localhost:3000,https://example.com",
            "ALLOWED_FILE_TYPES": "pdf,txt,doc",
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            
            assert settings.allowed_hosts == ["localhost", "example.com", "test.com"]
            assert settings.cors_origins == ["http://localhost:3000", "https://example.com"]
            assert settings.allowed_file_types == ["pdf", "txt", "doc"]
    
    def test_file_size_parsing(self):
        """Test file size parsing."""
        test_cases = [
            ("100MB", 100 * 1024 * 1024),
            ("1.5GB", int(1.5 * 1024 * 1024 * 1024)),
            ("500KB", 500 * 1024),
            ("1024B", 1024),
            ("1000", 1000),
        ]
        
        for size_str, expected_bytes in test_cases:
            with patch.dict(os.environ, {"MAX_FILE_SIZE": size_str}, clear=True):
                settings = Settings()
                assert settings.max_file_size == expected_bytes
    
    def test_required_fields(self):
        """Test required field validation."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                Settings()


class TestGetSettings:
    """Test get_settings function."""
    
    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
