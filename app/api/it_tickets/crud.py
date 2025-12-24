from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.it_tickets.models import ITTicket, TicketStatus
from app.api.it_tickets.schemas import (
    ITTicketAssignSchema,
    ITTicketCreateSchema,
    ITTicketResolveSchema,
    ITTicketSchema,
    ITTicketUpdateSchema,
)
from app.utils.filter_utils import get_paginated_data


def create_ticket(
    db: Session, ticket: ITTicketCreateSchema, reporter_id: UUID
) -> ITTicketSchema:
    """Create a new IT ticket"""
    ticket_dict = ticket.model_dump(exclude_unset=True)
    ticket_dict["reporter_id"] = reporter_id

    db_ticket = ITTicket(**ticket_dict)
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)

    return ITTicketSchema.model_validate(db_ticket).model_dump(mode="json")


def get_ticket(db: Session, ticket_id: UUID) -> ITTicketSchema:
    """Get a single IT ticket by ID with related names"""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility
    from app.api.inventory.models import Inventory

    ticket = db.query(ITTicket).filter(ITTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="IT ticket not found")

    # Get related names
    facility = None
    if ticket.facility_id:
        facility = db.query(Facility).filter(Facility.id == ticket.facility_id).first()

    reporter = db.query(User).filter(User.id == ticket.reporter_id).first()

    inventory_item = None
    if ticket.inventory_item_id:
        inventory_item = db.query(Inventory).filter(Inventory.id == ticket.inventory_item_id).first()

    assigned_to = None
    if ticket.assigned_to_id:
        assigned_to = db.query(User).filter(User.id == ticket.assigned_to_id).first()

    resolved_by = None
    if ticket.resolved_by_id:
        resolved_by = db.query(User).filter(User.id == ticket.resolved_by_id).first()

    # Convert to dict and add names
    result = ITTicketSchema.model_validate(ticket).model_dump(mode="json")
    result["facility_name"] = facility.facility_name if facility else None
    result["reporter_name"] = reporter.name if reporter else None
    result["inventory_item_name"] = inventory_item.item_name if inventory_item else None
    result["assigned_to_name"] = assigned_to.name if assigned_to else None
    result["resolved_by_name"] = resolved_by.name if resolved_by else None

    return result


def get_tickets(
    db: Session,
    request,
    reporter_id: Optional[UUID] = None,
    facility_id: Optional[UUID] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
) -> dict:
    """Get all IT tickets with filtering and pagination"""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility
    from app.api.inventory.models import Inventory

    query = db.query(ITTicket)

    # Apply filters
    if reporter_id:
        query = query.filter(ITTicket.reporter_id == reporter_id)
    if facility_id:
        query = query.filter(ITTicket.facility_id == facility_id)
    if status:
        query = query.filter(ITTicket.status == status)
    if category:
        query = query.filter(ITTicket.category == category)
    if priority:
        query = query.filter(ITTicket.priority == priority)

    # Use standard pagination utility
    result = get_paginated_data(
        db, request, ITTicket, ITTicketSchema, "created_at"
    )

    # Enrich each ticket with related names
    if result and "data" in result:
        facility_ids = {t["facility_id"] for t in result["data"] if t.get("facility_id")}
        reporter_ids = {t["reporter_id"] for t in result["data"] if t.get("reporter_id")}
        inventory_ids = {t["inventory_item_id"] for t in result["data"] if t.get("inventory_item_id")}
        assigned_ids = {t["assigned_to_id"] for t in result["data"] if t.get("assigned_to_id")}
        resolver_ids = {t["resolved_by_id"] for t in result["data"] if t.get("resolved_by_id")}

        # Fetch in bulk
        facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all() if facility_ids else []
        users = db.query(User).filter(User.id.in_(reporter_ids | assigned_ids | resolver_ids)).all()
        inventory_items = db.query(Inventory).filter(Inventory.id.in_(inventory_ids)).all() if inventory_ids else []

        # Create lookup dictionaries
        facility_map = {str(f.id): f.facility_name for f in facilities}
        user_map = {str(u.id): u.name for u in users}
        inventory_map = {str(i.id): i.item_name for i in inventory_items}

        # Add names to each ticket
        for t in result["data"]:
            t["facility_name"] = facility_map.get(t.get("facility_id"))
            t["reporter_name"] = user_map.get(t.get("reporter_id"))
            t["inventory_item_name"] = inventory_map.get(t.get("inventory_item_id"))
            t["assigned_to_name"] = user_map.get(t.get("assigned_to_id"))
            t["resolved_by_name"] = user_map.get(t.get("resolved_by_id"))

    return result


