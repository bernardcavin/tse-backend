from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.api.facilities.schemas import FacilitySchema
from app.api.inventory.models import Inventory, LocationStatus
from app.core.schema_operations import BaseModel


class InventorySchema(BaseModel):
    id: Optional[UUID] = None

    # 🔹 General Info
    item_name: str = Field(..., description="Name of the inventory item")
    item_description: Optional[str] = Field(
        None, description="Detailed description of the item"
    )
    item_category: str = Field(
        ..., description="Category such as PPE, Chemical, Tool, etc."
    )
    item_code: str = Field(..., description="Unique item code")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    supplier: Optional[str] = Field(None, description="Supplier name")

    # 🔹 Quantity & Measurement
    quantity: float = Field(0.0, description="Quantity available")
    quantity_uom: str = Field(
        "unit", description="Unit of measurement (e.g. pcs, liters, kg)"
    )
    minimum_stock_level: Optional[float] = Field(
        None, description="Minimum allowable stock before alert"
    )
    reorder_level: Optional[float] = Field(
        None, description="Stock level that triggers reordering"
    )

    # 🔹 Location & Tracking
    storage_location_id: UUID = Field(..., description="ID of the storage location")
    storage_location: Optional[FacilitySchema] = Field(
        None, description="The storage location of the item"
    )
    location_status: LocationStatus = Field(
        LocationStatus.in_storage,
        description="Current status of the item (in_storage, in_transit)",
    )
    current_latitude: Optional[float] = Field(
        None, description="Current latitude of the item"
    )
    current_longitude: Optional[float] = Field(
        None, description="Current longitude of the item"
    )

    assigned_department: Optional[str] = Field(
        None, description="Department using the item"
    )
    assigned_personnel: Optional[str] = Field(
        None, description="Personnel responsible for item"
    )
    asset_tag: Optional[str] = Field(None, description="Unique asset tag or barcode")

    # 🔹 Condition & Compliance
    condition_status: str = Field(
        ..., description="Condition of item (New, Used, Damaged)"
    )
    inspection_required: bool = Field(
        False, description="Whether item needs periodic inspection"
    )
    last_inspection_date: Optional[datetime] = Field(
        None, description="Last inspection date"
    )
    next_inspection_due: Optional[datetime] = Field(
        None, description="Next inspection due date"
    )
    certification_expiry_date: Optional[datetime] = Field(
        None, description="Certification expiry date"
    )
    safety_data_sheet_available: bool = Field(
        False, description="Whether SDS is available"
    )

    # 🔹 Dates
    purchase_date: Optional[datetime] = Field(None, description="Purchase date")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date of the item")

    # 🔹 Status
    is_active: bool = Field(True, description="Item is active or inactive")
    remarks: Optional[str] = Field(None, description="Additional notes or comments")

    # 🔹 Files
    photo_file_ids: list[UUID] = Field(
        [], description="List of photo file IDs associated with the item"
    )
    attachment_file_ids: list[UUID] = Field(
        [], description="List of attachment file IDs associated with the item"
    )

    class Meta:
        orm_model = Inventory
