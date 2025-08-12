from sqlalchemy.orm import Session
from src.core.models.user import User
from src.api.schemas.user_schemas import UserCreate
from src.core.security import get_password_hash

class UserService:
    def get_user_by_email(self, db: Session, *, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, db: Session, *, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def create_user(self, db: Session, *, user_in: UserCreate) -> User:
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            password_hash=hashed_password,
            full_name=user_in.full_name,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

user_service = UserService()
