import enum
import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import (
    ARRAY,
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship


class RequestType(str, enum.Enum):
    PURCHASE = "purchase"
    REIMBURSEMENT = "reimbursement"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TRANSFERRED = "transferred"
    REPORTED = "reported"
    DONE = "done"
    CANCELLED = "cancelled"


class Request(Base):
    __tablename__ = "requests"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Requester Info
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Request Details
    type = Column(Enum(RequestType), nullable=False)
    purpose = Column(Text, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    actual_cost = Column(Float, nullable=True)
    
    # Items (JSON)
    # Structure: [{"name": "Item 1", "cost": 10000}, {"name": "Item 2", "cost": 20000}]
    items = Column(ARRAY(JSON), nullable=True, default=[])

    # Status
    status = Column(
        Enum(RequestStatus),
        nullable=False,
        default=RequestStatus.PENDING,
    )

    # Attachments (File IDs)
    attachment_file_ids = Column(ARRAY(PG_UUID), nullable=True)
    transfer_proof_file_ids = Column(ARRAY(PG_UUID), nullable=True)
    receipt_file_ids = Column(ARRAY(PG_UUID), nullable=True)

    # Approval/Rejection Info
    rejection_reason = Column(Text, nullable=True)
    manager_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Finance Info
    finance_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    manager = relationship("User", foreign_keys=[manager_id])
    finance = relationship("User", foreign_keys=[finance_id])
