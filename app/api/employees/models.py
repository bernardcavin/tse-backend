import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True, unique=True)
    role = Column(String(50), nullable=False, default="Stylist")  # e.g. Stylist, Nail Tech, Receptionist
    specialization = Column(String(100), nullable=True)  # e.g. “Colorist”, “Fade Expert”
    bio = Column(Text, nullable=True)
    commission_rate = Column(Float, nullable=True, default=0.0)  # % per service if you do rev-split
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Employee(name='{self.full_name}', role='{self.role}')>"
