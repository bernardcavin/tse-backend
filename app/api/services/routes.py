from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.services import crud, schemas
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.security import authorize
from app.core.utils.request import get_request

router = APIRouter(prefix="/services")


@router.post(
    "/",
    summary="Create Service",
    tags=["Service"],
)
@authorize(role=["operator", "manager", "superuser"])
async def create_service(
    service: schemas.ServiceSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.create_service(db, service)
    log_contribution(db, user, "CREATED", "service", service.name)
    return create_api_response(success=True, message="Service created successfully")


@router.get(
    "/{id}",
    summary="Get Service",
    tags=["Service"],
)
@authorize(role=["operator", "manager", "superuser"])
async def get_service(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    service = crud.get_service(db, id)
    return create_api_response(
        success=True, message="Service retrieved successfully", data=service
    )


@router.put(
    "/{id}",
    summary="Update Service",
    tags=["Service"],
)
@authorize(role=["operator", "manager", "superuser"])
async def update_service(
    id: UUID,
    service: schemas.ServiceSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_service(db, id, service)
    log_contribution(db, user, "UPDATED", "service", service.name)
    return create_api_response(success=True, message="Service updated successfully")


@router.delete(
    "/{id}",
    summary="Delete Service",
    tags=["Service"],
)
@authorize(role=["operator", "manager", "superuser"])
async def delete_service(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.delete_service(db, id)
    log_contribution(db, user, "DELETED", "service", f"id={id}")
    return create_api_response(success=True, message="Service deleted successfully")
