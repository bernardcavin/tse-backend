import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, Date, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CheckStatus(str, enum.Enum):
    GOOD = "✔"  # Baik / Sesuai
    NOT_COMPLIANT = "✖"  # Tidak Sesuai
    NOT_APPLICABLE = "N/A"  # Tidak Berlaku


class Housekeeping(Base):
    __tablename__ = "housekeeping"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 Basic Information
    location_area = Column(String(255), nullable=False)
    inspection_date = Column(Date, nullable=False)
    inspector_name = Column(String(255), nullable=False)

    # 🔹 Inspector (User who created the checklist - HSE)
    inspector_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # 🔹 Optional Facility Link
    facility_id = Column(PG_UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=True)

    # 🔹 Section A: Kebersihan Area Kerja (Cleanliness of Work Area)
    section_a_items = Column(JSON, nullable=False)
    # Format: [
    #   {"item": "Lantai bersih dari debu, minyak, dan kotoran", "status": "✔|✖|N/A", "notes": ""},
    #   {"item": "Tidak ada sampah berserakan", "status": "✔|✖|N/A", "notes": ""},
    #   ...
    # ]

    # 🔹 Section B: Penataan Barang & Peralatan (Organization of Goods & Equipment)
    section_b_items = Column(JSON, nullable=False)

    # 🔹 Section C: Keselamatan & K3 (Safety & K3)
    section_c_items = Column(JSON, nullable=False)

    # 🔹 Section D: Kebersihan Fasilitas Umum (Cleanliness of Public Facilities)
    section_d_items = Column(JSON, nullable=False)

    # 🔹 Additional Notes
    additional_notes = Column(Text, nullable=True)

    # 🔹 Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 🔹 Relationships
    inspector = relationship("User", foreign_keys=[inspector_id])
    facility = relationship("Facility", foreign_keys=[facility_id])
