from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.attendance import crud, schemas
from app.api.auth.crud import can_view_all_employees, log_contribution
from app.api.auth.models import UserRole
from app.api.auth.utils import get_current_user
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/attendance")


# ============================================================================
# ATTENDANCE LOCATIONS (Manager only)
# ============================================================================


@router.post(
    "/locations",
    summary="Create Attendance Location",
    tags=["Attendance"],
)
async def create_location(
    location: schemas.AttendanceLocationSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    # Only managers can create locations
    if user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only managers can create locations")

    created_location = crud.create_attendance_location(db, location, user.id)
    log_contribution(
        db, user, "CREATED", "attendance_location", created_location["location_name"]
    )
    return create_api_response(
        success=True,
        message="Attendance location created successfully",
        data=created_location,
    )


@router.get(
    "/locations",
    summary="Get All Attendance Locations",
    tags=["Attendance"],
)
async def get_all_locations(
    active_only: bool = False,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    locations = crud.get_all_attendance_locations(db, request, active_only)
    return create_api_response(
        success=True, message="Locations retrieved successfully", data=locations
    )


@router.get(
    "/locations/{id}",
    summary="Get Attendance Location",
    tags=["Attendance"],
)
async def get_location(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    location = crud.get_attendance_location(db, id)
    return create_api_response(
        success=True, message="Location retrieved successfully", data=location
    )


@router.put(
    "/locations/{id}",
    summary="Update Attendance Location",
    tags=["Attendance"],
)
async def update_location(
    id: UUID,
    location: schemas.AttendanceLocationSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    # Only managers can update locations
    if user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only managers can update locations")

    updated_location = crud.update_attendance_location(db, id, location)
    log_contribution(
        db, user, "UPDATED", "attendance_location", updated_location["location_name"]
    )
    return create_api_response(
        success=True, message="Location updated successfully", data=updated_location
    )


@router.delete(
    "/locations/{id}",
    summary="Delete Attendance Location",
    tags=["Attendance"],
)
async def delete_location(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    # Only managers can delete locations
    if user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only managers can delete locations")

    crud.delete_attendance_location(db, id)
    log_contribution(db, user, "DELETED", "attendance_location", f"id={id}")
    return create_api_response(success=True, message="Location deleted successfully")


# ============================================================================
# ATTENDANCE RECORDS
# ============================================================================


@router.post(
    "/check-in",
    summary="Check In Employee",
    tags=["Attendance"],
)
async def check_in(
    request_data: schemas.CheckInRequest,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    record = crud.check_in(db, request_data, user.id)
    log_contribution(db, user, "CREATED", "attendance_check_in", f"Location: {record['location_id']}")
    return create_api_response(
        success=True, message="Checked in successfully", data=record
    )


@router.post(
    "/check-out",
    summary="Check Out Employee",
    tags=["Attendance"],
)
async def check_out(
    request_data: schemas.CheckOutRequest,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    record = crud.check_out(db, request_data, user.id)
    log_contribution(db, user, "UPDATED", "attendance_check_out", f"Record: {record["id"]}")
    return create_api_response(
        success=True, message="Checked out successfully", data=record
    )


@router.get(
    "/records",
    summary="Get Attendance Records",
    tags=["Attendance"],
)
async def get_records(
    user_id: Optional[UUID] = None,
    location_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    # Employees can only see their own records unless they're in HR/Finance
    if not can_view_all_employees(user):
        user_id = user.id

    records = crud.get_attendance_records(
        db, request, user_id, location_id, start_date, end_date
    )
    return create_api_response(
        success=True, message="Records retrieved successfully", data=records
    )


@router.get(
    "/records/{id}",
    summary="Get Attendance Record",
    tags=["Attendance"],
)
async def get_record(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    record = crud.get_attendance_record(db, id)

    # Employees can only see their own records unless they're in HR/Finance
    if not can_view_all_employees(user) and record.user_id != user.id:
        raise HTTPException(
            status_code=403, detail="You can only view your own attendance records"
        )

    return create_api_response(
        success=True, message="Record retrieved successfully", data=record
    )


@router.get(
    "/status",
    summary="Get Current Attendance Status",
    tags=["Attendance"],
)
async def get_status(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Get the current user's active check-in status"""
    active_record = crud.get_active_check_in(db, user.id)
    return create_api_response(
        success=True,
        message="Status retrieved successfully",
        data={"active_check_in": active_record, "is_checked_in": active_record is not None},
    )
