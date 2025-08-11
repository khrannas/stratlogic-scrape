"""
Base repository class for database operations.

This module provides a base repository class with common CRUD operations
that can be extended by specific repository classes.
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel

from ..database import Base
from ..utils import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with model.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Model instance or None
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} with id {id}: {e}")
            return None
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of filters to apply
            
        Returns:
            List of model instances
        """
        try:
            query = db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, key).in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__}: {e}")
            return []
    
    def create(self, db: Session, obj_in: CreateSchemaType) -> Optional[ModelType]:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic model with creation data
            
        Returns:
            Created model instance or None
        """
        try:
            obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            return None
    
    def update(
        self, 
        db: Session, 
        db_obj: ModelType, 
        obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        """
        Update an existing record.
        
        Args:
            db: Database session
            db_obj: Existing model instance
            obj_in: Pydantic model with update data
            
        Returns:
            Updated model instance or None
        """
        try:
            obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
            
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            return None
    
    def delete(self, db: Session, id: Any) -> bool:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            obj = db.query(self.model).get(id)
            if obj:
                db.delete(obj)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {e}")
            return False
    
    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.
        
        Args:
            db: Database session
            filters: Dictionary of filters to apply
            
        Returns:
            Number of records
        """
        try:
            query = db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, key).in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)
            
            return query.count()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0
    
    def exists(self, db: Session, id: Any) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            True if record exists, False otherwise
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first() is not None
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} with id {id}: {e}")
            return False
    
    def get_by_field(
        self, 
        db: Session, 
        field: str, 
        value: Any
    ) -> Optional[ModelType]:
        """
        Get a record by a specific field value.
        
        Args:
            db: Database session
            field: Field name
            value: Field value
            
        Returns:
            Model instance or None
        """
        try:
            if hasattr(self.model, field):
                return db.query(self.model).filter(
                    getattr(self.model, field) == value
                ).first()
            return None
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by {field}={value}: {e}")
            return None
    
    def get_multi_by_field(
        self, 
        db: Session, 
        field: str, 
        value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records by a specific field value.
        
        Args:
            db: Database session
            field: Field name
            value: Field value
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of model instances
        """
        try:
            if hasattr(self.model, field):
                return db.query(self.model).filter(
                    getattr(self.model, field) == value
                ).offset(skip).limit(limit).all()
            return []
        except Exception as e:
            logger.error(f"Error getting multiple {self.model.__name__} by {field}={value}: {e}")
            return []
