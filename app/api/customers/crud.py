
from uuid import UUID

from app.api.customers.models import Customer
from app.api.customers.schemas import CustomerSchema
from app.core.schema_operations import parse_schema
from sqlalchemy.orm import Session


def create_customer(db: Session,customer: CustomerSchema):
  db_customer = Customer(**parse_schema(customer))
  db.add(db_customer)
  db.commit()
  db.refresh(db_customer)
  return db_customer

def get_customer(db: Session, id: UUID):
  db_customer = db.query(Customer).get(id)
  return CustomerSchema.model_validate(db_customer)

def update_customer(db: Session, id: UUID, customer: CustomerSchema):
  db_customer = db.query(Customer).get(id)
  for key, value in parse_schema(customer).items():
    setattr(db_customer, key, value)
  db.commit()
  db.refresh(db_customer)
  return db_customer

def delete_customer(db: Session, id: UUID):
  db_customer = db.query(Customer).where(Customer.id == id).first()
  if db_customer is None:
    raise ValueError(f"Customer with id {id} does not exist")
  db_customer.soft_delete()
  db.commit()