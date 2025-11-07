import enum
import uuid

from sqlalchemy import ARRAY, Column, Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class FacilityTypeEnum(str, enum.Enum):
    OFFICE = "office"
    WAREHOUSE = "warehouse"
    YARD = "yard"
    RIG_SITE = "rig_site"
    PLANT = "plant"
    OTHER = "other"


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 🔹 General Info
    facility_name = Column(String(100), nullable=False)
    facility_type = Column(
        Enum(FacilityTypeEnum), nullable=False, default=FacilityTypeEnum.OTHER
    )
    description = Column(Text, nullable=True)

    # 🔹 Location
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    province = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # 🔹 Ownership / Management
    owner_company = Column(String(150), nullable=True)
    manager_name = Column(String(100), nullable=True)
    contact_email = Column(String(120), nullable=True)
    contact_phone = Column(String(50), nullable=True)

    photo_file_ids = Column(ARRAY(UUID), nullable=True)
