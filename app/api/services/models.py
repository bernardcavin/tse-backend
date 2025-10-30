import uuid
from datetime import datetime

from app.core.database import Base  # assuming you got a Base from declarative_base()
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)  # e.g., "Hair", "Nails", "Facial"
    description = Column(Text, nullable=True)
    duration_minutes = Column(Float, nullable=False, default=30.0)  # length of service
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime, default=datetime.now(), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now(), nullable=False)

    def __repr__(self):
        return f"<Service(name='{self.name}', price={self.price}, duration={self.duration_minutes}min)>"
