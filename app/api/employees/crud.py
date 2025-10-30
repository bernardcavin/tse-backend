
from uuid import UUID

from app.api.employees.models import Employee
from app.api.employees.schemas import EmployeeSchema
from app.core.schema_operations import parse_schema
from sqlalchemy.orm import Session


def create_employee(db: Session,employee: EmployeeSchema):
  db_employee = Employee(**parse_schema(employee))
  db.add(db_employee)
  db.commit()
  db.refresh(db_employee)
  return db_employee

def get_employee(db: Session, id: UUID):
  db_employee = db.query(Employee).get(id)
  return EmployeeSchema.model_validate(db_employee)

def update_employee(db: Session, id: UUID, employee: EmployeeSchema):
  db_employee = db.query(Employee).get(id)
  for key, value in parse_schema(employee).items():
    setattr(db_employee, key, value)
  db.commit()
  db.refresh(db_employee)
  return db_employee

def delete_employee(db: Session, id: UUID):
  db_employee = db.query(Employee).where(Employee.id == id).first()
  if db_employee is None:
    raise ValueError(f"Employee with id {id} does not exist")
  db_employee.soft_delete()
  db.commit()