from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.api.housekeeping.models import CheckStatus, Housekeeping
from app.core.schema_operations import BaseModel


# 🔹 Individual Checklist Item Schema
class ChecklistItemSchema(BaseModel):
    item: str = Field(..., description="Checklist item description")
    status: Optional[CheckStatus] = Field(None, description="Check status: ✔, ✖, or N/A")
    notes: Optional[str] = Field(None, description="Additional notes for this item")


# 🔹 Main Housekeeping Schema (Response)
class HousekeepingSchema(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Unique identifier")

    # Basic Information
    location_area: str = Field(..., description="Location or area inspected")
    inspection_date: date = Field(..., description="Date of inspection")
    inspector_name: str = Field(..., description="Inspector/Petugas name")

    # Inspector Information
    inspector_id: UUID = Field(..., description="ID of the inspector (HSE user)")
    inspector_user_name: Optional[str] = Field(None, description="Inspector username from User table")

    # Facility Information
    facility_id: Optional[UUID] = Field(None, description="ID of the facility")
    facility_name: Optional[str] = Field(None, description="Facility name")

    # Checklist Sections
    section_a_items: List[ChecklistItemSchema] = Field(
        ..., description="Section A: Kebersihan Area Kerja"
    )
    section_b_items: List[ChecklistItemSchema] = Field(
        ..., description="Section B: Penataan Barang & Peralatan"
    )
    section_c_items: List[ChecklistItemSchema] = Field(
        ..., description="Section C: Keselamatan & K3"
    )
    section_d_items: List[ChecklistItemSchema] = Field(
        ..., description="Section D: Kebersihan Fasilitas Umum"
    )

    # Additional Notes
    additional_notes: Optional[str] = Field(None, description="Additional notes")

    # Metadata
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    class Meta:
        orm_model = Housekeeping


# 🔹 Create Schema (HSE users)
class HousekeepingCreateSchema(BaseModel):
    location_area: str = Field(..., description="Location or area", min_length=2, max_length=255)
    inspection_date: date = Field(..., description="Date of inspection")
    inspector_name: str = Field(..., description="Inspector name", min_length=2, max_length=255)

    # Optional facility link
    facility_id: Optional[UUID] = Field(None, description="Optional facility ID")

    # Checklist Sections
    section_a_items: List[ChecklistItemSchema] = Field(
        ..., description="Section A items", min_length=5, max_length=5
    )
    section_b_items: List[ChecklistItemSchema] = Field(
        ..., description="Section B items", min_length=5, max_length=5
    )
    section_c_items: List[ChecklistItemSchema] = Field(
        ..., description="Section C items", min_length=5, max_length=5
    )
    section_d_items: List[ChecklistItemSchema] = Field(
        ..., description="Section D items", min_length=5, max_length=5
    )

    # Additional Notes
    additional_notes: Optional[str] = Field(None, description="Additional notes")


# 🔹 Update Schema (Managers)
class HousekeepingUpdateSchema(BaseModel):
    location_area: Optional[str] = Field(None, description="Location or area", max_length=255)
    inspection_date: Optional[date] = Field(None, description="Date of inspection")
    inspector_name: Optional[str] = Field(None, description="Inspector name", max_length=255)
    facility_id: Optional[UUID] = Field(None, description="Optional facility ID")
    section_a_items: Optional[List[ChecklistItemSchema]] = Field(None, description="Section A items")
    section_b_items: Optional[List[ChecklistItemSchema]] = Field(None, description="Section B items")
    section_c_items: Optional[List[ChecklistItemSchema]] = Field(None, description="Section C items")
    section_d_items: Optional[List[ChecklistItemSchema]] = Field(None, description="Section D items")
    additional_notes: Optional[str] = Field(None, description="Additional notes")
