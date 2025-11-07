from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.facilities import crud, schemas
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/facilities")


@router.get(
    "/",
    summary="Get All Facilitys",
    tags=["Facility"],
)
async def get_all_services(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    facilities = crud.get_all_facilities(db, request)
    return create_api_response(
        success=True, message="Facilitys retrieved successfully", data=facilities
    )


@router.post(
    "/",
    summary="Create Facility",
    tags=["Facility"],
)
async def create_facility(
    facility: schemas.FacilitySchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.create_facility(db, facility)
    log_contribution(db, user, "CREATED", "facility", facility.facility_name)
    return create_api_response(success=True, message="Facility created successfully")


@router.get(
    "/{id}",
    summary="Get Facility",
    tags=["Facility"],
)
async def get_facility(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    facility = crud.get_facility(db, id)
    return create_api_response(
        success=True, message="Facility retrieved successfully", data=facility
    )


@router.put(
    "/{id}",
    summary="Update Facility",
    tags=["Facility"],
)
async def update_facility(
    id: UUID,
    facility: schemas.FacilitySchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_facility(db, id, facility)
    log_contribution(db, user, "UPDATED", "facility", facility.facility_name)
    return create_api_response(success=True, message="Facility updated successfully")


@router.delete(
    "/{id}",
    summary="Delete Facility",
    tags=["Facility"],
)
async def delete_facility(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.delete_facility(db, id)
    log_contribution(db, user, "DELETED", "facility", f"id={id}")
    return create_api_response(success=True, message="Facility deleted successfully")


@router.get(
    "/utils/options",
    summary="Get Facility Options",
    tags=["Facility"],
)
async def get_facility_options(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    options = crud.get_facilities_options(db)
    return create_api_response(
        success=True, message="Facility options retrieved successfully", data=options
    )


@router.get(
    "/{id}/coordinates",
    summary="Get Facility Coordinates",
    tags=["Facility"],
)
async def get_facility_coordinates(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    coordinates = crud.get_facility_coordinates(db, id)
    return create_api_response(
        success=True,
        message="Facility coordinates retrieved successfully",
        data=coordinates,
    )
