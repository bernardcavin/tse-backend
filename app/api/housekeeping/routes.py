from typing import Optional
from uuid import UUID

from app.api.auth.crud import log_contribution
from app.api.auth.models import DepartmentEnum, UserRole
from app.api.auth.utils import get_current_user
from app.api.housekeeping import crud, schemas
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/housekeeping", tags=["Housekeeping"])


# ============================================================================
# HOUSEKEEPING CHECKLISTS
# ============================================================================


@router.post(
    "",
    summary="Create Housekeeping Checklist",
    tags=["Housekeeping"],
)
async def create_housekeeping(
    housekeeping: schemas.HousekeepingCreateSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Create a new housekeeping checklist.
    Only HSE department and managers can create checklists.
    """
    if user.department != DepartmentEnum.HSE and user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=403,
            detail="Only HSE department and managers can create housekeeping checklists",
        )

    created_housekeeping = crud.create_housekeeping(db, housekeeping, user.id)
    log_contribution(
        db,
        user,
        "CREATED",
        "housekeeping",
        f"Location: {created_housekeeping['location_area']}",
    )
    return create_api_response(
        success=True,
        message="Housekeeping checklist created successfully",
        data=created_housekeeping,
    )


@router.get(
    "",
    summary="Get All Housekeeping Checklists",
    tags=["Housekeeping"],
)
async def get_housekeeping_list(
    facility_id: Optional[UUID] = None,
    inspector_id: Optional[UUID] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get housekeeping checklists with filters.
    All authenticated users can view checklists.
    """
    # All employees can view housekeeping checklists
    housekeeping_list = crud.get_housekeeping_list(
        db, request
    )
    return create_api_response(
        success=True,
        message="Housekeeping checklists retrieved successfully",
        data=housekeeping_list,
    )


@router.get(
    "/export/csv",
    summary="Export Housekeeping Checklists to CSV",
    tags=["Housekeeping"],
)
async def export_housekeeping_csv(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Export housekeeping checklists data for CSV download.
    Only managers can export data.
    """
    if user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=403,
            detail="Only managers can export housekeeping data",
        )

    housekeeping_list = crud.get_housekeeping_for_export(db)
    return create_api_response(
        success=True,
        message="Housekeeping checklists exported successfully",
        data=housekeeping_list,
    )


@router.get(
    "/analytics/summary",
    summary="Get Housekeeping Analytics",
    tags=["Housekeeping"],
)
async def get_analytics(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get housekeeping analytics.
    Only managers can access analytics.
    """
    if user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=403,
            detail="Only managers can access housekeeping analytics",
        )

    analytics = crud.get_analytics(db)
    return create_api_response(
        success=True,
        message="Analytics retrieved successfully",
        data=analytics,
    )


@router.get(
    "/{id}",
    summary="Get Housekeeping Checklist",
    tags=["Housekeeping"],
)
async def get_housekeeping(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get a specific housekeeping checklist.
    All authenticated users can view checklists.
    """
    # All employees can view housekeeping checklists
    housekeeping = crud.get_housekeeping(db, id)
    return create_api_response(
        success=True,
        message="Housekeeping checklist retrieved successfully",
        data=housekeeping,
    )


@router.put(
    "/{id}",
    summary="Update Housekeeping Checklist",
    tags=["Housekeeping"],
)
async def update_housekeeping(
    id: UUID,
    housekeeping: schemas.HousekeepingUpdateSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Update a housekeeping checklist.
    Only managers can update checklists.
    """
    if user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=403,
            detail="Only managers can update housekeeping checklists",
        )

    updated_housekeeping = crud.update_housekeeping(db, id, housekeeping)
    log_contribution(db, user, "UPDATED", "housekeeping", f"ID: {id}")
    return create_api_response(
        success=True,
        message="Housekeeping checklist updated successfully",
        data=updated_housekeeping,
    )


@router.delete(
    "/{id}",
    summary="Delete Housekeeping Checklist",
    tags=["Housekeeping"],
)
async def delete_housekeeping(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Delete a housekeeping checklist.
    Only managers can delete checklists.
    """
    if user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=403,
            detail="Only managers can delete housekeeping checklists",
        )

    crud.delete_housekeeping(db, id)
    log_contribution(db, user, "DELETED", "housekeeping", f"ID: {id}")
    return create_api_response(
        success=True,
        message="Housekeeping checklist deleted successfully",
    )
