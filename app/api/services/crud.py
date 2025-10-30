
from uuid import UUID

from app.api.services.models import Service
from app.api.services.schemas import ServiceSchema
from app.core.schema_operations import parse_schema
from sqlalchemy.orm import Session


def create_service(db: Session,service: ServiceSchema):
  db_service = Service(**parse_schema(service))
  db.add(db_service)
  db.commit()
  db.refresh(db_service)
  return db_service

def get_service(db: Session, id: UUID):
  db_service = db.query(Service).get(id)
  return ServiceSchema.model_validate(db_service)

def update_service(db: Session, id: UUID, service: ServiceSchema):
  db_service = db.query(Service).get(id)
  for key, value in parse_schema(service).items():
    setattr(db_service, key, value)
  db.commit()
  db.refresh(db_service)
  return db_service

def delete_service(db: Session, id: UUID):
  db_service = db.query(Service).where(Service.id == id).first()
  if db_service is None:
    raise ValueError(f"Service with id {id} does not exist")
  db_service.soft_delete()
  db.commit()