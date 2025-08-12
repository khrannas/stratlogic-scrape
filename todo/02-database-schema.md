# Task 02: Database Schema and Models

## Overview
Design and implement the database schema for storing metadata, user information, scraping jobs, and system configuration.

## Priority: High
## Estimated Time: 2-3 days
## Dependencies: Task 01 (Project Setup)

## Checklist

### 2.1 Database Design
- [x] Design user management tables
- [x] Design scraping job tables
- [x] Design artifact metadata tables
- [x] Design system configuration tables
- [x] Design audit logging tables
- [ ] Create database schema diagram

### 2.2 SQLAlchemy Models
- [x] Create User model
- [x] Create ScrapingJob model
- [x] Create Artifact model
- [x] Create Metadata model
- [x] Create SystemConfig model
- [x] Create AuditLog model
- [x] Set up model relationships

### 2.3 Database Migrations
- [x] Set up Alembic for migrations
- [x] Create initial migration
- [x] Set up migration scripts
- [ ] Test migration rollback
- [ ] Create seed data scripts

### 2.4 Database Operations
- [x] Create database connection manager
- [ ] Implement CRUD operations
- [x] Set up connection pooling
- [x] Implement transaction management
- [x] Add database health checks

## Subtasks

### Subtask 2.1.1: User Management Schema
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Subtask 2.1.2: Scraping Job Schema
```sql
-- Scraping jobs table
CREATE TABLE scraping_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'web', 'paper', 'government'
    keywords TEXT[] NOT NULL,
    expanded_keywords TEXT[],
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    progress INTEGER DEFAULT 0,
    total_items INTEGER DEFAULT 0,
    completed_items INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job configuration table
CREATE TABLE job_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Subtask 2.1.3: Artifact Metadata Schema
```sql
-- Artifacts table
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL, -- 'web_page', 'paper', 'government_doc', 'social_media'
    source_url TEXT,
    title VARCHAR(500),
    content_hash VARCHAR(64) NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    minio_path VARCHAR(500) NOT NULL,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metadata tags table
CREATE TABLE metadata_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID REFERENCES artifacts(id) ON DELETE CASCADE,
    tag_type VARCHAR(50) NOT NULL, -- 'type', 'keyword', 'user', 'privacy'
    tag_key VARCHAR(100) NOT NULL,
    tag_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content extraction table
CREATE TABLE content_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID REFERENCES artifacts(id) ON DELETE CASCADE,
    extraction_type VARCHAR(50) NOT NULL, -- 'text', 'metadata', 'links', 'images'
    extracted_data JSONB,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Subtask 2.1.4: System Configuration Schema
```sql
-- System configuration table
CREATE TABLE system_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    config_type VARCHAR(20) DEFAULT 'string', -- 'string', 'integer', 'boolean', 'json'
    description TEXT,
    is_sensitive BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API rate limits table
CREATE TABLE api_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(100) NOT NULL,
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Subtask 2.1.5: Audit Logging Schema
```sql
-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Files to Create

1. `src/core/models/__init__.py` - Models package
2. `src/core/models/user.py` - User-related models
3. `src/core/models/job.py` - Scraping job models
4. `src/core/models/artifact.py` - Artifact models
5. `src/core/models/metadata.py` - Metadata models
6. `src/core/models/system.py` - System configuration models
7. `src/core/models/audit.py` - Audit logging models
8. `src/core/database.py` - Database connection and session management
9. `alembic.ini` - Alembic configuration
10. `migrations/env.py` - Alembic environment
11. `migrations/versions/` - Migration files directory

## SQLAlchemy Models Implementation

### User Models
```python
# src/core/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    scraping_jobs = relationship("ScrapingJob", back_populates="user")
    artifacts = relationship("Artifact", back_populates="user")
```

