# Development Setup Guide

## Overview
This guide will help you set up the StratLogic Scraping System for development.

## Prerequisites

### Required Software
- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Download Docker](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Node.js 18+** (for frontend development) - [Download Node.js](https://nodejs.org/)

### Recommended Tools
- **VS Code** with Python extension
- **Postman** or **Insomnia** for API testing
- **pgAdmin** or **DBeaver** for database management

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd stratlogic-scrape
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# See Configuration section below
```

### 3. Start Services with Docker
```bash
# Start all services (PostgreSQL, Redis, MinIO)
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Note**: The Docker setup is now separated into multiple files for better organization:
- `docker-compose.yml` - Infrastructure services only
- `docker-compose.application.yml` - Main application
- `docker-compose.override.yml` - Development overrides (auto-loaded)
- `docker-compose.prod.yml` - Production configuration

See [Docker Setup Guide](./docker-setup.md) for detailed usage instructions.

### 4. Python Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # if available
```

### 5. Database Setup
```bash
# Run database migrations
alembic upgrade head

# Optional: Seed with test data
python scripts/seed_data.py  # if available
```

### 6. Start the Application
```bash
# Start the FastAPI server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Verify Installation
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/
- MinIO Console: http://localhost:9001 (admin/admin)

## Configuration

### Environment Variables
Edit the `.env` file with your configuration:

```bash
# Core Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
API_V1_STR=/api/v1

# Database Configuration
POSTGRES_SERVER=db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=stratlogic
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# MinIO Storage Configuration
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# API Keys (Required for full functionality)
OPENROUTER_API_KEY=your-openrouter-api-key
GEMINI_API_KEY=your-gemini-api-key
ARXIV_API_KEY=your-arxiv-api-key
```

### API Keys Setup

#### OpenRouter API Key
1. Visit [OpenRouter](https://openrouter.ai/)
2. Create an account and get your API key
3. Add to `.env`: `OPENROUTER_API_KEY=your-key`

#### Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Add to `.env`: `GEMINI_API_KEY=your-key`

#### arXiv API Key
1. Visit [arXiv API](https://arxiv.org/help/api/user-manual)
2. Register for an API key (optional but recommended)
3. Add to `.env`: `ARXIV_API_KEY=your-key`

## Development Workflow

### Code Quality Tools
```bash
# Install pre-commit hooks
pre-commit install

# Run linting
flake8 src/
black src/
isort src/

# Run type checking
mypy src/
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_web_scraper.py
```

### Database Operations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history
```

### Docker Operations
```bash
# Rebuild containers
docker-compose build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Clean up volumes (WARNING: deletes data)
docker-compose down -v
```

## Project Structure

```
stratlogic-scrape/
├── src/                    # Main application code
│   ├── api/               # API routes and middleware
│   ├── auth/              # Authentication logic
│   ├── core/              # Core configuration and models
│   ├── scrapers/          # Scraping modules
│   ├── services/          # Business logic services
│   └── storage/           # Storage management
├── tests/                 # Test files
├── docs/                  # Documentation
├── migrations/            # Database migrations
├── docker-compose.yml     # Service orchestration
├── Dockerfile            # Application container
└── requirements.txt      # Python dependencies
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# Kill the process or use different port
uvicorn src.main:app --reload --port 8001
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart database service
docker-compose restart db

# Check database logs
docker-compose logs db
```

#### MinIO Connection Issues
```bash
# Check MinIO status
docker-compose ps minio

# Access MinIO console
# http://localhost:9001
# Username: admin
# Password: admin
```

#### Python Import Errors
```bash
# Ensure virtual environment is activated
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
# or add to .env: LOG_LEVEL=DEBUG

# Start with debug mode
uvicorn src.main:app --reload --log-level debug
```

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
- `GET /` - Health check
- `GET /api/v1/` - API root
- `GET /api/v1/users/` - User management
- `POST /api/v1/scrapers/web/` - Web scraping
- `POST /api/v1/scrapers/papers/` - Paper scraping

## Contributing

### Code Style
- Follow PEP 8 for Python code
- Use type hints
- Write docstrings for functions and classes
- Keep functions small and focused

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/your-feature-name

# Create pull request
```

### Testing Requirements
- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Maintain test coverage above 80%

## Support

### Getting Help
1. Check this documentation
2. Review existing issues on GitHub
3. Create a new issue with detailed information
4. Contact the development team

### Useful Commands
```bash
# Check system status
docker-compose ps
python -c "import src.core.config; print('Config loaded successfully')"

# View application logs
docker-compose logs -f app

# Access database
docker-compose exec db psql -U user -d stratlogic
```

## Next Steps

After completing the setup:
1. Review the [API Documentation](http://localhost:8000/docs)
2. Explore the [scraping modules](../src/scrapers/)
3. Check out the [testing guide](./testing.md)
4. Read the [deployment guide](./deployment.md)
