from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.models import DepartmentEnum, UserRole
from app.api.auth.utils import get_current_user
from app.api.requests import crud
from app.api.requests.models import RequestStatus
from app.api.requests.schemas import (
    RequestActionSchema,
    RequestCreateSchema,
    RequestUpdateSchema,
)
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/requests", tags=["Requests"])


@router.get(
    "",
    summary="Get All Requests",
    tags=["Requests"],
)
def get_requests(
    status: Optional[RequestStatus] = Query(None),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get requests with filters.
    - Employees can only see their own requests
    - Managers and Finance can see all requests
    """
    requests = crud.get_requests(db, request, user, status)
    return create_api_response(
        success=True, message="Requests retrieved successfully", data=requests
    )


@router.post(
    "",
    summary="Create Request",
    tags=["Requests"],
)
def create_request(
    request_data: RequestCreateSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Create a new request."""
    created_request = crud.create_request(db, request_data, user.id)
    log_contribution(
        db,
        user,
        "CREATED",
        "request",
        f"Purpose: {created_request['purpose']}",
    )
    return create_api_response(
        success=True,
        message="Request created successfully",
        data=created_request,
    )


@router.get(
    "/{request_id}",
    summary="Get Request",
    tags=["Requests"],
)
def get_request_details(
    request_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Get a specific request.
    - Employees can only view their own requests
    - Managers and Finance can view any request
    """
    req = crud.get_request(db, request_id)

    # Access control
    if (
        user.role != UserRole.MANAGER
        and user.department != DepartmentEnum.FINANCE
        and req["employee_id"] != str(user.id)
    ):
        raise HTTPException(
            status_code=403, detail="You can only view your own requests"
        )

    return create_api_response(
        success=True, message="Request retrieved successfully", data=req
    )


@router.put(
    "/{request_id}",
    summary="Update Request",
    tags=["Requests"],
)
def update_request(
    request_id: UUID,
    request_update: RequestUpdateSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Update a request.
    - Only the requester can update the request
    - Only pending requests can be updated
    """
    req = crud.get_request(db, request_id)
    
    if req["employee_id"] != str(user.id):
         raise HTTPException(
            status_code=403, detail="Only the requester can update the request"
        )
        
    if req["status"] != RequestStatus.PENDING:
        raise HTTPException(
            status_code=400, detail="Only pending requests can be updated"
        )

    updated_request = crud.update_request(db, request_id, request_update)
    log_contribution(db, user, "UPDATED", "request", f"ID: {request_id}")
    return create_api_response(
        success=True,
        message="Request updated successfully",
        data=updated_request,
    )


@router.delete(
    "/{request_id}",
    summary="Delete Request",
    tags=["Requests"],
)
def delete_request(
    request_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """
    Delete a request.
    - Only the requester can delete the request
    - Only pending requests can be deleted
    """
    req = crud.get_request(db, request_id)
    
    # Check if user is the owner or a manager (Managers can delete any? Let's say yes for now, similar to other modules)
    is_owner = req["employee_id"] == str(user.id)
    is_manager = user.role == UserRole.MANAGER
    
    if not is_owner and not is_manager:
         raise HTTPException(
            status_code=403, detail="You can only delete your own requests"
        )
        
    if is_owner and not is_manager:
        if req["status"] != RequestStatus.PENDING:
            raise HTTPException(
                status_code=400, detail="Only pending requests can be deleted"
            )

    crud.delete_request(db, request_id)
    log_contribution(db, user, "DELETED", "request", f"ID: {request_id}")
    return create_api_response(success=True, message="Request deleted successfully")


@router.post(
    "/{request_id}/action",
    summary="Perform Request Action",
    tags=["Requests"],
)
def perform_request_action(
    request_id: UUID,
    action_data: RequestActionSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    action = action_data.action.lower()
    
    if action == "approve":
        if user.role != UserRole.MANAGER and user.department != DepartmentEnum.FINANCE:
            raise HTTPException(status_code=403, detail="Not authorized to approve requests")
        result = crud.approve_request(db, request_id, user.id)
        log_contribution(db, user, "APPROVED", "request", f"ID: {request_id}")
        
    elif action == "reject":
        if user.role != UserRole.MANAGER and user.department != DepartmentEnum.FINANCE:
            raise HTTPException(status_code=403, detail="Not authorized to reject requests")
        if not action_data.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        result = crud.reject_request(db, request_id, action_data.rejection_reason, user.id)
        log_contribution(db, user, "REJECTED", "request", f"ID: {request_id}")
        
    elif action == "transfer":
        if user.department != DepartmentEnum.FINANCE and user.role != UserRole.MANAGER:
            # Strict: Only Finance
             if user.department != DepartmentEnum.FINANCE:
                 raise HTTPException(status_code=403, detail="Only Finance can mark as transferred")
        
        # Transfer proof is optional
        result = crud.transfer_request(db, request_id, action_data.transfer_proof_file_ids or [], user.id)
        log_contribution(db, user, "TRANSFERRED", "request", f"ID: {request_id}")
        
    elif action == "report":
        # Check ownership
        req = crud.get_request(db, request_id)
        if req["employee_id"] != str(user.id):
            raise HTTPException(status_code=403, detail="Only the requester can report expenses")
            
        if action_data.actual_cost is None or not action_data.receipt_file_ids:
            raise HTTPException(status_code=400, detail="Actual cost and receipt are required")
        result = crud.report_request(db, request_id, action_data.actual_cost, action_data.receipt_file_ids)
        log_contribution(db, user, "REPORTED", "request", f"ID: {request_id}")
        
    elif action == "done":
        if user.role != UserRole.MANAGER and user.department != DepartmentEnum.FINANCE:
            raise HTTPException(status_code=403, detail="Not authorized to complete requests")
        result = crud.complete_request(db, request_id)
        log_contribution(db, user, "COMPLETED", "request", f"ID: {request_id}")
        
    elif action == "cancel":
        req = crud.get_request(db, request_id)
        # Allow requester to cancel if pending
        if req["status"] == RequestStatus.PENDING and req["employee_id"] == str(user.id):
            pass
        # Allow manager/finance to cancel anytime
        elif user.role == UserRole.MANAGER or user.department == DepartmentEnum.FINANCE:
            pass
        else:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this request")
            
        result = crud.cancel_request(db, request_id)
        log_contribution(db, user, "CANCELLED", "request", f"ID: {request_id}")
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
        
    return create_api_response(
        success=True,
        message=f"Request {action} successful",
        data=result,
    )
