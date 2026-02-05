import enum
import uuid
from datetime import datetime

from app.core.database import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship


class AttendanceStatus(str, enum.Enum):
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"


class AttendanceLocation(Base):
    __tablename__ = "attendance_locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 Location Info
    location_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(255), nullable=True)

    # 🔹 Geolocation
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Integer, nullable=False, default=100)  # Geofence radius
    attendance_max_time = Column(Time, nullable=True)  # Max time for auto-checkout

    # 🔹 QR Code
    qr_code_data = Column(Text, nullable=True)  # Stores the QR code payload

    # 🔹 Status
    is_active = Column(Boolean, default=True, nullable=False)

    # 🔹 Metadata
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    attendance_records = relationship(
        "AttendanceRecord", back_populates="location", cascade="all, delete-orphan"
    )


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 User & Location
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    location_id = Column(
        UUID(as_uuid=True), ForeignKey("attendance_locations.id"), nullable=False
    )

    # 🔹 Check-in Details
    check_in_time = Column(DateTime, nullable=False, server_default=func.now())
    check_in_latitude = Column(Float, nullable=True)
    check_in_longitude = Column(Float, nullable=True)

    # 🔹 Check-out Details
    check_out_time = Column(DateTime, nullable=True)
    check_out_latitude = Column(Float, nullable=True)
    check_out_longitude = Column(Float, nullable=True)

    # 🔹 Status
    status = Column(
        Enum(AttendanceStatus),
        nullable=False,
        default=AttendanceStatus.CHECKED_IN,
    )

    # 🔹 Notes
    notes = Column(Text, nullable=True)

    # 🔹 Metadata
    created_at = Column(DateTime, server_default=func.now(), default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    location = relationship("AttendanceLocation", back_populates="attendance_records")


class LeaveRequestType(str, enum.Enum):
    SICK = "sick"
    PAID = "paid"
    UNPAID = "unpaid"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    OTHER = "other"


class LeaveRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 User Info
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 🔹 Leave Details
    leave_type = Column(Enum(LeaveRequestType), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)

    # 🔹 Status
    status = Column(
        Enum(LeaveRequestStatus),
        nullable=False,
        default=LeaveRequestStatus.PENDING,
    )
    rejection_reason = Column(Text, nullable=True)

    # 🔹 Approval Metadata
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # 🔹 Metadata
    created_at = Column(DateTime, server_default=func.now(), default=datetime.now, nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), default=datetime.now, onupdate=datetime.now, nullable=False
    )

    # Attachment
    attachment_file_ids = Column(ARRAY(UUID), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    manager = relationship("User", foreign_keys=[manager_id])

