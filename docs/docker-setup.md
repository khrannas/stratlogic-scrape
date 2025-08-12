# Docker Setup Guide

## Overview
This guide explains the Docker setup for the StratLogic Scraping System, which uses multiple docker-compose files for different environments and purposes.

## Docker Compose Files

### 1. `docker-compose.yml` - Infrastructure Services
Contains the core infrastructure services:
- **PostgreSQL** - Database
- **Redis** - Caching and session storage
- **MinIO** - Object storage

### 2. `docker-compose.application.yml` - Main Application
Contains the main FastAPI application service.

### 3. `docker-compose.override.yml` - Development Overrides
Automatically loaded in development with additional configurations:
- Hot reload for the application
- Debug mode enabled
- Additional volume mounts
- Development-specific environment variables

### 4. `docker-compose.prod.yml` - Production Configuration
Production-optimized settings:
- Multi-worker configuration
- Resource limits
- Production environment variables
- Health checks

## Usage Scenarios

### Development Environment

#### Start Infrastructure Only
```bash
# Start only infrastructure services (database, Redis, MinIO)
docker-compose up -d

# Check status
docker-compose ps
```

#### Start Full Development Stack
```bash
# Start everything (infrastructure + application with development overrides)
docker-compose up -d

# View logs
docker-compose logs -f app
```

#### Run Application Locally with Docker Infrastructure
```bash
# Start infrastructure
docker-compose up -d

# Run application locally (for debugging)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Environment

#### Start Production Stack
```bash
# Start production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

#### Start Application Only (with existing infrastructure)
```bash
# Start only the application service
docker-compose -f docker-compose.application.yml up -d
```

## Service Details

### Infrastructure Services

#### PostgreSQL Database
- **Port**: 5432
- **Database**: stratlogic
- **User**: user
- **Password**: password
- **Volume**: postgres_data
- **Initialization**: scripts/init-db.sql

#### Redis Cache
- **Port**: 6379
- **Volume**: redis_data
- **Features**: AOF persistence enabled

#### MinIO Object Storage
- **API Port**: 9000
- **Console Port**: 9001
- **User**: minioadmin
- **Password**: minioadmin
- **Volume**: minio_data
- **Initialization**: scripts/minio-init.sh

### Application Service

#### Development Mode
- **Port**: 8000
- **Hot Reload**: Enabled
- **Debug**: Enabled
- **Volumes**: src/, logs/, tests/, docs/

#### Production Mode
- **Port**: 8000
- **Workers**: 4
- **Debug**: Disabled
- **Health Check**: Enabled
- **Resource Limits**: CPU and memory constraints

## Environment Variables

### Core Configuration
```bash
# Database
DATABASE_URL=postgresql://user:password@db:5432/stratlogic
POSTGRES_SERVER=db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=stratlogic
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# Application
SECRET_KEY=your-super-secret-key-change-this-in-production
API_V1_STR=/api/v1
DEBUG=true
LOG_LEVEL=INFO
```

## Network Configuration

All services are connected through the `stratlogic-network` bridge network, allowing them to communicate using service names as hostnames.

## Volumes

### Persistent Data
- `postgres_data` - PostgreSQL database files
- `redis_data` - Redis AOF files
- `minio_data` - MinIO object storage

### Development Volumes
- `./src` - Application source code
- `./logs` - Application logs
- `./tests` - Test files
- `./docs` - Documentation

## Health Checks

The application service includes health checks that verify the API is responding:
```bash
# Manual health check
curl -f http://localhost:8000/
```

## Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using a port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # macOS/Linux

# Use different ports
docker-compose up -d --scale app=0
docker-compose -f docker-compose.application.yml up -d -p 8001
```

#### Service Not Starting
```bash
# Check logs
docker-compose logs service_name

# Restart service
docker-compose restart service_name

# Rebuild and restart
docker-compose up -d --build service_name
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec db psql -U user -d stratlogic -c "SELECT 1;"

# Reset database
docker-compose down -v
docker-compose up -d db
```

#### MinIO Connection Issues
```bash
# Check MinIO status
docker-compose exec minio mc admin info

# Access MinIO console
# http://localhost:9001
# Username: minioadmin
# Password: minioadmin
```

### Debug Commands

#### View All Logs
```bash
docker-compose logs -f
```

#### Execute Commands in Containers
```bash
# Database
docker-compose exec db psql -U user -d stratlogic

# Redis
docker-compose exec redis redis-cli

# MinIO
docker-compose exec minio mc ls myminio/

# Application
docker-compose exec app python -c "import src.core.config; print('Config loaded')"
```

#### Check Resource Usage
```bash
docker stats
```

## Backup and Recovery

### Database Backup
```bash
# Create backup
docker-compose exec db pg_dump -U user stratlogic > backup.sql

# Restore backup
docker-compose exec -T db psql -U user -d stratlogic < backup.sql
```

### MinIO Backup
```bash
# Backup all data
docker-compose exec minio mc mirror myminio/ /backup/

# Restore data
docker-compose exec minio mc mirror /backup/ myminio/
```

## Performance Optimization

### Production Settings
- Use `docker-compose.prod.yml` for production
- Set appropriate resource limits
- Enable Redis persistence
- Configure MinIO lifecycle policies
- Use multiple application workers

### Development Settings
- Use `docker-compose.override.yml` for development
- Enable hot reload
- Mount source code volumes
- Enable debug mode

## Security Considerations

### Production Security
- Change default passwords
- Use environment variables for secrets
- Enable SSL/TLS
- Restrict network access
- Regular security updates

### Development Security
- Use separate development credentials
- Don't expose production data
- Use local development certificates

## Next Steps

1. **Start Development**: `docker-compose up -d`
2. **Access Services**:
   - API: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001
   - Database: localhost:5432
3. **Monitor Logs**: `docker-compose logs -f`
4. **Scale for Production**: Use production compose files