### Job Models
```python
# src/core/models/job.py
from sqlalchemy import Column, String, Integer, DateTime, UUID, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    job_type = Column(String(50), nullable=False)
    keywords = Column(ARRAY(Text), nullable=False)
    expanded_keywords = Column(ARRAY(Text))
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="scraping_jobs")
    artifacts = relationship("Artifact", back_populates="job")
```

## Database Operations

### Connection Management
```python
# src/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
```

## Testing

### Unit Tests
- [ ] Test model creation and relationships
- [ ] Test database operations (CRUD)
- [ ] Test constraint validations
- [ ] Test foreign key relationships

### Integration Tests
- [ ] Test database migrations
- [ ] Test connection pooling
- [ ] Test transaction management
- [ ] Test concurrent access

## Documentation

- [ ] Create database schema documentation
- [ ] Document model relationships
- [ ] Create migration guide
- [ ] Document database operations

## Risk Assessment and Mitigation

### High Risk Items

#### 1. Data Security and Privacy
**Risk**: Sensitive user data and scraping results could be exposed or compromised.

**Mitigation Strategies**:
- **Data Encryption**: Implement encryption at rest for sensitive data
- **Access Control**: Implement row-level security and role-based access
- **Audit Logging**: Comprehensive audit trail for all data access and modifications
- **Data Masking**: Mask sensitive data in logs and non-production environments
- **Backup Encryption**: Encrypt database backups
- **Connection Security**: Use SSL/TLS for database connections
- **Input Validation**: Strict validation of all data inputs to prevent injection attacks

#### 2. Scalability and Performance
**Risk**: Database performance could degrade with large volumes of data and concurrent users.

**Mitigation Strategies**:
- **Connection Pooling**: Implement proper connection pooling with monitoring
- **Indexing Strategy**: Create appropriate indexes for query performance
- **Query Optimization**: Monitor and optimize slow queries
- **Partitioning**: Implement table partitioning for large datasets
- **Read Replicas**: Set up read replicas for read-heavy workloads
- **Caching Layer**: Implement application-level caching for frequently accessed data
- **Database Sharding**: Plan for horizontal scaling with sharding

### Medium Risk Items

#### 1. Data Integrity
**Risk**: Data corruption or inconsistencies could occur due to concurrent access or system failures.

**Mitigation Strategies**:
- **Transaction Management**: Proper ACID compliance and transaction handling
- **Constraint Validation**: Implement comprehensive database constraints
- **Data Validation**: Application-level data validation before database operations
- **Consistency Checks**: Regular data consistency validation
- **Backup and Recovery**: Automated backup and recovery procedures
- **Migration Safety**: Safe database migration procedures with rollback capability

#### 2. Schema Evolution
**Risk**: Database schema changes could cause application failures or data loss.

**Mitigation Strategies**:
- **Migration Strategy**: Comprehensive migration planning and testing
- **Backward Compatibility**: Maintain backward compatibility during migrations
- **Rollback Procedures**: Automated rollback procedures for failed migrations
- **Schema Versioning**: Proper schema versioning and documentation
- **Testing**: Thorough testing of schema changes in staging environment
- **Gradual Deployment**: Implement gradual deployment for schema changes

## Notes

- Use UUIDs for primary keys for better security
- Implement soft deletes where appropriate
- Add proper indexes for performance
- Use JSONB for flexible metadata storage
- Implement proper foreign key constraints
- Add audit logging for sensitive operations
- Implement comprehensive data backup and recovery procedures
- Set up database monitoring and alerting
- Use connection pooling for optimal performance
- Implement proper error handling and logging

## Next Steps

After completing this task, proceed to:
- Task 03: MinIO Storage Integration
- Task 04: Basic API Endpoints
- Task 05: User Authentication System

## Completion Criteria

- [ ] Database schema is designed and documented
- [ ] All SQLAlchemy models are implemented
- [ ] Database migrations are working
- [ ] CRUD operations are implemented
- [ ] Database health checks are working
- [ ] All tests are passing
- [ ] Documentation is complete