def update_ticket(
    db: Session, ticket_id: UUID, ticket: ITTicketUpdateSchema
) -> ITTicketSchema:
    """Update an IT ticket"""
    db_ticket = db.query(ITTicket).filter(ITTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="IT ticket not found")

    update_data = ticket.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_ticket, key, value)

    db.commit()
    db.refresh(db_ticket)
    return ITTicketSchema.model_validate(db_ticket).model_dump(mode="json")


def assign_ticket(
    db: Session, ticket_id: UUID, assignment: ITTicketAssignSchema
) -> ITTicketSchema:
    """Assign an IT ticket to a staff member"""
    db_ticket = db.query(ITTicket).filter(ITTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="IT ticket not found")

    db_ticket.assigned_to_id = assignment.assigned_to_id
    if db_ticket.status == TicketStatus.OPEN:
        db_ticket.status = TicketStatus.IN_PROGRESS

    db.commit()
    db.refresh(db_ticket)
    return ITTicketSchema.model_validate(db_ticket).model_dump(mode="json")


def resolve_ticket(
    db: Session,
    ticket_id: UUID,
    resolution: ITTicketResolveSchema,
    resolved_by_id: UUID,
) -> ITTicketSchema:
    """Resolve an IT ticket"""
    db_ticket = db.query(ITTicket).filter(ITTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="IT ticket not found")

    if db_ticket.status == TicketStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Ticket is already resolved")

    db_ticket.status = TicketStatus.RESOLVED
    db_ticket.resolved_by_id = resolved_by_id
    db_ticket.resolved_at = datetime.utcnow()
    db_ticket.resolution_notes = resolution.resolution_notes

    db.commit()
    db.refresh(db_ticket)
    return ITTicketSchema.model_validate(db_ticket).model_dump(mode="json")


def delete_ticket(db: Session, ticket_id: UUID) -> None:
    """Delete an IT ticket"""
    db_ticket = db.query(ITTicket).filter(ITTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="IT ticket not found")

    db.delete(db_ticket)
    db.commit()


def get_analytics(db: Session) -> dict:
    """Get analytics for IT tickets"""
    from sqlalchemy import func

    # Total tickets
    total = db.query(ITTicket).count()

    # Status breakdown
    status_counts = (
        db.query(ITTicket.status, func.count(ITTicket.id).label("count"))
        .group_by(ITTicket.status)
        .all()
    )

    status_breakdown = {
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
        "closed": 0,
    }
    for status, count in status_counts:
        if status:
            status_breakdown[status.value] = count

    # Category breakdown
    category_counts = (
        db.query(ITTicket.category, func.count(ITTicket.id).label("count"))
        .group_by(ITTicket.category)
        .all()
    )

    category_breakdown = {}
    for category, count in category_counts:
        if category:
            category_breakdown[category.value] = count

    # Priority breakdown
    priority_counts = (
        db.query(ITTicket.priority, func.count(ITTicket.id).label("count"))
        .group_by(ITTicket.priority)
        .all()
    )

    priority_breakdown = {}
    for priority, count in priority_counts:
        if priority:
            priority_breakdown[priority.value] = count

    # Monthly trend (last 6 months)
    from datetime import timedelta
    six_months_ago = datetime.now() - timedelta(days=180)

    monthly_trend = (
        db.query(
            func.date_trunc("month", ITTicket.created_at).label("month"),
            func.count(ITTicket.id).label("count"),
        )
        .filter(ITTicket.created_at >= six_months_ago)
        .group_by("month")
        .order_by("month")
        .all()
    )

    monthly_data = [
        {"month": month.strftime("%Y-%m") if month else None, "count": count}
        for month, count in monthly_trend
    ]

    # Average resolution time (for resolved tickets)
    resolved_tickets = (
        db.query(ITTicket)
        .filter(ITTicket.status == TicketStatus.RESOLVED)
        .filter(ITTicket.resolved_at.isnot(None))
        .all()
    )

    avg_resolution_hours = 0
    if resolved_tickets:
        total_hours = sum(
            (t.resolved_at - t.created_at).total_seconds() / 3600
            for t in resolved_tickets
            if t.resolved_at and t.created_at
        )
        avg_resolution_hours = round(total_hours / len(resolved_tickets), 1)

    return {
        "total_tickets": total,
        "status_breakdown": status_breakdown,
        "category_breakdown": category_breakdown,
        "priority_breakdown": priority_breakdown,
        "monthly_trend": monthly_data,
        "avg_resolution_hours": avg_resolution_hours,
    }


