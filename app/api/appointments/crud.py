
from uuid import UUID

from app.api.appointments.models import Appointment
from app.api.appointments.schemas import AppointmentSchema
from app.core.schema_operations import parse_schema
from sqlalchemy.orm import Session


def create_appointment(db: Session,appointment: AppointmentSchema):
  db_appointment = Appointment(**parse_schema(appointment))
  
  db.add(db_appointment)
  db.flush()  # attaches it to session
  db_appointment.load_employees(db)
  db.commit()
  db.refresh(db_appointment)
  return db_appointment

def get_appointment(db: Session, id: UUID):
  db_appointment = db.query(Appointment).where(Appointment.id == id).first()
  return AppointmentSchema.model_validate(db_appointment)

def update_appointment(db: Session, id: UUID, appointment: AppointmentSchema):
  db_appointment = db.query(Appointment).where(Appointment.id == id).first()
  if db_appointment is None:
    raise ValueError(f"Appointment with id {id} does not exist")
  for key, value in parse_schema(appointment).items():
    setattr(db_appointment, key, value)
  db.flush()  # attaches it to session
  db_appointment.load_employees(db)
  db.commit()
  db.refresh(db_appointment)
  return db_appointment

def delete_appointment(db: Session, id: UUID):
  db_appointment = db.query(Appointment).where(Appointment.id == id).first()
  if db_appointment is None:
    raise ValueError(f"Appointment with id {id} does not exist")
  db_appointment.soft_delete()
  db.commit()