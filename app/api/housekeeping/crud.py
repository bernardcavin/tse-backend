from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.api.housekeeping.models import Housekeeping
from app.api.housekeeping.schemas import (
    HousekeepingCreateSchema,
    HousekeepingSchema,
    HousekeepingUpdateSchema,
)
from app.utils.filter_utils import get_paginated_data
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session


def create_housekeeping(
    db: Session, housekeeping: HousekeepingCreateSchema, inspector_id: UUID
) -> Dict[str, Any]:
    """Create a new housekeeping checklist. Called by HSE users."""
    # Convert checklist items to dict for JSON storage
    section_a = [item.model_dump() for item in housekeeping.section_a_items]
    section_b = [item.model_dump() for item in housekeeping.section_b_items]
    section_c = [item.model_dump() for item in housekeeping.section_c_items]
    section_d = [item.model_dump() for item in housekeeping.section_d_items]

    db_housekeeping = Housekeeping(
        location_area=housekeeping.location_area,
        inspection_date=housekeeping.inspection_date,
        inspector_name=housekeeping.inspector_name,
        inspector_id=inspector_id,
        facility_id=housekeeping.facility_id,
        section_a_items=section_a,
        section_b_items=section_b,
        section_c_items=section_c,
        section_d_items=section_d,
        additional_notes=housekeeping.additional_notes,
    )

    db.add(db_housekeeping)
    db.commit()
    db.refresh(db_housekeeping)

    return HousekeepingSchema.model_validate(db_housekeeping).model_dump(mode="json")


def get_housekeeping(db: Session, housekeeping_id: UUID) -> Dict[str, Any]:
    """Get a single housekeeping checklist by ID."""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility

    housekeeping = (
        db.query(Housekeeping).filter(Housekeeping.id == housekeeping_id).first()
    )

    if not housekeeping:
        raise HTTPException(status_code=404, detail="Housekeeping checklist not found")
    
    # Get inspector name
    inspector = db.query(User).filter(User.id == housekeeping.inspector_id).first()
    inspector_user_name = inspector.username if inspector else None
    
    # Get facility name
    facility = None
    if housekeeping.facility_id:
        facility = db.query(Facility).filter(Facility.id == housekeeping.facility_id).first()
    
    # Convert to dict and add names
    result = HousekeepingSchema.model_validate(housekeeping).model_dump(mode="json")
    result["inspector_user_name"] = inspector_user_name
    result["facility_name"] = facility.facility_name if facility else None
    
    return result


def get_housekeeping_list(
    db: Session,
    request: Any,
) -> Dict[str, Any]:

    return get_paginated_data(db, request, Housekeeping, HousekeepingSchema, "inspection_date")


def update_housekeeping(
    db: Session, housekeeping_id: UUID, housekeeping: HousekeepingUpdateSchema
) -> Dict[str, Any]:
    """Update an existing housekeeping checklist. Only managers can do this."""
    db_housekeeping = (
        db.query(Housekeeping).filter(Housekeeping.id == housekeeping_id).first()
    )

    if not db_housekeeping:
        raise HTTPException(status_code=404, detail="Housekeeping checklist not found")

    # Update only provided fields
    update_data = housekeeping.model_dump(exclude_unset=True)

    # Convert checklist items if provided
    if "section_a_items" in update_data and update_data["section_a_items"]:
        update_data["section_a_items"] = [
            item.model_dump() for item in housekeeping.section_a_items
        ]
    if "section_b_items" in update_data and update_data["section_b_items"]:
        update_data["section_b_items"] = [
            item.model_dump() for item in housekeeping.section_b_items
        ]
    if "section_c_items" in update_data and update_data["section_c_items"]:
        update_data["section_c_items"] = [
            item.model_dump() for item in housekeeping.section_c_items
        ]
    if "section_d_items" in update_data and update_data["section_d_items"]:
        update_data["section_d_items"] = [
            item.model_dump() for item in housekeeping.section_d_items
        ]

    for key, value in update_data.items():
        setattr(db_housekeeping, key, value)

    db_housekeeping.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_housekeeping)

    return HousekeepingSchema.model_validate(db_housekeeping).model_dump(mode="json")


def delete_housekeeping(db: Session, housekeeping_id: UUID) -> None:
    """Delete a housekeeping checklist. Only managers can do this."""
    db_housekeeping = (
        db.query(Housekeeping).filter(Housekeeping.id == housekeeping_id).first()
    )

    if not db_housekeeping:
        raise HTTPException(status_code=404, detail="Housekeeping checklist not found")

    db.delete(db_housekeeping)
    db.commit()


def get_analytics(db: Session) -> Dict[str, Any]:
    """Get housekeeping analytics. Only managers can access this."""
    total_checklists = db.query(func.count(Housekeeping.id)).scalar()

    # Get recent checklists (last 30 days)
    thirty_days_ago = datetime.utcnow().date()
    from datetime import timedelta
    thirty_days_ago = thirty_days_ago - timedelta(days=30)
    
    recent_checklists = (
        db.query(func.count(Housekeeping.id))
        .filter(Housekeeping.inspection_date >= thirty_days_ago)
        .scalar()
    )

    # Get checklists by facility (top 5)
    checklists_by_facility = (
        db.query(
            Housekeeping.facility_id,
            func.count(Housekeeping.id).label("count")
        )
        .filter(Housekeeping.facility_id.isnot(None))
        .group_by(Housekeeping.facility_id)
        .order_by(func.count(Housekeeping.id).desc())
        .limit(5)
        .all()
    )

    return {
        "total_checklists": total_checklists or 0,
        "recent_checklists_30_days": recent_checklists or 0,
        "checklists_by_facility": [
            {"facility_id": str(f[0]), "count": f[1]} for f in checklists_by_facility
        ],
    }


def get_housekeeping_for_export(db: Session) -> List[Dict[str, Any]]:
    """Get all housekeeping checklists for CSV export."""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility

    housekeeping_list = (
        db.query(Housekeeping)
        .order_by(Housekeeping.inspection_date.desc())
        .all()
    )

    # Get unique IDs
    facility_ids = {hk.facility_id for hk in housekeeping_list if hk.facility_id}
    inspector_ids = {hk.inspector_id for hk in housekeeping_list if hk.inspector_id}

    # Fetch in bulk
    facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all() if facility_ids else []
    users = db.query(User).filter(User.id.in_(inspector_ids)).all() if inspector_ids else []

    # Create lookup dictionaries
    facility_map = {f.id: f.facility_name for f in facilities}
    user_map = {u.id: u.username for u in users}

    result = []
    for hk in housekeeping_list:
        result.append({
            "location_area": hk.location_area or "",
            "facility": facility_map.get(hk.facility_id, "") if hk.facility_id else "",
            "inspection_date": hk.inspection_date.strftime("%Y-%m-%d") if hk.inspection_date else "",
            "inspector_name": hk.inspector_name or "",
            "inspector_username": user_map.get(hk.inspector_id, "") if hk.inspector_id else "",
            "additional_notes": hk.additional_notes or "",
            "created_at": hk.created_at.strftime("%Y-%m-%d %H:%M") if hk.created_at else "",
        })

    return result
