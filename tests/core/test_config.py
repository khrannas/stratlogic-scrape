from src.core.config import settings

def test_settings_load_defaults():
    """
    Test that the settings object loads default values correctly.
    """
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MINIO_ENDPOINT == "minio:9000"
    assert settings.MINIO_SECURE is False
    assert settings.REDIS_HOST == "redis"
    assert settings.POSTGRES_SERVER == "db"
    assert settings.SECRET_KEY == "your-super-secret-key"
