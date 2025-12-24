import enum
import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketCategory(str, enum.Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    ACCOUNT_ACCESS = "account_access"
    OTHER = "other"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ITTicket(Base):
    __tablename__ = "it_tickets"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 Attachments (Screenshots, Documents)
    photo_file_ids = Column(ARRAY(PG_UUID), nullable=True)

    # 🔹 Ticket Info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(
        Enum(TicketCategory),
        nullable=False,
        default=TicketCategory.OTHER,
    )
    priority = Column(
        Enum(TicketPriority),
        nullable=False,
        default=TicketPriority.MEDIUM,
    )

    # 🔹 Reporter (Who submitted the ticket)
    reporter_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 🔹 Location/Facility
    facility_id = Column(PG_UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=True)

    # 🔹 Link to IT Inventory (Optional - for asset-related tickets)
    inventory_item_id = Column(PG_UUID(as_uuid=True), ForeignKey("inventory.id"), nullable=True)

    # 🔹 Assignment (IT Staff assigned to handle)
    assigned_to_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # 🔹 Status
    status = Column(
        Enum(TicketStatus),
        nullable=False,
        default=TicketStatus.OPEN,
    )

    # 🔹 Resolution Information
    resolved_by_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # 🔹 Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 🔹 Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    facility = relationship("Facility", foreign_keys=[facility_id])
    inventory_item = relationship("Inventory", foreign_keys=[inventory_item_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
