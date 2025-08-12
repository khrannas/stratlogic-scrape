from pydantic import PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings
from typing import Any

class Settings(BaseSettings):
    # Core
    SECRET_KEY: str = "your-super-secret-key"
    API_V1_STR: str = "/api/v1"

    # Database
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "stratlogic"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: PostgresDsn | None = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: str | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: RedisDsn | None = None

    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: str | None, values: dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False

    # LLM & Scraper APIs
    LLM_PROVIDER: str = "openai"  # "openai" or "gemini"
    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    ARXIV_API_KEY: str | None = None

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Development
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
