# StratLogic Scraping System - AI Agents Guide

## System Overview

The StratLogic Scraping System is a sophisticated multi-tenant web scraping platform designed to collect, process, and store data from multiple sources. The system follows a microservices architecture with clear separation of concerns and comprehensive data management.

## Architecture Components

### 1. Core Infrastructure Layer

#### Database Management (`src/core/`)
- **Models** (`models.py`): SQLAlchemy ORM models with UUID primary keys and timestamp tracking
- **Database** (`database.py`): Async database session management and connection pooling
- **Repositories** (`repositories/`): Data access layer following repository pattern
- **Config** (`config.py`): Centralized configuration management

**Key Models:**
- `User`: Multi-tenant user management with role-based access
- `ScrapingJob`: Job tracking with status, progress, and configuration
- `Artifact`: Scraped content storage with metadata and MinIO references
- `MetadataTag`: Flexible tagging system for content categorization
- `AuditLog`: Comprehensive activity logging for security and compliance

#### Storage System (`src/storage/`)
- **MinIO Client** (`minio_client.py`): Object storage for artifacts (PDFs, images, documents)
- **Artifact Storage** (`artifact_storage.py`): High-level storage operations
- **Metadata Manager** (`metadata_manager.py`): Metadata indexing and search

### 2. Scraping Modules

#### Web Scraper (`src/scrapers/web_scraper/`)
- **Playwright Integration**: Browser automation for dynamic content
- **Search Engine APIs**: Google, Bing, DuckDuckGo integration
- **Content Extraction**: HTML parsing and text processing
- **Rate Limiting**: Intelligent request throttling and proxy rotation

#### Paper Scraper (`src/scrapers/paper_scraper/`)
- **arXiv API**: Academic paper discovery (MIT licensed)
- **Grobid Integration**: PDF processing and metadata extraction
- **CrossRef API**: Additional academic source integration
- **Semantic Scholar**: Paper recommendations and citations

#### Government Scraper (`src/scrapers/government_scraper/`)
- **Indonesian Government APIs**: Official document repositories
- **Document Processing**: PDF and document format handling
- **Content Classification**: Government document categorization
- **Compliance Tracking**: Legal and regulatory compliance

### 3. API Layer (`src/api/`)

#### Authentication & Authorization
- **JWT Tokens**: Secure session management with expiration
- **Role-Based Access**: ADMIN, USER, VIEWER, MODERATOR roles
- **API Keys**: Programmatic access with permission scoping
- **Rate Limiting**: Per-user API request throttling

#### RESTful Endpoints
- **User Management**: Registration, authentication, profile management
- **Job Management**: Create, monitor, and control scraping jobs
- **Artifact Access**: Search, retrieve, and manage scraped content
- **System Administration**: Configuration and monitoring endpoints

### 4. Services Layer (`src/services/`)

#### Business Logic Services
- **Scraping Orchestration**: Job scheduling and execution coordination
- **LLM Integration**: OpenRouter/Gemini for keyword expansion and content analysis
- **Content Processing**: Text extraction, summarization, and enrichment
- **Notification System**: Real-time job status and system alerts

#### External Integrations
- **Email Service**: User notifications and system alerts
- **Monitoring Service**: Health checks and performance metrics
- **Analytics Service**: Usage tracking and data insights

## Data Flow Architecture

### 1. Job Creation Flow
```
User Request → API Validation → Job Creation → Keyword Expansion → Scraper Selection → Background Execution
```

### 2. Content Processing Flow
```
Raw Content → Content Extraction → Metadata Generation → Storage → Indexing → Search Availability
```

### 3. User Access Flow
```
Authentication → Authorization → Content Retrieval → Rate Limiting → Audit Logging → Response
```

## AI Agent Interaction Patterns

### 1. Understanding the Data Model

When working with this system, AI agents should understand:

#### User Isolation
- All data is scoped to specific users
- Jobs and artifacts belong to users
- Access control is enforced at the API level
- Audit logs track user actions

#### Job Lifecycle
- Jobs progress through: PENDING → RUNNING → COMPLETED/FAILED
- Progress tracking (0-100%) with detailed metrics
- Configuration stored as JSON for flexibility
- Error handling with detailed error messages

#### Artifact Management
- Content stored in MinIO with PostgreSQL metadata
- Multiple artifact types: web_page, pdf, document, image, video, audio
- Rich metadata including keywords, tags, language detection
- Content hashing for duplicate detection

### 2. Common Development Tasks

#### Adding New Scrapers
1. **Create Scraper Module**: Follow existing pattern in `src/scrapers/`
2. **Implement Interface**: Standard scraper interface with async methods
3. **Add Configuration**: Update configuration files and environment variables
4. **Create Tests**: Unit and integration tests for scraper functionality
5. **Update API**: Add endpoints for new scraper type
6. **Documentation**: Update API docs and user guides

#### Database Schema Changes
1. **Model Updates**: Modify SQLAlchemy models in `src/core/models.py`
2. **Migration Creation**: Use Alembic to generate migration scripts
3. **Repository Updates**: Update data access layer if needed
4. **API Updates**: Modify Pydantic models and endpoints
5. **Testing**: Update tests to reflect schema changes

