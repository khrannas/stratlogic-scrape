# Development Setup Guide

This guide will help you set up the StratLogic Scraping System for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Git** - [Install Git](https://git-scm.com/downloads)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/stratlogic/stratlogic-scrape.git
cd stratlogic-scrape
```

### 2. Set Up Environment

```bash
# Copy environment template
cp env.example .env

# Edit the .env file with your configuration
# At minimum, update the SECRET_KEY
```

### 3. Start Development Environment

```bash
# Make the startup script executable
chmod +x scripts/start.sh

# Run the startup script
./scripts/start.sh
```

The startup script will:
- Start Docker services (PostgreSQL, Redis, MinIO)
- Create Python virtual environment
- Install dependencies
- Set up database tables
- Start the FastAPI application

### 4. Access the Application

Once started, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MinIO Console**: http://localhost:9001 (admin/admin123)

## Manual Setup

If you prefer to set up manually:

### 1. Start Services

```bash
# Start only the required services
docker-compose up -d postgres redis minio

# Wait for services to be ready
docker-compose ps
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install --with-deps chromium
```

### 3. Set Up Database

```bash
# Create database tables
python -c "
from src.core.database import create_tables
create_tables()
print('Database tables created successfully!')
"
```

### 4. Start Application

```bash
# Start FastAPI application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m database

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_config.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Database Operations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Celery Tasks

```bash
# Start Celery worker
celery -A src.core.celery_app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A src.core.celery_app beat --loglevel=info

# Monitor Celery tasks
celery -A src.core.celery_app flower
```

## Project Structure

```
stratlogic-scrape/
├── src/                    # Source code
│   ├── core/              # Core functionality
│   │   ├── config.py      # Configuration management
│   │   ├── database.py    # Database connection
│   │   ├── models.py      # Database models
│   │   └── utils.py       # Utility functions
│   ├── api/               # API endpoints
│   ├── scrapers/          # Scraping modules
│   ├── storage/           # Storage operations
│   ├── services/          # Business logic
│   └── main.py            # FastAPI application
├── tests/                 # Test suite
├── config/                # Configuration files
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── docker-compose.yml     # Service orchestration
├── Dockerfile            # Application container
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Project configuration
```

## Configuration

### Environment Variables

Key environment variables to configure:

```bash
# Application
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
POSTGRES_PASSWORD=your-password

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123

# API Keys
OPENAI_API_KEY=your-openai-key
OPENROUTER_API_KEY=your-openrouter-key
```

### Development vs Production

The application automatically detects the environment:

- **Development**: Debug mode, detailed logging, auto-reload
- **Production**: Optimized settings, minimal logging, security headers

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart service
docker-compose restart postgres
```

#### 2. MinIO Connection Failed

```bash
# Check if MinIO is running
docker-compose ps minio

# Check logs
docker-compose logs minio

# Access MinIO console
# http://localhost:9001 (admin/admin123)
```

#### 3. Redis Connection Failed

```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

#### 4. Port Already in Use

```bash
# Check what's using the port
lsof -i :8000

# Kill the process or change port in .env
```

#### 5. Permission Denied

```bash
# Fix script permissions
chmod +x scripts/*.sh

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

### Logs

View application logs:

```bash
# Docker logs
docker-compose logs -f app

# Application logs (if running locally)
tail -f logs/app.log
```

## Contributing

### Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting
- Use isort for import sorting
- Add type hints to all functions
- Write docstrings for all public functions

### Testing

- Write tests for all new functionality
- Maintain test coverage above 80%
- Use appropriate test markers
- Mock external dependencies

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create pull request
git push origin feature/your-feature
```

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Check the [Issues](https://github.com/stratlogic/stratlogic-scrape/issues) page
4. Create a new issue with detailed information

## Next Steps

After setting up the development environment:

1. Review the [API Documentation](http://localhost:8000/docs)
2. Explore the test suite in `tests/`
3. Check out the [Architecture Guide](ARCHITECTURE.md)
4. Read the [Contributing Guidelines](CONTRIBUTING.md)
