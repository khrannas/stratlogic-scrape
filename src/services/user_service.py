from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

from src.core.models.user import User
from src.core.security import verify_password, get_password_hash, create_access_token
from src.core.config import settings
from src.api.schemas.auth_schemas import UserRegister, UserLogin, Token
from src.api.schemas.user_schemas import UserCreate, UserInDB
from src.core.exceptions import AuthenticationError, UserAlreadyExistsError

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def create_user(self, user_data: UserRegister) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()

        if existing_user:
            raise UserAlreadyExistsError("User with this email or username already exists")

        # Create user
        user_create = UserCreate(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password=user_data.password
        )

        user = User(
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            password_hash=get_password_hash(user_create.password),
            role="user"  # Default role
        )

        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise UserAlreadyExistsError("User with this email or username already exists")

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def login_user(self, login_data: UserLogin) -> Token:
        """Login a user and return JWT token"""
        user = self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    def update_user_role(self, user_id: str, new_role: str) -> User:
        """Update user role (admin only)"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.role = new_role
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate_user(self, user_id: str) -> User:
        """Deactivate a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def activate_user(self, user_id: str) -> User:
        """Activate a user account"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        return user
