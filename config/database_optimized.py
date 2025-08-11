"""
Optimized database configuration module.

This module provides enhanced database configuration with performance optimizations,
connection pooling improvements, and query monitoring capabilities.
"""

from sqlalchemy import create_engine, pool, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import time
import logging

from ..src.core.config import settings

logger = logging.getLogger(__name__)


def create_optimized_database_engine():
    """Create database engine with performance optimizations."""
    return create_engine(
        settings.database_url,
        poolclass=QueuePool,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
        echo=settings.debug,
        pool_size=20,  # Increased pool size
        max_overflow=30,  # Increased max overflow
        pool_timeout=60,  # Increased timeout
        pool_reset_on_return='commit',  # Reset on return
        connect_args={
            "connect_timeout": 10,
            "application_name": "stratlogic_scraper"
        }
    )


def create_optimized_session_factory(engine):
    """Create optimized session factory for database operations."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )


@contextmanager
def get_optimized_database_session():
    """Get optimized database session as context manager."""
    engine = create_optimized_database_engine()
    SessionLocal = create_optimized_session_factory(engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def setup_query_monitoring(engine):
    """Setup query monitoring and performance tracking."""
    
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query start time."""
        context._query_start_time = time.time()
    
    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Record query execution time and log slow queries."""
        total_time = time.time() - context._query_start_time
        
        # Log slow queries
        if total_time > 1.0:  # Log queries taking more than 1 second
            logger.warning(f"Slow query detected: {total_time:.3f}s - {statement[:200]}...")
        
        # Log very slow queries
        if total_time > 5.0:  # Log queries taking more than 5 seconds
            logger.error(f"Very slow query detected: {total_time:.3f}s - {statement[:200]}...")


def check_optimized_database_health():
    """Check optimized database health and connectivity."""
    try:
        with get_optimized_database_session() as session:
            # Test basic connectivity
            session.execute("SELECT 1")
            
            # Test connection pool status
            engine = session.bind
            pool_status = {
                "pool_size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "invalid": engine.pool.invalid()
            }
            
            return {
                "status": "healthy",
                "pool_status": pool_status
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def get_optimized_database_info():
    """Get optimized database connection information."""
    return {
        "url": settings.database_url.replace(settings.postgres_password, "***"),
        "pool_size": 20,
        "max_overflow": 30,
        "pool_timeout": 60,
        "pool_recycle": 3600,
        "optimizations": [
            "Enhanced connection pooling",
            "Query monitoring",
            "Slow query logging",
            "Connection recycling",
            "Application name tracking"
        ]
    }


def create_database_indexes():
    """Create performance-optimized database indexes."""
    indexes = [
        # Users table indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role ON users(role)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at)",
        
        # Scraping jobs table indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_user_id ON scraping_jobs(user_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_status ON scraping_jobs(status)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_created_at ON scraping_jobs(created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_completed_at ON scraping_jobs(completed_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_jobs_user_status ON scraping_jobs(user_id, status)",
        
        # Artifacts table indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_user_id ON artifacts(user_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_job_id ON artifacts(job_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_created_at ON artifacts(created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_artifacts_user_type ON artifacts(user_id, artifact_type)",
        
        # Performance metrics table indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_type ON performance_metrics(metric_type)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_user_id ON performance_metrics(user_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_created_at ON performance_metrics(created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_processing_time ON performance_metrics(processing_time_ms)",
        
        # Search indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_search_artifact_id ON search_index(artifact_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_search_active ON search_index(is_active)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_search_embeddings_artifact ON search_embeddings(artifact_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_search_embeddings_model ON search_embeddings(model_name)",
        
        # Monitoring indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_service ON system_health(service_name)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_created_at ON system_health(created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_metrics_user_created ON scraping_metrics(user_id, created_at)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_activity_user_created ON user_activity(user_id, created_at)"
    ]
    
    return indexes


def get_database_performance_tips():
    """Get database performance optimization tips."""
    return {
        "connection_pooling": {
            "pool_size": "Set to 20 for optimal performance",
            "max_overflow": "Set to 30 for handling traffic spikes",
            "pool_recycle": "Recycle connections every hour to prevent stale connections",
            "pool_timeout": "60 seconds timeout for connection acquisition"
        },
        "indexing": {
            "primary_keys": "All tables use UUID primary keys",
            "foreign_keys": "Index all foreign key columns",
            "composite_indexes": "Create composite indexes for common query patterns",
            "full_text_search": "Use GIN indexes for full-text search"
        },
        "query_optimization": {
            "avoid_select_star": "Select only needed columns",
            "use_limit": "Always use LIMIT for large result sets",
            "avoid_n_plus_one": "Use eager loading for relationships",
            "use_explain": "Use EXPLAIN ANALYZE for query optimization"
        },
        "monitoring": {
            "slow_query_logging": "Queries > 1s are logged as warnings",
            "very_slow_logging": "Queries > 5s are logged as errors",
            "connection_pool_monitoring": "Track pool usage and overflow",
            "performance_metrics": "Record query execution times"
        }
    }
