from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.safety_observations import crud, schemas
from app.api.auth.crud import log_contribution
from app.api.auth.models import DepartmentEnum, UserRole
from app.api.auth.utils import get_current_user
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/safety-observations", tags=["Safety Observations"])


# ============================================================================
# SAFETY OBSERVATIONS
# ============================================================================


@router.post(
    "",
    summary="Create Safety Observation",
    tags=["Safety Observations"],
)
async def create_observation(
    observation: schemas.SafetyObservationCreateSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Create a new safety observation. All authenticated users can create observations."""
    created_observation = crud.create_observation(db, observation, user.id)
    log_contribution(
        db,
        user,
        "CREATED",
        "safety_observation",
        f"Facility: {created_observation['facility_id']}",
    )
    return create_api_response(
        success=True,
        message="Safety observation created successfully",
        data=created_observation,
    )


@router.get(
    "",
    summary="Get All Safety Observations",
    tags=["Safety Observations"],
)
async def get_observations(
    facility_id: Optional[UUID] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get safety observations with filters.
    - Employees (non-HSE) can only see their own observations
    - Managers and HSE employees can see all observations
    """
    observer_id = None
    # Non-HSE employees can only see their own observations
    # Managers and HSE employees can see all
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.HSE:
        observer_id = user.id

    observations = crud.get_observations(
        db, request, observer_id, facility_id, status, start_date, end_date
    )
    return create_api_response(
        success=True, message="Observations retrieved successfully", data=observations
    )


@router.get(
    "/{id}",
    summary="Get Safety Observation",
    tags=["Safety Observations"],
)
async def get_observation(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get a specific safety observation.
    - Employees (non-HSE) can only view their own observations
    - Managers and HSE employees can view any observation
    """
    observation = crud.get_observation(db, id)

    # Non-HSE employees can only see their own observations
    if (
        user.role != UserRole.MANAGER
        and user.department != DepartmentEnum.HSE
        and observation["observer_id"] != str(user.id)
    ):
        raise HTTPException(
            status_code=403, detail="You can only view your own safety observations"
        )

    return create_api_response(
        success=True, message="Observation retrieved successfully", data=observation
    )


@router.put(
    "/{id}",
    summary="Update Safety Observation",
    tags=["Safety Observations"],
)
async def update_observation(
    id: UUID,
    observation: schemas.SafetyObservationUpdateSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Update a safety observation.
    - Employees can only update their own observations
    - Managers can update any observation
    """
    existing_observation = crud.get_observation(db, id)

    # Employees can only update their own observations
    if user.role != UserRole.MANAGER and existing_observation["observer_id"] != str(
        user.id
    ):
        raise HTTPException(
            status_code=403, detail="You can only update your own safety observations"
        )

    updated_observation = crud.update_observation(db, id, observation)
    log_contribution(db, user, "UPDATED", "safety_observation", f"ID: {id}")
    return create_api_response(
        success=True,
        message="Observation updated successfully",
        data=updated_observation,
    )


@router.delete(
    "/{id}",
    summary="Delete Safety Observation",
    tags=["Safety Observations"],
)
async def delete_observation(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Delete a safety observation.
    - Employees can delete their own observations if not resolved
    - Managers can delete any observation
    """
    existing_observation = crud.get_observation(db, id)

    # Check if user is the owner or a manager
    is_owner = existing_observation["observer_id"] == str(user.id)
    is_manager = user.role == UserRole.MANAGER

    if not is_owner and not is_manager:
        raise HTTPException(
            status_code=403, detail="You can only delete your own safety observations"
        )

    # Employees can only delete unresolved observations
    if is_owner and not is_manager:
        if existing_observation["status"] in ["resolved", "closed"]:
            raise HTTPException(
                status_code=403,
                detail="Cannot delete resolved/closed observations. Only managers can delete resolved/closed observations."
            )

    crud.delete_observation(db, id)
    log_contribution(db, user, "DELETED", "safety_observation", f"ID: {id}")
    return create_api_response(
        success=True, message="Observation deleted successfully"
    )


@router.put(
    "/{id}/resolve",
    summary="Resolve Safety Observation",
    tags=["Safety Observations"],
)
async def resolve_observation(
    id: UUID,
    resolution: schemas.SafetyObservationResolveSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Resolve a safety observation.
    Managers and HSE department employees can resolve observations.
    """
    # Managers and HSE department can resolve Safetys
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.HSE:
        raise HTTPException(
            status_code=403,
            detail="Only managers and HSE department employees can resolve safety observations",
        )

    resolved_observation = crud.resolve_observation(db, id, resolution, user.id)
    log_contribution(db, user, "RESOLVED", "safety_observation", f"ID: {id}")
    return create_api_response(
        success=True,
        message="Observation resolved successfully",
        data=resolved_observation,
    )


@router.put(
    "/{id}/close",
    summary="Close Safety Observation",
    tags=["Safety Observations"],
)
async def close_observation(
    id: UUID,
    close_data: schemas.SafetyObservationCloseSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Close an invalid safety observation.
    Managers and HSE department employees can close observations.
    """
    # Managers and HSE department can close Safetys
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.HSE:
        raise HTTPException(
            status_code=403,
            detail="Only managers and HSE department employees can close safety observations",
        )

    closed_observation = crud.close_observation(db, id, close_data, user.id)
    log_contribution(db, user, "CLOSED", "safety_observation", f"ID: {id}")
    return create_api_response(
        success=True,
        message="Observation closed successfully",
        data=closed_observation,
    )


@router.get(
    "/export/csv",
    summary="Export Safety Observations to CSV",
    tags=["Safety Observations"],
)
async def export_observations_csv(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Export all safety observations data for CSV download.
    Only managers and HSE employees can export all data.
    """
    observer_id = None
    # Non-HSE employees can only export their own observations
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.HSE:
        observer_id = user.id

    observations = crud.get_observations_for_export(db, observer_id)
    return create_api_response(
        success=True, message="Observations exported successfully", data=observations
    )


@router.get(
    "/analytics/summary",
    summary="Get Safety Observation Analytics",
    tags=["Safety Observations"],
)
async def get_analytics(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get safety observation analytics.
    Only managers and HSE employees can access analytics.
    """
    # Only managers and HSE employees can access analytics
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.HSE:
        raise HTTPException(
            status_code=403,
            detail="Only managers and HSE employees can access safety analytics",
        )

    analytics = crud.get_analytics(db)
    return create_api_response(
        success=True, message="Analytics retrieved successfully", data=analytics
    )
