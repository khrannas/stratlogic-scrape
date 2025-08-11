from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# In a real application, this would come from a config file or environment variables
DATABASE_URL = "postgresql://user:password@localhost:5432/stratlogic"

class DatabaseManager:
    def __init__(self, database_url: str = DATABASE_URL):
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

# Global instance of the database manager
db_manager = DatabaseManager()

def get_db():
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
