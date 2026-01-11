import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExpeditionStatus(str, enum.Enum):
    """Status of an expedition."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Expedition(Base):
    """Main expedition entity tracking inventory movement by employees."""
    __tablename__ = "expeditions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Employee who started the expedition
    employee_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Status tracking
    status = Column(
        Enum(ExpeditionStatus),
        nullable=False,
        default=ExpeditionStatus.ACTIVE,
    )
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    
    # Optional notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    items = relationship("ExpeditionItem", back_populates="expedition", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Expedition id={self.id} employee={self.employee_id} status={self.status}>"


class ExpeditionItem(Base):
    """Junction table linking expeditions to inventory items with quantity tracking."""
    __tablename__ = "expedition_items"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    expedition_id = Column(PG_UUID(as_uuid=True), ForeignKey("expeditions.id"), nullable=False)
    inventory_id = Column(PG_UUID(as_uuid=True), ForeignKey("inventory.id"), nullable=False)
    
    # Quantity tracking
    quantity = Column(Float, nullable=False)  # Quantity being moved in this expedition
    confirmed_quantity = Column(Float, nullable=True)  # Quantity confirmed when ending expedition
    
    # Timestamps
    scanned_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # When item was added
    confirmed_at = Column(DateTime, nullable=True)  # When item was confirmed during end process
    
    # Relationships
    expedition = relationship("Expedition", back_populates="items")
    inventory = relationship("Inventory", foreign_keys=[inventory_id])

    def __repr__(self):
        return f"<ExpeditionItem expedition={self.expedition_id} inventory={self.inventory_id} qty={self.quantity}>"
