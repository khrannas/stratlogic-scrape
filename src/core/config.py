"""
Configuration management for StratLogic Scraping System.

This module handles all configuration settings using Pydantic settings
for type safety and validation.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Settings
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], env="ALLOWED_HOSTS")
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    postgres_password: str = Field(default="stratlogic_password", env="POSTGRES_PASSWORD")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # MinIO Configuration
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin123", env="MINIO_SECRET_KEY")
    minio_use_ssl: bool = Field(default=False, env="MINIO_USE_SSL")
    minio_bucket_name: str = Field(default="stratlogic-artifacts", env="MINIO_BUCKET_NAME")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    
    # LLM Configuration
    default_llm_provider: str = Field(default="openai", env="DEFAULT_LLM_PROVIDER")
    default_model: str = Field(default="gpt-4", env="DEFAULT_MODEL")
    max_tokens: int = Field(default=4000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    
    # Scraping Configuration
    scraping_delay: int = Field(default=1, env="SCRAPING_DELAY")
    max_concurrent_scrapers: int = Field(default=5, env="MAX_CONCURRENT_SCRAPERS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; StratLogic/1.0; +https://stratlogic.com)",
        env="USER_AGENT"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # File Storage
    max_file_size: str = Field(default="100MB", env="MAX_FILE_SIZE")
    allowed_file_types: List[str] = Field(
        default=["pdf", "doc", "docx", "txt", "html", "json"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Monitoring
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    celery_task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    celery_result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    celery_accept_content: List[str] = Field(default=["json"], env="CELERY_ACCEPT_CONTENT")
    celery_timezone: str = Field(default="UTC", env="CELERY_TIMEZONE")
    celery_enable_utc: bool = Field(default=True, env="CELERY_ENABLE_UTC")
    
    # Security
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="CORS_ORIGINS"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    password_min_length: int = Field(default=8, env="PASSWORD_MIN_LENGTH")
    
    # Development
    reload: bool = Field(default=True, env="RELOAD")
    workers: int = Field(default=1, env="WORKERS")
    
    @validator("allowed_hosts", "cors_origins", "allowed_file_types", "celery_accept_content", pre=True)
    def parse_list_fields(cls, v):
        """Parse string lists from environment variables."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v
    
    @validator("max_file_size")
    def validate_max_file_size(cls, v):
        """Validate and convert file size string to bytes."""
        if isinstance(v, str):
            v = v.upper()
            if v.endswith("MB"):
                return int(v[:-2]) * 1024 * 1024
            elif v.endswith("KB"):
                return int(v[:-2]) * 1024
            elif v.endswith("B"):
                return int(v[:-1])
            else:
                return int(v)
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
