from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.it_tickets import crud, schemas
from app.api.auth.crud import log_contribution
from app.api.auth.models import DepartmentEnum, UserRole
from app.api.auth.utils import get_current_user
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/it-tickets", tags=["IT Tickets"])


# ============================================================================
# IT TICKETS
# ============================================================================


@router.post(
    "",
    summary="Create IT Ticket",
    tags=["IT Tickets"],
)
async def create_ticket(
    ticket: schemas.ITTicketCreateSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Create a new IT ticket. All authenticated users can create tickets."""
    created_ticket = crud.create_ticket(db, ticket, user.id)
    log_contribution(
        db,
        user,
        "CREATED",
        "it_ticket",
        f"Title: {created_ticket['title']}",
    )
    return create_api_response(
        success=True,
        message="IT ticket created successfully",
        data=created_ticket,
    )


@router.get(
    "",
    summary="Get All IT Tickets",
    tags=["IT Tickets"],
)
async def get_tickets(
    facility_id: Optional[UUID] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get IT tickets with filters.
    - Regular employees can only see their own tickets
    - Managers and IT department can see all tickets
    """
    reporter_id = None
    # Regular employees can only see their own tickets
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.IT:
        reporter_id = user.id

    tickets = crud.get_tickets(
        db, request, reporter_id, facility_id, status, category, priority
    )
    return create_api_response(
        success=True, message="Tickets retrieved successfully", data=tickets
    )


@router.get(
    "/export/csv",
    summary="Export IT Tickets to CSV",
    tags=["IT Tickets"],
)
async def export_tickets_csv(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Export IT tickets data for CSV download.
    Only managers and IT employees can export all data.
    """
    reporter_id = None
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.IT:
        reporter_id = user.id

    tickets = crud.get_tickets_for_export(db, reporter_id)
    return create_api_response(
        success=True, message="Tickets exported successfully", data=tickets
    )


@router.get(
    "/analytics/summary",
    summary="Get IT Ticket Analytics",
    tags=["IT Tickets"],
)
async def get_analytics(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get IT ticket analytics.
    Only managers and IT employees can access analytics.
    """
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.IT:
        raise HTTPException(
            status_code=403,
            detail="Only managers and IT employees can access ticket analytics",
        )

    analytics = crud.get_analytics(db)
    return create_api_response(
        success=True, message="Analytics retrieved successfully", data=analytics
    )


@router.get(
    "/{id}",
    summary="Get IT Ticket",
    tags=["IT Tickets"],
)
async def get_ticket(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get a specific IT ticket.
    - Regular employees can only view their own tickets
    - Managers and IT employees can view any ticket
    """
    ticket = crud.get_ticket(db, id)

    # Regular employees can only see their own tickets
    if (
        user.role != UserRole.MANAGER
        and user.department != DepartmentEnum.IT
        and ticket["reporter_id"] != str(user.id)
    ):
        raise HTTPException(
            status_code=403, detail="You can only view your own tickets"
        )

    return create_api_response(
        success=True, message="Ticket retrieved successfully", data=ticket
    )


@router.put(
    "/{id}",
    summary="Update IT Ticket",
    tags=["IT Tickets"],
)
async def update_ticket(
    id: UUID,
    ticket: schemas.ITTicketUpdateSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Update an IT ticket.
    - Regular employees can only update their own tickets
    - Managers and IT employees can update any ticket
    """
    existing_ticket = crud.get_ticket(db, id)

    # Regular employees can only update their own tickets
    if (
        user.role != UserRole.MANAGER
        and user.department != DepartmentEnum.IT
        and existing_ticket["reporter_id"] != str(user.id)
    ):
        raise HTTPException(
            status_code=403, detail="You can only update your own tickets"
        )

    updated_ticket = crud.update_ticket(db, id, ticket)
    log_contribution(db, user, "UPDATED", "it_ticket", f"ID: {id}")
    return create_api_response(
        success=True,
        message="Ticket updated successfully",
        data=updated_ticket,
    )


@router.put(
    "/{id}/assign",
    summary="Assign IT Ticket",
    tags=["IT Tickets"],
)
async def assign_ticket(
    id: UUID,
    assignment: schemas.ITTicketAssignSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Assign an IT ticket to a staff member.
    Managers and IT department employees can assign tickets.
    """
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.IT:
        raise HTTPException(
            status_code=403,
            detail="Only managers and IT department employees can assign tickets",
        )

    assigned_ticket = crud.assign_ticket(db, id, assignment)
    log_contribution(db, user, "ASSIGNED", "it_ticket", f"ID: {id}")
    return create_api_response(
        success=True,
        message="Ticket assigned successfully",
        data=assigned_ticket,
    )


@router.put(
    "/{id}/resolve",
    summary="Resolve IT Ticket",
    tags=["IT Tickets"],
)
async def resolve_ticket(
    id: UUID,
    resolution: schemas.ITTicketResolveSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Resolve an IT ticket.
    Managers and IT department employees can resolve tickets.
    """
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.IT:
        raise HTTPException(
            status_code=403,
            detail="Only managers and IT department employees can resolve tickets",
        )

    resolved_ticket = crud.resolve_ticket(db, id, resolution, user.id)
    log_contribution(db, user, "RESOLVED", "it_ticket", f"ID: {id}")
    return create_api_response(
        success=True,
        message="Ticket resolved successfully",
        data=resolved_ticket,
    )


@router.delete(
    "/{id}",
    summary="Delete IT Ticket",
    tags=["IT Tickets"],
)
async def delete_ticket(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Delete an IT ticket.
    - Employees can delete their own tickets if status is still open
    - Managers can delete any ticket
    """
    existing_ticket = crud.get_ticket(db, id)

    # Check if user is the owner or a manager
    is_owner = existing_ticket["reporter_id"] == str(user.id)
    is_manager = user.role == UserRole.MANAGER

    if not is_owner and not is_manager:
        raise HTTPException(
            status_code=403, detail="You can only delete your own tickets"
        )

    # Employees can only delete open tickets
    if is_owner and not is_manager:
        if existing_ticket["status"] != "open":
            raise HTTPException(
                status_code=403,
                detail="Cannot delete tickets that are not open. Only managers can delete non-open tickets."
            )

    crud.delete_ticket(db, id)
    log_contribution(db, user, "DELETED", "it_ticket", f"ID: {id}")
    return create_api_response(success=True, message="Ticket deleted successfully")

