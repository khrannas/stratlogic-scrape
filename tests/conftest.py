import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.core.config import settings
from src.core.models.base import Base
from src.core.models.user import User
from src.services import user_service
from src.api.schemas import user_schemas

# Use a separate test database URL, connecting via localhost
TEST_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}_test"

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables for the test database
Base.metadata.drop_all(bind=engine) # Drop existing tables first for a clean slate
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Creates a new database session for a test that is rolled back after the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def test_user(db_session: Session) -> User:
    """
    Create a user for use in tests.
    This user is created per test function and rolled back.
    """
    user_in = user_schemas.UserCreate(
        email="test@example.com",
        username="testuser",
        password="password"
    )
    return user_service.create_user(db=db_session, user_in=user_in)
