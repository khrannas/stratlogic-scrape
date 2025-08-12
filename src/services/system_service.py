from typing import Optional
from sqlalchemy.orm import Session

from src.core.models.system import SystemConfiguration
from src.api.schemas import system_schemas

class SystemService:
    def get_config(self, db: Session, *, key: str) -> Optional[SystemConfiguration]:
        return db.query(SystemConfiguration).filter(SystemConfiguration.config_key == key).first()

    def create_config(self, db: Session, *, config_in: system_schemas.SystemConfigurationCreate) -> SystemConfiguration:
        db_config = SystemConfiguration(**config_in.dict())
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return db_config

    def update_config(self, db: Session, *, db_obj: SystemConfiguration, obj_in: system_schemas.SystemConfigurationUpdate) -> SystemConfiguration:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

system_service = SystemService()