def get_tickets_for_export(db: Session, reporter_id: Optional[UUID] = None) -> list[dict]:
    """Get all IT tickets without pagination for CSV export."""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility
    from app.api.inventory.models import Inventory

    STATUS_LABELS = {
        "open": "Open",
        "in_progress": "In Progress",
        "resolved": "Resolved",
        "closed": "Closed",
    }

    CATEGORY_LABELS = {
        "hardware": "Hardware",
        "software": "Software",
        "network": "Network",
        "account_access": "Account/Access",
        "other": "Other",
    }

    PRIORITY_LABELS = {
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical",
    }

    query = db.query(ITTicket)

    if reporter_id:
        query = query.filter(ITTicket.reporter_id == reporter_id)

    tickets = query.order_by(ITTicket.created_at.desc()).all()

    # Get all unique IDs
    facility_ids = {t.facility_id for t in tickets if t.facility_id}
    reporter_ids = {t.reporter_id for t in tickets if t.reporter_id}
    inventory_ids = {t.inventory_item_id for t in tickets if t.inventory_item_id}
    assigned_ids = {t.assigned_to_id for t in tickets if t.assigned_to_id}
    resolver_ids = {t.resolved_by_id for t in tickets if t.resolved_by_id}

    # Fetch in bulk
    facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all() if facility_ids else []
    users = db.query(User).filter(User.id.in_(reporter_ids | assigned_ids | resolver_ids)).all()
    inventory_items = db.query(Inventory).filter(Inventory.id.in_(inventory_ids)).all() if inventory_ids else []

    # Create lookup dictionaries
    facility_map = {f.id: f.facility_name for f in facilities}
    user_map = {u.id: u.name for u in users}
    inventory_map = {i.id: i.item_name for i in inventory_items}

    result = []
    for t in tickets:
        result.append({
            "title": t.title or "",
            "description": t.description or "",
            "category": CATEGORY_LABELS.get(t.category.value, t.category.value) if t.category else "",
            "priority": PRIORITY_LABELS.get(t.priority.value, t.priority.value) if t.priority else "",
            "status": STATUS_LABELS.get(t.status.value, t.status.value) if t.status else "",
            "reporter": user_map.get(t.reporter_id, "") if t.reporter_id else "",
            "facility": facility_map.get(t.facility_id, "") if t.facility_id else "",
            "inventory_item": inventory_map.get(t.inventory_item_id, "") if t.inventory_item_id else "",
            "assigned_to": user_map.get(t.assigned_to_id, "") if t.assigned_to_id else "",
            "resolved_by": user_map.get(t.resolved_by_id, "") if t.resolved_by_id else "",
            "resolved_at": t.resolved_at.strftime("%Y-%m-%d %H:%M") if t.resolved_at else "",
            "resolution_notes": t.resolution_notes or "",
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "",
        })

    return result
