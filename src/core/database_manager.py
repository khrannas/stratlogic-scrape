"""
Enhanced database manager for StratLogic Scraping System.

This module provides an enhanced database manager with connection pooling,
health checks, and transaction management.
"""

import time
from typing import Optional, Dict, Any, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError

from .config import settings
from .utils import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Enhanced database manager with connection pooling and monitoring."""
    
    def __init__(self):
        """Initialize database manager."""
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
        self._setup_event_listeners()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with connection pooling."""
        try:
            self.engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_timeout=30,
                echo=settings.debug,
                echo_pool=settings.debug,
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                expire_on_commit=False,
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def _setup_event_listeners(self):
        """Setup database event listeners for monitoring."""
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            logger.debug("Database connection established")
        
        @event.listens_for(self.engine, "disconnect")
        def receive_disconnect(dbapi_connection, connection_record):
            logger.debug("Database connection closed")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            logger.debug("Database connection checked out from pool")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            logger.debug("Database connection returned to pool")
    
    def get_session(self) -> Session:
        """
        Get a database session.
        
        Returns:
            Database session
        """
        return self.SessionLocal()
    
    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """
        Get database session as context manager.
        
        Yields:
            Database session
        """
        session = self.get_session()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive database health check.
        
        Returns:
            Dictionary with health check results
        """
        start_time = time.time()
        health_status = {
            "status": "unhealthy",
            "response_time": 0,
            "connection_pool": {},
            "database_info": {},
            "errors": []
        }
        
        try:
            # Test basic connectivity
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            
            # Get connection pool info
            pool = self.engine.pool
            health_status["connection_pool"] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
            
            # Get database info
            with self.engine.connect() as connection:
                # PostgreSQL version
                version_result = connection.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                health_status["database_info"]["version"] = version
                
                # Database size
                size_result = connection.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """))
                size = size_result.fetchone()[0]
                health_status["database_info"]["size"] = size
                
                # Active connections
                connections_result = connection.execute(text("""
                    SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
                """))
                active_connections = connections_result.fetchone()[0]
                health_status["database_info"]["active_connections"] = active_connections
            
            health_status["status"] = "healthy"
            health_status["response_time"] = time.time() - start_time
            
        except Exception as e:
            health_status["errors"].append(str(e))
            logger.error(f"Database health check failed: {e}")
        
        return health_status
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get database connection information.
        
        Returns:
            Dictionary with connection information
        """
        try:
            pool = self.engine.pool
            return {
                "url": settings.database_url.replace(settings.postgres_password, "***"),
                "pool_size": pool.size(),
                "max_overflow": pool._max_overflow,
                "pool_timeout": pool._timeout,
                "pool_recycle": pool._recycle,
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            return {}
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def execute_transaction(self, queries: list) -> bool:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.engine.begin() as connection:
                for query, params in queries:
                    connection.execute(text(query), params or {})
            return True
        except Exception as e:
            logger.error(f"Error executing transaction: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create database backup.
        
        Args:
            backup_path: Path to save backup
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            import os
            
            # Extract database connection info
            from urllib.parse import urlparse
            parsed_url = urlparse(settings.database_url)
            
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h", parsed_url.hostname,
                "-p", str(parsed_url.port or 5432),
                "-U", parsed_url.username,
                "-d", parsed_url.path[1:],  # Remove leading slash
                "-f", backup_path,
                "--verbose",
                "--no-password"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.postgres_password
            
            # Execute backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_path}")
                return True
            else:
                logger.error(f"Database backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import subprocess
            import os
            
            # Extract database connection info
            from urllib.parse import urlparse
            parsed_url = urlparse(settings.database_url)
            
            # Build psql command
            cmd = [
                "psql",
                "-h", parsed_url.hostname,
                "-p", str(parsed_url.port or 5432),
                "-U", parsed_url.username,
                "-d", parsed_url.path[1:],  # Remove leading slash
                "-f", backup_path,
                "--verbose",
                "--no-password"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = settings.postgres_password
            
            # Execute restore
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database restored from: {backup_path}")
                return True
            else:
                logger.error(f"Database restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False
    
    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session generator for FastAPI dependency injection.
    
    Yields:
        Database session
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def get_db_context():
    """Get database session context manager."""
    return db_manager.get_session_context()
