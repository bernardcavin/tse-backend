import uuid
from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class FileRecordStatus(PyEnum):
    PENDING = "PENDING"
    MISSING = "MISSING"
    UPLOADED = "UPLOADED"


class FileRecord(Base):
    __tablename__ = "files"

    id = Column(
        UUID(), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    filename = Column(String(255))
    size = Column(BigInteger)
    content_type = Column(String(255))
    upload_date = Column(DateTime)
    status = Column(Enum(FileRecordStatus))
    uploaded_by_id = Column(UUID(), nullable=True)
