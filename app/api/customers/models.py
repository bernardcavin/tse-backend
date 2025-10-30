import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Boolean, Column, Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=True, unique=True)
    email = Column(String(100), nullable=True, unique=True)
    gender = Column(String(20), nullable=True)  # e.g., "Male", "Female", "Non-binary"
    date_of_birth = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)  # for allergies, preferences, or VIP notes
    is_vip = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now(), nullable=False)

    def __repr__(self):
        return f"<Customer(name='{self.full_name}', phone='{self.phone_number}')>"
