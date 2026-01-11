from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.api.expeditions.models import Expedition, ExpeditionItem, ExpeditionStatus
from app.api.inventory.schemas import InventorySchema
from app.core.schema_operations import BaseModel
from app.api.auth.schemas import UserSchema

class ExpeditionItemSchema(BaseModel):
    """Schema for expedition items with inventory details."""
    id: Optional[UUID] = None
    expedition_id: Optional[UUID] = None
    inventory_id: UUID = Field(..., description="ID of the inventory item")
    
    # Quantity tracking
    quantity: float = Field(..., description="Quantity being moved")
    confirmed_quantity: Optional[float] = Field(None, description="Quantity confirmed during end process")
    
    # Timestamps
    scanned_at: Optional[datetime] = Field(None, description="When item was added to expedition")
    confirmed_at: Optional[datetime] = Field(None, description="When item was confirmed")
    
    # Nested inventory details
    inventory: Optional[InventorySchema] = Field(None, description="Full inventory item details")

    class Meta:
        orm_model = ExpeditionItem


class ExpeditionSchema(BaseModel):
    """Schema for expeditions."""
    id: Optional[UUID] = None
    
    # Employee info
    employee_id: UUID = Field(..., description="ID of employee who started the expedition")
    employee: Optional[UserSchema] = Field(None, description="Employee details")
    
    # Status
    status: ExpeditionStatus = Field(
        ExpeditionStatus.ACTIVE,
        description="Current status of the expedition"
    )
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="When expedition was started")
    ended_at: Optional[datetime] = Field(None, description="When expedition was ended")
    
    # Notes
    notes: Optional[str] = Field(None, description="Optional notes about the expedition")
    
    # Items in this expedition
    items: list[ExpeditionItemSchema] = Field([], description="Items in this expedition")

    class Meta:
        orm_model = Expedition


class CreateExpeditionSchema(BaseModel):
    """Schema for creating a new expedition."""
    notes: Optional[str] = Field(None, description="Optional notes about the expedition")


class AddItemSchema(BaseModel):
    """Schema for adding an item to an expedition."""
    inventory_id: UUID = Field(..., description="ID of the inventory item to add")
    quantity: float = Field(..., gt=0, description="Quantity to add (must be positive)")


class UpdateItemQuantitySchema(BaseModel):
    """Schema for updating item quantity in an expedition."""
    quantity: float = Field(..., gt=0, description="New quantity (must be positive)")


class ConfirmItemSchema(BaseModel):
    """Schema for confirming an item when ending expedition."""
    confirmed_quantity: float = Field(..., ge=0, description="Confirmed quantity (can be 0 if item is missing)")


class EndExpeditionSchema(BaseModel):
    """Schema for ending an expedition."""
    notes: Optional[str] = Field(None, description="Final notes about the expedition")


class ExpeditionAnalytics(BaseModel):
    """Analytics data for expeditions dashboard."""
    total_expeditions: int = Field(0, description="Total number of expeditions")
    active_expeditions: int = Field(0, description="Number of active expeditions")
    completed_expeditions: int = Field(0, description="Number of completed expeditions")
    cancelled_expeditions: int = Field(0, description="Number of cancelled expeditions")
    total_items_moved: int = Field(0, description="Total items moved across all expeditions")
    items_in_transit: int = Field(0, description="Items currently in active expeditions")
