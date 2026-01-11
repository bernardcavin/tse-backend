from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.api.requests.models import Request, RequestStatus, RequestType
from app.core.schema_operations import BaseModel


class RequestItemSchema(BaseModel):
    name: str = Field(..., description="Name of the item")
    cost: float = Field(..., description="Cost of the item")


class RequestSchema(BaseModel):
    id: UUID = Field(..., description="Unique identifier")
    
    # Requester Info
    employee_id: UUID = Field(..., description="ID of the employee who made the request")
    employee_name: Optional[str] = Field(None, description="Name of the employee")
    
    # Request Details
    type: RequestType = Field(..., description="Type of request")
    purpose: str = Field(..., description="Purpose of the request")
    estimated_cost: float = Field(..., description="Estimated cost")
    actual_cost: Optional[float] = Field(None, description="Actual cost (filled when reporting)")
    items: List[RequestItemSchema] = Field(default_factory=list, description="List of items")
    
    # Status
    status: RequestStatus = Field(..., description="Current status")
    
    # Attachments
    attachment_file_ids: Optional[List[UUID]] = Field(None, description="Initial attachment file IDs")
    transfer_proof_file_ids: Optional[List[UUID]] = Field(None, description="Transfer proof file IDs")
    receipt_file_ids: Optional[List[UUID]] = Field(None, description="Receipt/Proof file IDs")
    
    # Approval/Rejection Info
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    manager_id: Optional[UUID] = Field(None, description="ID of manager who approved/rejected")
    manager_name: Optional[str] = Field(None, description="Name of the manager")
    
    # Finance Info
    finance_id: Optional[UUID] = Field(None, description="ID of finance staff who transferred")
    finance_name: Optional[str] = Field(None, description="Name of the finance staff")
    
    # Metadata
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    class Meta:
        orm_model = Request


class RequestCreateSchema(BaseModel):
    type: RequestType = Field(..., description="Type of request")
    purpose: str = Field(..., description="Purpose of the request")
    estimated_cost: float = Field(..., description="Estimated cost")
    items: List[RequestItemSchema] = Field(default_factory=list, description="List of items")
    attachment_file_ids: Optional[List[UUID]] = Field(None, description="Attachment file IDs")


class RequestUpdateSchema(BaseModel):
    type: Optional[RequestType] = Field(None, description="Type of request")
    purpose: Optional[str] = Field(None, description="Purpose of the request")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")
    items: Optional[List[RequestItemSchema]] = Field(None, description="List of items")
    attachment_file_ids: Optional[List[UUID]] = Field(None, description="Attachment file IDs")


class RequestActionSchema(BaseModel):
    action: str = Field(..., description="Action to perform: approve, reject, transfer, report, done, cancel")
    
    # For Reject
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection (required if action is reject)")
    
    # For Transfer
    transfer_proof_file_ids: Optional[List[UUID]] = Field(None, description="Transfer proof file IDs (required if action is transfer)")
    
    # For Report
    actual_cost: Optional[float] = Field(None, description="Actual cost (required if action is report)")
    receipt_file_ids: Optional[List[UUID]] = Field(None, description="Receipt file IDs (required if action is report)")
