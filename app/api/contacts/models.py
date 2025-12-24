import uuid

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 Basic Info
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    position = Column(String(100), nullable=True)

    # 🔹 Organization
    company = Column(String(150), nullable=True)
    regional = Column(Integer, nullable=True)  # 0=None, 1-4=Regional 1-4
    zone = Column(String(100), nullable=True)
    field = Column(String(100), nullable=True)

    # 🔹 Additional Info
    address = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
