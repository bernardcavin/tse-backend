from datetime import datetime, time
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.api.attendance.models import (
    AttendanceLocation,
    AttendanceRecord,
    AttendanceStatus,
    LeaveRequest,
    LeaveRequestType,
    LeaveRequestStatus,
)
from app.core.schema_operations import BaseModel


class AttendanceLocationSchema(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Unique identifier")

    # Location Info
    location_name: str = Field(..., description="Name of the attendance location")
    description: Optional[str] = Field(None, description="Description of the location")
    address: Optional[str] = Field(None, description="Physical address")

    # Geolocation
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    radius_meters: int = Field(
        default=100, description="Geofence radius in meters", ge=1, le=10000
    )
    attendance_max_time: Optional[time] = Field(None, description="Max time for auto-checkout")

    # QR Code
    qr_code_data: Optional[str] = Field(None, description="QR code payload")

    # Status
    is_active: bool = Field(default=True, description="Whether location is active")

    # Metadata
    created_by_id: Optional[UUID] = Field(None, description="Creator user ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None,
            time: lambda v: v.strftime('%H:%M:%S') if v else None
        }

    class Meta:
        orm_model = AttendanceLocation


class AttendanceRecordSchema(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Unique identifier")

    # User & Location
    user_id: UUID = Field(..., description="Employee user ID")
    location_id: UUID = Field(..., description="Attendance location ID")
    
    # Names for display
    employee_name: Optional[str] = Field(None, description="Employee name")
    location_name: Optional[str] = Field(None, description="Location name")

    # Check-in Details
    check_in_time: datetime = Field(..., description="Check-in timestamp")
    check_in_latitude: Optional[float] = Field(None, description="Check-in latitude")
    check_in_longitude: Optional[float] = Field(None, description="Check-in longitude")

    # Check-out Details
    check_out_time: Optional[datetime] = Field(None, description="Check-out timestamp")
    check_out_latitude: Optional[float] = Field(None, description="Check-out latitude")
    check_out_longitude: Optional[float] = Field(
        None, description="Check-out longitude"
    )

    # Status
    status: AttendanceStatus = Field(
        default=AttendanceStatus.CHECKED_IN, description="Attendance status"
    )

    # Notes
    notes: Optional[str] = Field(None, description="Additional notes")

    # Metadata
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }

    class Meta:
        orm_model = AttendanceRecord


class CheckInRequest(BaseModel):
    location_id: UUID = Field(..., description="Attendance location ID")
    qr_code_data: str = Field(..., description="Scanned QR code data")
    latitude: float = Field(..., description="User's current latitude")
    longitude: float = Field(..., description="User's current longitude")
    face_embedding: list[float] = Field(..., description="Pre-computed face embedding from client")


class CheckOutRequest(BaseModel):
    attendance_record_id: UUID = Field(..., description="Attendance record ID")
    latitude: Optional[float] = Field(None, description="User's current latitude")
    longitude: Optional[float] = Field(None, description="User's current longitude")
    notes: Optional[str] = Field(None, description="Additional notes")
    face_embedding: Optional[list[float]] = Field(None, description="Pre-computed face embedding from client")


class GenerateQRCodeRequest(BaseModel):
    location_id: UUID = Field(..., description="Location ID to generate QR code for")


class AttendanceRecordUpdate(BaseModel):
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        from_attributes = True


class LeaveRequestSchema(BaseModel):
    id: Optional[UUID] = Field(default=None, description="Unique identifier")
    user_id: UUID = Field(..., description="Employee user ID")
    employee_name: Optional[str] = Field(None, description="Employee name")
    
    leave_type: LeaveRequestType = Field(..., description="Type of leave")
    start_date: datetime = Field(..., description="Start date of leave")
    end_date: datetime = Field(..., description="End date of leave")
    reason: str = Field(..., description="Reason for leave")
    attachment_file_ids: Optional[list[UUID]] = Field(None, description="List of uploaded file IDs")
    
    status: LeaveRequestStatus = Field(default=LeaveRequestStatus.PENDING, description="Status of request")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    
    manager_id: Optional[UUID] = Field(None, description="Manager who approved/rejected")
    manager_name: Optional[str] = Field(None, description="Manager name")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Update timestamp")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S') if v else None
        }

    class Meta:
        orm_model = LeaveRequest


class LeaveRequestCreate(BaseModel):
    leave_type: LeaveRequestType = Field(..., description="Type of leave")
    start_date: datetime = Field(..., description="Start date of leave")
    end_date: datetime = Field(..., description="End date of leave")
    reason: str = Field(..., description="Reason for leave")
    attachment_file_ids: Optional[list[UUID]] = Field(None, description="List of uploaded file IDs")


class LeaveRequestUpdate(BaseModel):
    status: LeaveRequestStatus = Field(..., description="New status")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if rejected")


