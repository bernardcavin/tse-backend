from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.appointments import crud, schemas
from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.security import authorize
from app.core.utils.request import get_request

router = APIRouter(prefix="/appointments")


@router.post(
    "/",
    summary="Create Appointment",
    tags=["Appointment"],
)
@authorize(role=["operator", "manager", "superuser"])
async def create_appointment(
    appointment: schemas.AppointmentSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.create_appointment(db, appointment)
    log_contribution(db, user, "CREATED", "appointment")
    return create_api_response(success=True, message="Appointment created successfully")


@router.get(
    "/{id}",
    summary="Get Appointment",
    tags=["Appointment"],
)
@authorize(role=["operator", "manager", "superuser"])
async def get_appointment(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    appointment = crud.get_appointment(db, id)
    return create_api_response(
        success=True, message="Appointment retrieved successfully", data=appointment
    )


@router.put(
    "/{id}",
    summary="Update Appointment",
    tags=["Appointment"],
)
@authorize(role=["operator", "manager", "superuser"])
async def update_appointment(
    id: UUID,
    appointment: schemas.AppointmentSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_appointment(db, id, appointment)
    log_contribution(db, user, "UPDATED", "appointment")
    return create_api_response(success=True, message="Appointment updated successfully")


@router.delete(
    "/{id}",
    summary="Delete Appointment",
    tags=["Appointment"],
)
@authorize(role=["operator", "manager", "superuser"])
async def delete_appointment(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.delete_appointment(db, id)
    log_contribution(db, user, "DELETED", "appointment", f"id={id}")
    return create_api_response(success=True, message="Appointment deleted successfully")
