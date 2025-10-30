from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.customers import crud, schemas
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.security import authorize
from app.core.utils.request import get_request

router = APIRouter(prefix="/customers")


@router.post(
    "/",
    summary="Create Customer",
    tags=["Customer"],
)
@authorize(role=["operator", "manager", "superuser"])
async def create_customer(
    customer: schemas.CustomerSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.create_customer(db, customer)
    log_contribution(db, user, "CREATED", "customer", customer.full_name)
    return create_api_response(success=True, message="Customer created successfully")


@router.get(
    "/{id}",
    summary="Get Customer",
    tags=["Customer"],
)
@authorize(role=["operator", "manager", "superuser"])
async def get_customer(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    customer = crud.get_customer(db, id)
    return create_api_response(
        success=True, message="Customer retrieved successfully", data=customer
    )


@router.put(
    "/{id}",
    summary="Update Customer",
    tags=["Customer"],
)
@authorize(role=["operator", "manager", "superuser"])
async def update_customer(
    id: UUID,
    customer: schemas.CustomerSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_customer(db, id, customer)
    log_contribution(db, user, "UPDATED", "customer", customer.full_name)
    return create_api_response(success=True, message="Customer updated successfully")


@router.delete(
    "/{id}",
    summary="Delete Customer",
    tags=["Customer"],
)
@authorize(role=["operator", "manager", "superuser"])
async def delete_customer(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.delete_customer(db, id)
    log_contribution(db, user, "DELETED", "customer", f"id={id}")
    return create_api_response(success=True, message="Customer deleted successfully")
