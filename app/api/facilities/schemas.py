from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, Field

from app.api.facilities.models import Facility, FacilityTypeEnum
from app.core.schema_operations import BaseModel


class FacilitySchema(BaseModel):
    id: Optional[UUID] = Field(
        default=None, description="Unique identifier for the facility"
    )

    # 🔹 General Info
    facility_name: str = Field(..., description="Name of the facility")
    facility_type: FacilityTypeEnum = Field(
        default=FacilityTypeEnum.OTHER, description="Type of the facility"
    )
    description: Optional[str] = Field(
        None, description="Detailed description of the facility"
    )

    # 🔹 Location
    address: Optional[str] = Field(None, description="Street address of the facility")
    city: Optional[str] = Field(None, description="City where the facility is located")
    province: Optional[str] = Field(
        None, description="Province or state of the facility"
    )
    country: Optional[str] = Field(None, description="Country of the facility")
    latitude: Optional[float] = Field(
        None, description="Latitude coordinate of the facility"
    )
    longitude: Optional[float] = Field(
        None, description="Longitude coordinate of the facility"
    )

    # 🔹 Ownership / Management
    owner_company: Optional[str] = Field(
        None, description="Company that owns the facility"
    )
    manager_name: Optional[str] = Field(
        None, description="Name of the facility manager"
    )
    contact_email: Optional[EmailStr] = Field(
        None, description="Email contact for the facility"
    )
    contact_phone: Optional[str] = Field(
        None, description="Phone number for the facility"
    )

    photo_file_ids: Optional[List[UUID]] = Field(
        None, description="List of photo file IDs"
    )

    class Meta:
        orm_model = Facility
