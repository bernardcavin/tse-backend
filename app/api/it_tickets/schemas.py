from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.api.it_tickets.models import (
    ITTicket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.core.schema_operations import BaseModel


class ITTicketSchema(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Unique identifier")

    # Photo File IDs
    photo_file_ids: Optional[List[UUID]] = Field(None, description="Attachment file IDs")

    # Ticket Info
    title: str = Field(..., description="Title of the ticket")
    description: str = Field(..., description="Detailed description of the issue")
    category: TicketCategory = Field(
        default=TicketCategory.OTHER, description="Category of the ticket"
    )
    priority: TicketPriority = Field(
        default=TicketPriority.MEDIUM, description="Priority level"
    )

    # Reporter Information
    reporter_id: UUID = Field(..., description="ID of the person who submitted the ticket")
    reporter_name: Optional[str] = Field(None, description="Name of the reporter")

    # Location
    facility_id: Optional[UUID] = Field(None, description="Facility where issue occurs")
    facility_name: Optional[str] = Field(None, description="Facility name")

    # Inventory Link
    inventory_item_id: Optional[UUID] = Field(None, description="Linked inventory item ID")
    inventory_item_name: Optional[str] = Field(None, description="Linked inventory item name")

    # Assignment
    assigned_to_id: Optional[UUID] = Field(None, description="ID of assigned IT staff")
    assigned_to_name: Optional[str] = Field(None, description="Name of assigned IT staff")

    # Status
    status: TicketStatus = Field(
        default=TicketStatus.OPEN, description="Current status of the ticket"
    )

    # Resolution Information
    resolved_by_id: Optional[UUID] = Field(None, description="ID of person who resolved")
    resolved_by_name: Optional[str] = Field(None, description="Name of the resolver")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

    # Metadata
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    class Meta:
        orm_model = ITTicket


class ITTicketCreateSchema(BaseModel):
    title: str = Field(..., description="Title of the ticket", min_length=5, max_length=255)
    description: str = Field(
        ..., description="Detailed description of the issue", min_length=10
    )
    category: TicketCategory = Field(
        default=TicketCategory.OTHER, description="Category of the ticket"
    )
    priority: TicketPriority = Field(
        default=TicketPriority.MEDIUM, description="Priority level"
    )
    facility_id: Optional[UUID] = Field(None, description="Facility where issue occurs")
    inventory_item_id: Optional[UUID] = Field(None, description="Linked inventory item ID")
    photo_file_ids: Optional[List[UUID]] = Field(None, description="Attachment file IDs")


class ITTicketUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, description="Title of the ticket", max_length=255)
    description: Optional[str] = Field(None, description="Detailed description")
    category: Optional[TicketCategory] = Field(None, description="Category")
    priority: Optional[TicketPriority] = Field(None, description="Priority level")
    facility_id: Optional[UUID] = Field(None, description="Facility ID")
    inventory_item_id: Optional[UUID] = Field(None, description="Linked inventory item ID")
    status: Optional[TicketStatus] = Field(None, description="Current status")
    photo_file_ids: Optional[List[UUID]] = Field(None, description="Attachment file IDs")


class ITTicketResolveSchema(BaseModel):
    resolution_notes: str = Field(
        ..., description="Resolution notes", min_length=10
    )


class ITTicketAssignSchema(BaseModel):
    assigned_to_id: UUID = Field(..., description="ID of IT staff to assign")
