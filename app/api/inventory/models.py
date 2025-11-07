import enum
import uuid

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class LocationStatus(str, enum.Enum):
    in_storage = "in_storage"
    in_transit = "in_transit"


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    photo_file_ids = Column(ARRAY(UUID), nullable=True)
    attachment_file_ids = Column(ARRAY(UUID), nullable=True)

    # 🔹 General Info
    item_name = Column(String(255), nullable=False)
    item_description = Column(Text, nullable=True)
    item_category = Column(
        String(100), nullable=False
    )  # e.g., PPE, Chemical, Tool, Spare Part
    item_code = Column(String(50), nullable=False)
    manufacturer = Column(String(255), nullable=True)
    supplier = Column(String(255), nullable=True)

    # 🔹 Quantity & Measurement
    quantity = Column(Float, nullable=False, default=0.0)
    quantity_uom = Column(
        String(50), nullable=False, default="unit"
    )  # e.g., pcs, liters, kg
    minimum_stock_level = Column(Float, nullable=True)
    reorder_level = Column(Float, nullable=True)

    # 🔹 Location & Tracking
    storage_location_id = Column(UUID(as_uuid=True), ForeignKey(column="facilities.id"))
    storage_location = relationship("Facility", foreign_keys=[storage_location_id])

    location_status = Column(
        Enum(LocationStatus), nullable=False, default=LocationStatus.in_storage
    )

    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)

    assigned_department = Column(String(255), nullable=True)
    assigned_personnel = Column(String(255), nullable=True)
    asset_tag = Column(String(100), unique=True, nullable=True)

    # 🔹 Condition & Compliance
    condition_status = Column(String(100), nullable=True)  # e.g., New, Used, Damaged
    inspection_required = Column(Boolean, default=False)
    last_inspection_date = Column(DateTime, nullable=True)
    next_inspection_due = Column(DateTime, nullable=True)
    certification_expiry_date = Column(DateTime, nullable=True)
    safety_data_sheet_available = Column(Boolean, default=False)

    # 🔹 Dates
    purchase_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)

    # 🔹 Status
    is_active = Column(Boolean, default=True)
    remarks = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Inventory item_name={self.item_name} category={self.item_category} qty={self.quantity}>"


# class InventoryMovement(Base):
#     __tablename__ = "inventory_movement"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     inventory_id = Column(
#         UUID(as_uuid=True), ForeignKey("inventory.id"), nullable=False
#     )

#     reason = Column(String(255), nullable=True)

#     source_location_id = Column(UUID(as_uuid=True), nullable=True)
#     destination_location_id = Column(UUID(as_uuid=True), nullable=True)

#     remarks = Column(Text, nullable=True)

#     movement_date = Column(DateTime, default=datetime.datetime.now())


# class InventoryRouteLog(Base):
#     __tablename__ = "inventory_movement_route"

#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     movement_id = Column(
#         UUID(as_uuid=True), ForeignKey("inventory_movement_log.id"), nullable=False
#     )

#     # 🔹 Route details
#     sequence_number = Column(Integer, nullable=False)  # 1, 2, 3... order of points
#     latitude = Column(Float, nullable=True)
#     longitude = Column(Float, nullable=True)

#     remarks = Column(Text, nullable=True)
