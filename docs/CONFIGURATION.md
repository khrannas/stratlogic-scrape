# Configuration Guide

This guide explains all configuration options available in the StratLogic Scraping System.

## Environment Variables

The application uses environment variables for configuration. Copy `env.example` to `.env` and customize the values.

### Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Application environment (development, staging, production) |
| `DEBUG` | `true` | Enable debug mode |
| `SECRET_KEY` | **Required** | Secret key for JWT tokens and encryption |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of allowed hosts |

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | **Required** | PostgreSQL connection string |
| `POSTGRES_PASSWORD` | `stratlogic_password` | PostgreSQL password |

**Example DATABASE_URL:**
```
postgresql://username:password@host:port/database
```

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `REDIS_PASSWORD` | `None` | Redis password (if required) |

### MinIO Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO server endpoint |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | `minioadmin123` | MinIO secret key |
| `MINIO_USE_SSL` | `false` | Use SSL for MinIO connections |
| `MINIO_BUCKET_NAME` | `stratlogic-artifacts` | Default bucket name |

### API Keys

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `None` | OpenAI API key for LLM operations |
| `OPENROUTER_API_KEY` | `None` | OpenRouter API key for alternative LLM access |
| `GOOGLE_API_KEY` | `None` | Google API key for additional services |

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_LLM_PROVIDER` | `openai` | Default LLM provider (openai, openrouter) |
| `DEFAULT_MODEL` | `gpt-4` | Default model to use |
| `MAX_TOKENS` | `4000` | Maximum tokens for LLM responses |
| `TEMPERATURE` | `0.7` | Temperature for LLM responses (0.0-1.0) |

### Scraping Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPING_DELAY` | `1` | Delay between scraping requests (seconds) |
| `MAX_CONCURRENT_SCRAPERS` | `5` | Maximum concurrent scraping jobs |
| `REQUEST_TIMEOUT` | `30` | Request timeout (seconds) |
| `USER_AGENT` | Custom | User agent string for web requests |

### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_PER_MINUTE` | `60` | Requests per minute |
| `RATE_LIMIT_PER_HOUR` | `1000` | Requests per hour |

### File Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_SIZE` | `100MB` | Maximum file size for uploads |
| `ALLOWED_FILE_TYPES` | `pdf,doc,docx,txt,html,json` | Comma-separated list of allowed file types |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FORMAT` | `json` | Log format (json, text) |

### Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_ENABLED` | `true` | Enable Prometheus metrics |
| `METRICS_PORT` | `9090` | Port for metrics endpoint |

### Celery Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | Redis URL for Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | Redis URL for Celery results |
| `CELERY_TASK_SERIALIZER` | `json` | Task serialization format |
| `CELERY_RESULT_SERIALIZER` | `json` | Result serialization format |
| `CELERY_ACCEPT_CONTENT` | `json` | Accepted content types |
| `CELERY_TIMEZONE` | `UTC` | Celery timezone |
| `CELERY_ENABLE_UTC` | `true` | Enable UTC for Celery |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed CORS origins |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRATION_HOURS` | `24` | JWT token expiration time |
| `PASSWORD_MIN_LENGTH` | `8` | Minimum password length |

### Development

| Variable | Default | Description |
|----------|---------|-------------|
| `RELOAD` | `true` | Enable auto-reload for development |
| `WORKERS` | `1` | Number of worker processes |

## Configuration Files

### pyproject.toml

The `pyproject.toml` file contains project metadata and tool configurations:

- **Build system**: setuptools
- **Dependencies**: All required packages
- **Development tools**: Black, isort, mypy, pytest
- **Code quality**: Bandit, safety

### pytest.ini

Test configuration:

- **Test paths**: `tests/`
- **Markers**: unit, integration, e2e, database, minio, redis
- **Options**: Verbose output, color, warnings

## Environment-Specific Configuration

### Development

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
RELOAD=true
```

### Production

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
RELOAD=false
```

### Staging

```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
RELOAD=false
```

## Docker Configuration

### docker-compose.yml

The Docker Compose file defines all services:

- **postgres**: PostgreSQL database
- **redis**: Redis cache and message broker
- **minio**: MinIO object storage
- **app**: Main application
- **celery-worker**: Background task worker
- **celery-beat**: Task scheduler

### Environment Variables in Docker

Docker Compose uses environment variables from `.env` file:

```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}
  - REDIS_URL=${REDIS_URL}
  - MINIO_ENDPOINT=${MINIO_ENDPOINT}
```

## Configuration Validation

The application validates configuration on startup:

1. **Required fields**: SECRET_KEY, DATABASE_URL
2. **Type validation**: All values are validated against expected types
3. **Format validation**: URLs, file sizes, etc.
4. **Connection testing**: Database, Redis, MinIO connectivity

## Security Considerations

### Sensitive Data

Never commit sensitive data to version control:

- API keys
- Passwords
- Secret keys
- Database credentials

### Environment Separation

Use different configurations for different environments:

- Development: Local services, debug mode
- Staging: Production-like setup
- Production: Optimized, secure settings

### Access Control

Configure proper access controls:

- Database user permissions
- MinIO bucket policies
- Redis authentication
- API rate limiting

## Troubleshooting Configuration

### Common Issues

1. **Missing SECRET_KEY**: Application won't start
2. **Invalid DATABASE_URL**: Database connection fails
3. **Wrong MinIO credentials**: Storage operations fail
4. **Redis connection issues**: Background tasks fail

### Debug Configuration

Enable debug mode to see configuration issues:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### Configuration Testing

Test configuration loading:

```python
from src.core.config import settings
print(f"Environment: {settings.environment}")
print(f"Database URL: {settings.database_url}")
```

## Best Practices

1. **Use environment variables** for all configuration
2. **Validate configuration** on startup
3. **Separate environments** with different configs
4. **Use secure defaults** for production
5. **Document all options** clearly
6. **Test configuration** in CI/CD
7. **Monitor configuration** changes
8. **Backup configuration** securely