#### API Endpoint Development
1. **Pydantic Models**: Define request/response models with validation
2. **Dependency Injection**: Use FastAPI dependencies for services
3. **Authentication**: Implement proper user authentication
4. **Authorization**: Check user permissions and role access
5. **Error Handling**: Use consistent error response format
6. **Testing**: Create comprehensive API tests

### 3. Configuration Management

#### Environment Variables
- Database connections and credentials
- MinIO endpoint and access keys
- Redis connection details
- External API keys (OpenRouter, Gemini, etc.)
- Security settings and JWT secrets

#### System Configuration
- Scraper-specific settings
- Rate limiting parameters
- Storage quotas and policies
- Feature flags and toggles

### 4. Testing Strategies

#### Unit Testing
- Individual component testing
- Mock external dependencies
- Test edge cases and error conditions
- Maintain high test coverage

#### Integration Testing
- Database operations with test data
- Storage operations with test buckets
- API endpoint testing with authentication
- Scraper testing with mock responses

#### End-to-End Testing
- Complete user workflows
- Job creation and execution
- Content retrieval and search
- Performance and load testing

## Development Workflow for AI Agents

### 1. Task Planning
- Check `todo/00-master-todo.md` for current priorities
- Understand task dependencies and requirements
- Review existing code patterns and conventions
- Plan implementation approach

### 2. Implementation
- Follow established code patterns and conventions
- Use proper error handling and logging
- Implement comprehensive testing
- Update documentation as needed

### 3. Quality Assurance
- Run all tests before completing tasks
- Check code quality with linting tools
- Verify API documentation generation
- Test in development environment

### 4. Progress Tracking
- Update todo files after completing tasks
- Document progress in `todo/progress/`
- Update relevant documentation
- Commit changes with descriptive messages

## Common Patterns and Conventions

### 1. Repository Pattern
```python
class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, id: UUID) -> Optional[Model]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
```

### 2. Service Layer Pattern
```python
class ScrapingService:
    def __init__(self, db: AsyncSession, storage: MinIOClient):
        self.db = db
        self.storage = storage
    
    async def create_job(self, user_id: UUID, job_data: JobCreate) -> ScrapingJob:
        # Business logic implementation
        pass
```

### 3. API Endpoint Pattern
```python
@router.post("/jobs/", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    scraping_service: ScrapingService = Depends(get_scraping_service)
) -> JobResponse:
    # Endpoint implementation
    pass
```

### 4. Error Handling Pattern
```python
try:
    result = await operation()
    return result
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

## Security Considerations

### 1. Authentication
- JWT tokens with proper expiration
- Secure password hashing
- Session management
- API key authentication

### 2. Authorization
- Role-based access control
- Resource-level permissions
- User data isolation
- Audit logging

### 3. Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting

## Performance Optimization

### 1. Database Optimization
- Connection pooling
- Query optimization
- Indexing strategies
- Caching layers

### 2. Storage Optimization
- Efficient MinIO operations
- Metadata caching
- Content compression
- CDN integration

### 3. API Optimization
- Response caching
- Pagination
- Async processing
- Background tasks

## Monitoring and Observability

### 1. Health Checks
- Database connectivity
- Storage availability
- External API status
- System metrics

### 2. Logging
- Structured logging
- Error tracking
- Performance monitoring
- Audit trails

### 3. Metrics
- API response times
- Scraping success rates
- Storage usage
- User activity

## Deployment and Operations

### 1. Docker Configuration
- Multi-stage builds
- Health checks
- Environment configuration
- Volume management

### 2. Environment Management
- Development setup
- Staging environment
- Production deployment
- Configuration management

### 3. Backup and Recovery
- Database backups
- Storage backups
- Configuration backups
- Disaster recovery procedures

## Best Practices for AI Agents

### 1. Code Quality
- Follow PEP 8 and project conventions
- Use type hints consistently
- Write comprehensive docstrings
- Implement proper error handling

### 2. Testing
- Write unit tests for new features
- Maintain test coverage
- Use fixtures for test data
- Test edge cases and error conditions

### 3. Documentation
- Update README.md with new features
- Document API changes
- Keep configuration docs current
- Write clear commit messages

### 4. Security
- Validate all user inputs
- Implement proper authentication
- Follow security best practices
- Log security events

### 5. Performance
- Use async operations where appropriate
- Implement caching strategies
- Optimize database queries
- Monitor performance metrics

## Troubleshooting Guide

### 1. Common Issues
- Database connection problems
- Storage access issues
- Authentication failures
- Rate limiting errors

### 2. Debugging Tools
- Log analysis
- Database query inspection
- API endpoint testing
- Performance profiling

### 3. Recovery Procedures
- Service restart procedures
- Database recovery
- Storage recovery
- Configuration restoration

This guide provides AI agents with comprehensive understanding of the StratLogic Scraping System architecture, enabling effective development and maintenance of this sophisticated multi-tenant web scraping platform.
