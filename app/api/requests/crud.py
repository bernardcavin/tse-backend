from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.auth.models import DepartmentEnum, User, UserRole
from app.api.requests.models import Request, RequestStatus
from app.api.requests.schemas import (
    RequestCreateSchema,
    RequestSchema,
    RequestUpdateSchema,
)
from app.utils.filter_utils import get_paginated_data


def get_requests(
    db: Session,
    request,
    user: User,
    status_filter: Optional[RequestStatus] = None,
) -> dict:
    query = db.query(Request)

    # Filter based on role
    # Manager and Finance can see all (or filter by department if needed)
    # Employees can only see their own
    if user.role != UserRole.MANAGER and user.department != DepartmentEnum.FINANCE:
        query = query.filter(Request.employee_id == user.id)

    if status_filter:
        query = query.filter(Request.status == status_filter)

    # Use standard pagination utility
    result = get_paginated_data(
        db, request, Request, RequestSchema, "created_at", base_query=query
    )
    
    # Enrich with names
    if result and "data" in result:
        employee_ids = {req["employee_id"] for req in result["data"] if req.get("employee_id")}
        manager_ids = {req["manager_id"] for req in result["data"] if req.get("manager_id")}
        finance_ids = {req["finance_id"] for req in result["data"] if req.get("finance_id")}
        
        all_user_ids = employee_ids | manager_ids | finance_ids
        users = db.query(User).filter(User.id.in_(all_user_ids)).all()
        user_map = {str(u.id): u.name for u in users}
        
        for req in result["data"]:
            req["employee_name"] = user_map.get(req.get("employee_id"))
            req["manager_name"] = user_map.get(req.get("manager_id"))
            req["finance_name"] = user_map.get(req.get("finance_id"))

    return result


def get_request(db: Session, request_id: UUID) -> RequestSchema:
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    # Enrich with names
    result = RequestSchema.model_validate(db_request).model_dump(mode="json")
    
    employee = db.query(User).filter(User.id == db_request.employee_id).first()
    result["employee_name"] = employee.name if employee else None
    
    if db_request.manager_id:
        manager = db.query(User).filter(User.id == db_request.manager_id).first()
        result["manager_name"] = manager.name if manager else None
        
    if db_request.finance_id:
        finance = db.query(User).filter(User.id == db_request.finance_id).first()
        result["finance_name"] = finance.name if finance else None
        
    return result


def create_request(db: Session, request: RequestCreateSchema, user_id: UUID) -> RequestSchema:
    request_dict = request.model_dump(exclude_unset=True)
    request_dict["employee_id"] = user_id
    request_dict["status"] = RequestStatus.PENDING
    
    # Calculate estimated cost from items if provided and cost is not manually set (or override it?)
    # User requirement: "add multiple items also with it's costs". 
    # Usually total cost is sum of items.
    if request.items:
        # Convert Pydantic models to dicts for JSON storage
        request_dict["items"] = [item.model_dump() for item in request.items]
        # Auto-calculate estimated cost
        request_dict["estimated_cost"] = sum(item.cost for item in request.items)
    
    db_request = Request(**request_dict)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    result = RequestSchema.model_validate(db_request).model_dump(mode="json")
    user = db.query(User).filter(User.id == user_id).first()
    result["employee_name"] = user.name if user else None
    
    return result


def update_request(
    db: Session, request_id: UUID, request_update: RequestUpdateSchema
) -> RequestSchema:
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")

    update_data = request_update.model_dump(exclude_unset=True)
    
    # Handle items update
    if "items" in update_data:
        # Convert to dicts
        update_data["items"] = [item.model_dump() if hasattr(item, "model_dump") else item for item in update_data["items"]]
        # Recalculate cost
        update_data["estimated_cost"] = sum(item["cost"] for item in update_data["items"])

    for key, value in update_data.items():
        setattr(db_request, key, value)

    db.commit()
    db.refresh(db_request)
    return get_request(db, request_id)


def delete_request(db: Session, request_id: UUID):
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")

    db.delete(db_request)
    db.commit()


# Status Transitions

def approve_request(db: Session, request_id: UUID, user_id: UUID) -> RequestSchema:
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if db_request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request must be pending to approve")

    db_request.status = RequestStatus.APPROVED
    db_request.manager_id = user_id
    db.commit()
    db.refresh(db_request)
    return get_request(db, request_id)


def reject_request(db: Session, request_id: UUID, reason: str, user_id: UUID) -> RequestSchema:
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if db_request.status != RequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request must be pending to reject")

    db_request.status = RequestStatus.REJECTED
    db_request.rejection_reason = reason
    db_request.manager_id = user_id
    db.commit()
    db.refresh(db_request)
    return get_request(db, request_id)


def transfer_request(
    db: Session, request_id: UUID, proof_file_ids: List[UUID], user_id: UUID
) -> RequestSchema:
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if db_request.status != RequestStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Request must be approved to transfer")

    db_request.status = RequestStatus.TRANSFERRED
    db_request.transfer_proof_file_ids = proof_file_ids
    db_request.finance_id = user_id
    db.commit()
    db.refresh(db_request)
    return get_request(db, request_id)


def report_request(
    db: Session, request_id: UUID, actual_cost: float, receipt_file_ids: List[UUID]
) -> RequestSchema:
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if db_request.status != RequestStatus.TRANSFERRED:
        raise HTTPException(status_code=400, detail="Request must be transferred to report")

    db_request.status = RequestStatus.REPORTED
    db_request.actual_cost = actual_cost
    db_request.receipt_file_ids = receipt_file_ids
    db.commit()
    db.refresh(db_request)
    return get_request(db, request_id)


def complete_request(db: Session, request_id: UUID) -> RequestSchema:
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if db_request.status != RequestStatus.REPORTED:
        raise HTTPException(status_code=400, detail="Request must be reported to complete")

    db_request.status = RequestStatus.DONE
    db.commit()
    db.refresh(db_request)
    return get_request(db, request_id)


def cancel_request(db: Session, request_id: UUID) -> RequestSchema:
    db_request = db.query(Request).filter(Request.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")

    db_request.status = RequestStatus.CANCELLED
    db.commit()
    db.refresh(db_request)
    return get_request(db, request_id)
