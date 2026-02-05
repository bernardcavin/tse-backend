import enum
import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import (
    ARRAY,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class TaskStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ON_HOLD = "ON_HOLD"


class TaskPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(Enum(TaskStatus), default=TaskStatus.PLANNED, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    
    # date = Column(Date, nullable=True) # Deprecated in favor of start_date/end_date
    time_start = Column(String, nullable=True)
    time_end = Column(String, nullable=True)
    
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Relationships
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    assignee_ids = Column(ARRAY(UUID), nullable=True)  # List of User UUIDs
    
    attachment_file_ids = Column(ARRAY(UUID), nullable=True) # List of File UUIDs
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Task title={self.title} status={self.status}>"
