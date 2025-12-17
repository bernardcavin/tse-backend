import json
import math
import uuid
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.attendance.models import AttendanceLocation, AttendanceRecord, AttendanceStatus
from app.api.attendance.schemas import (
    AttendanceLocationSchema,
    AttendanceRecordSchema,
    CheckInRequest,
    CheckOutRequest,
)
from app.core.schema_operations import parse_schema
from app.utils.filter_utils import get_paginated_data


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def validate_geolocation(
    user_lat: float, user_lon: float, location_lat: float, location_lon: float, radius: int
) -> bool:
    """
    Validate if user's location is within the geofence radius.
    Returns True if within radius, False otherwise.
    """
    distance = calculate_distance(user_lat, user_lon, location_lat, location_lon)
    return distance <= radius


# ============================================================================
# ATTENDANCE LOCATIONS
# ============================================================================


def create_attendance_location(
    db: Session, location: AttendanceLocationSchema, created_by_id: UUID
) -> AttendanceLocationSchema:
    """Create a new attendance location"""
    location_dict = location.model_dump(exclude_unset=True, exclude={"id"})
    location_dict["created_by_id"] = created_by_id

    # Generate QR code data (JSON with location ID)
    temp_id = str(uuid.uuid4())
    qr_data = json.dumps({"location_id": temp_id, "type": "attendance"})
    location_dict["qr_code_data"] = qr_data

    db_location = AttendanceLocation(**location_dict)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)

    # Update QR code with actual ID
    qr_data = json.dumps({"location_id": str(db_location.id), "type": "attendance"})
    db_location.qr_code_data = qr_data
    db.commit()
    db.refresh(db_location)

    return AttendanceLocationSchema.model_validate(db_location).model_dump(mode='json')


def get_attendance_location(db: Session, location_id: UUID) -> AttendanceLocationSchema:
    """Get a single attendance location by ID"""
    location = (
        db.query(AttendanceLocation).filter(AttendanceLocation.id == location_id).first()
    )
    if not location:
        raise HTTPException(status_code=404, detail="Attendance location not found")
    return AttendanceLocationSchema.model_validate(location).model_dump(mode='json')


def get_all_attendance_locations(
    db: Session, request, active_only: bool = False
) -> dict:
    """Get all attendance locations with pagination"""
    query = db.query(AttendanceLocation)

    if active_only:
        query = query.filter(AttendanceLocation.is_active == True)

    # Use standard pagination utility
    return get_paginated_data(db, request, AttendanceLocation, AttendanceLocationSchema, "location_name")


def update_attendance_location(
    db: Session, location_id: UUID, location: AttendanceLocationSchema
) -> AttendanceLocationSchema:
    """Update an attendance location"""
    db_location = (
        db.query(AttendanceLocation).filter(AttendanceLocation.id == location_id).first()
    )
    if not db_location:
        raise HTTPException(status_code=404, detail="Attendance location not found")

    update_data = location.model_dump(exclude_unset=True, exclude={"id", "created_by_id"})
    for key, value in update_data.items():
        setattr(db_location, key, value)

    db.commit()
    db.refresh(db_location)
    return AttendanceLocationSchema.model_validate(db_location).model_dump(mode='json')


def delete_attendance_location(db: Session, location_id: UUID) -> None:
    """Delete an attendance location"""
    db_location = (
        db.query(AttendanceLocation).filter(AttendanceLocation.id == location_id).first()
    )
    if not db_location:
        raise HTTPException(status_code=404, detail="Attendance location not found")

    db.delete(db_location)
    db.commit()


# ============================================================================
# ATTENDANCE RECORDS
# ============================================================================


def check_in(db: Session, request: CheckInRequest, user_id: UUID) -> AttendanceRecordSchema:
    """Check in an employee with QR code and location validation"""
    # Get location
    location = (
        db.query(AttendanceLocation)
        .filter(AttendanceLocation.id == request.location_id)
        .first()
    )
    if not location:
        raise HTTPException(status_code=404, detail="Attendance location not found")

    if not location.is_active:
        raise HTTPException(status_code=400, detail="Attendance location is inactive")

    # Validate QR code
    if location.qr_code_data != request.qr_code_data:
        raise HTTPException(status_code=400, detail="Invalid QR code")

    # Validate geolocation
    if not validate_geolocation(
        request.latitude,
        request.longitude,
        location.latitude,
        location.longitude,
        location.radius_meters,
    ):
        raise HTTPException(
            status_code=400,
            detail=f"You are not within the required {location.radius_meters}m radius of the attendance location",
        )

    # Check if user already has an active check-in
    existing_record = (
        db.query(AttendanceRecord)
        .filter(
            and_(
                AttendanceRecord.user_id == user_id,
                AttendanceRecord.status == AttendanceStatus.CHECKED_IN,
            )
        )
        .first()
    )
    if existing_record:
        raise HTTPException(
            status_code=400,
            detail="You already have an active check-in. Please check out first.",
        )

    # Create attendance record
    record = AttendanceRecord(
        user_id=user_id,
        location_id=request.location_id,
        check_in_time=datetime.utcnow(),
        check_in_latitude=request.latitude,
        check_in_longitude=request.longitude,
        status=AttendanceStatus.CHECKED_IN,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return AttendanceRecordSchema.model_validate(record).model_dump(mode='json')


def check_out(db: Session, request: CheckOutRequest, user_id: UUID) -> AttendanceRecordSchema:
    """Check out an employee"""
    # Get attendance record
    record = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.id == request.attendance_record_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    # Verify ownership
    if record.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="You can only check out your own attendance"
        )

    # Verify status
    if record.status == AttendanceStatus.CHECKED_OUT:
        raise HTTPException(status_code=400, detail="Already checked out")

    # Update record
    record.check_out_time = datetime.utcnow()
    record.check_out_latitude = request.latitude
    record.check_out_longitude = request.longitude
    record.status = AttendanceStatus.CHECKED_OUT
    if request.notes:
        record.notes = request.notes

    db.commit()
    db.refresh(record)

    return AttendanceRecordSchema.model_validate(record).model_dump(mode='json')


def get_attendance_records(
    db: Session,
    request,
    user_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict:
    """Get attendance records with filters"""
    query = db.query(AttendanceRecord)

    # Apply filters
    if user_id:
        query = query.filter(AttendanceRecord.user_id == user_id)
    if location_id:
        query = query.filter(AttendanceRecord.location_id == location_id)
    if start_date:
        query = query.filter(AttendanceRecord.check_in_time >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.check_in_time <= end_date)

    # Use standard pagination utility
    return get_paginated_data(db, request, AttendanceRecord, AttendanceRecordSchema, "check_in_time")


def get_attendance_record(db: Session, record_id: UUID) -> AttendanceRecordSchema:
    """Get a single attendance record"""
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return AttendanceRecordSchema.model_validate(record).model_dump(mode='json')


def get_active_check_in(db: Session, user_id: UUID) -> Optional[AttendanceRecordSchema]:
    """Get the user's active check-in if any"""
    record = (
        db.query(AttendanceRecord)
        .filter(
            and_(
                AttendanceRecord.user_id == user_id,
                AttendanceRecord.status == AttendanceStatus.CHECKED_IN,
            )
        )
        .first()
    )
    if record:
        return AttendanceRecordSchema.model_validate(record).model_dump(mode='json')
    return None
