from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.employees import crud, schemas
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.security import authorize
from app.core.utils.request import get_request

router = APIRouter(prefix="/employees")


@router.post(
    "/",
    summary="Create Employee",
    tags=["Employee"],
)
@authorize(role=["operator", "manager", "superuser"])
async def create_employee(
    employee: schemas.EmployeeSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.create_employee(db, employee)
    log_contribution(db, user, "CREATED", "employee", employee.full_name)
    return create_api_response(success=True, message="Employee created successfully")


@router.get(
    "/{id}",
    summary="Get Employee",
    tags=["Employee"],
)
@authorize(role=["operator", "manager", "superuser"])
async def get_employee(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    employee = crud.get_employee(db, id)
    return create_api_response(
        success=True, message="Employee retrieved successfully", data=employee
    )


@router.put(
    "/{id}",
    summary="Update Employee",
    tags=["Employee"],
)
@authorize(role=["operator", "manager", "superuser"])
async def update_employee(
    id: UUID,
    employee: schemas.EmployeeSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_employee(db, id, employee)
    log_contribution(db, user, "UPDATED", "employee", employee.full_name)
    return create_api_response(success=True, message="Employee updated successfully")


@router.delete(
    "/{id}",
    summary="Delete Employee",
    tags=["Employee"],
)
@authorize(role=["operator", "manager", "superuser"])
async def delete_employee(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.delete_employee(db, id)
    log_contribution(db, user, "DELETED", "employee", f"id={id}")
    return create_api_response(success=True, message="Employee deleted successfully")
