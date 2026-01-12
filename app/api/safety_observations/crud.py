from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api.safety_observations.models import SafetyObservation, ObservationStatus
from app.api.safety_observations.schemas import (
    SafetyObservationCloseSchema,
    SafetyObservationCreateSchema,
    SafetyObservationResolveSchema,
    SafetyObservationSchema,
    SafetyObservationUpdateSchema,
)
from app.utils.filter_utils import get_paginated_data


def create_observation(
    db: Session, observation: SafetyObservationCreateSchema, observer_id: UUID
) -> SafetyObservationSchema:
    """Create a new Safety observation"""
    observation_dict = observation.model_dump(exclude_unset=True)
    observation_dict["observer_id"] = observer_id

    # Convert enum lists to string lists for database storage
    if "observation_types" in observation_dict and observation_dict["observation_types"]:
        observation_dict["observation_types"] = [ot.value for ot in observation_dict["observation_types"]]
    if "observation_categories" in observation_dict and observation_dict["observation_categories"]:
        observation_dict["observation_categories"] = [oc.value for oc in observation_dict["observation_categories"]]
    if "potential_impacts" in observation_dict and observation_dict["potential_impacts"]:
        observation_dict["potential_impacts"] = [pi.value for pi in observation_dict["potential_impacts"]]

    db_observation = SafetyObservation(**observation_dict)
    db.add(db_observation)
    db.commit()
    db.refresh(db_observation)

    return SafetyObservationSchema.model_validate(db_observation).model_dump(mode="json")


def get_observation(db: Session, observation_id: UUID) -> SafetyObservationSchema:
    """Get a single Safety observation by ID"""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility
    
    observation = (
        db.query(SafetyObservation)
        .filter(SafetyObservation.id == observation_id)
        .first()
    )
    if not observation:
        raise HTTPException(status_code=404, detail="Safety observation not found")
    
    # Get facility name if exists
    facility_name = None
    if observation.facility_id:
        facility = db.query(Facility).filter(Facility.id == observation.facility_id).first()
        facility_name = facility.facility_name if facility else None
    
    # Get observer name
    observer = db.query(User).filter(User.id == observation.observer_id).first()
    observer_name = observer.name if observer else None
    
    # Get resolved by name if resolved
    resolved_by_name = None
    if observation.resolved_by_id:
        resolver = db.query(User).filter(User.id == observation.resolved_by_id).first()
        resolved_by_name = resolver.name if resolver else None

    # Get closed by name if closed
    closed_by_name = None
    if observation.closed_by_id:
        closer = db.query(User).filter(User.id == observation.closed_by_id).first()
        closed_by_name = closer.name if closer else None
    
    # Convert to dict and add names
    result = SafetyObservationSchema.model_validate(observation).model_dump(mode="json")
    result["facility_name"] = facility_name
    result["observer_name"] = observer_name
    result["resolved_by_name"] = resolved_by_name
    result["closed_by_name"] = closed_by_name
    
    return result


def get_observations(
    db: Session,
    request,
    observer_id: Optional[UUID] = None,
    facility_id: Optional[UUID] = None,
    status: Optional[ObservationStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    """Get all Safety observations with filtering and pagination"""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility
    
    query = db.query(SafetyObservation)

    # Apply filters
    if observer_id:  # For employees - only show their own observations
        query = query.filter(SafetyObservation.observer_id == observer_id)
    if facility_id:
        query = query.filter(SafetyObservation.facility_id == facility_id)
    if status:
        query = query.filter(SafetyObservation.status == status)
    if start_date:
        query = query.filter(SafetyObservation.observation_date >= start_date)
    if end_date:
        query = query.filter(SafetyObservation.observation_date <= end_date)

    # Use standard pagination utility with filtered query
    result = get_paginated_data(
        db, request, SafetyObservation, SafetyObservationSchema, "observation_date", base_query=query
    )
    
    # Enrich each observation with facility and observer names
    if result and "data" in result:
        # Get all unique facility, observer, resolver, and closer IDs
        facility_ids = {obs["facility_id"] for obs in result["data"] if obs.get("facility_id")}
        observer_ids = {obs["observer_id"] for obs in result["data"] if obs.get("observer_id")}
        resolver_ids = {obs["resolved_by_id"] for obs in result["data"] if obs.get("resolved_by_id")}
        closer_ids = {obs["closed_by_id"] for obs in result["data"] if obs.get("closed_by_id")}
        
        # Fetch facilities and users in bulk
        facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all()
        users = db.query(User).filter(User.id.in_(observer_ids | resolver_ids | closer_ids)).all()
        
        # Create lookup dictionaries
        facility_map = {str(f.id): f.facility_name for f in facilities}
        user_map = {str(u.id): u.name for u in users}
        
        # Add names to each observation
        for obs in result["data"]:
            obs["facility_name"] = facility_map.get(obs.get("facility_id"))
            obs["observer_name"] = user_map.get(obs.get("observer_id"))
            obs["resolved_by_name"] = user_map.get(obs.get("resolved_by_id")) if obs.get("resolved_by_id") else None
            obs["closed_by_name"] = user_map.get(obs.get("closed_by_id")) if obs.get("closed_by_id") else None
    
    return result


def update_observation(
    db: Session, observation_id: UUID, observation: SafetyObservationUpdateSchema
) -> SafetyObservationSchema:
    """Update a Safety observation"""
    db_observation = (
        db.query(SafetyObservation)
        .filter(SafetyObservation.id == observation_id)
        .first()
    )
    if not db_observation:
        raise HTTPException(status_code=404, detail="Safety observation not found")

    update_data = observation.model_dump(exclude_unset=True)

    # Convert enum lists to string lists for database storage
    if "observation_types" in update_data and update_data["observation_types"]:
        update_data["observation_types"] = [ot.value for ot in update_data["observation_types"]]
    if "observation_categories" in update_data and update_data["observation_categories"]:
        update_data["observation_categories"] = [oc.value for oc in update_data["observation_categories"]]
    if "potential_impacts" in update_data and update_data["potential_impacts"]:
        update_data["potential_impacts"] = [pi.value for pi in update_data["potential_impacts"]]

    for key, value in update_data.items():
        setattr(db_observation, key, value)

    db.commit()
    db.refresh(db_observation)
    return SafetyObservationSchema.model_validate(db_observation).model_dump(mode="json")


def delete_observation(db: Session, observation_id: UUID) -> None:
    """Delete a Safety observation (managers only)"""
    db_observation = (
        db.query(SafetyObservation)
        .filter(SafetyObservation.id == observation_id)
        .first()
    )
    if not db_observation:
        raise HTTPException(status_code=404, detail="Safety observation not found")

    db.delete(db_observation)
    db.commit()


def resolve_observation(
    db: Session,
    observation_id: UUID,
    resolution: SafetyObservationResolveSchema,
    resolved_by_id: UUID,
) -> SafetyObservationSchema:
    """Resolve a Safety observation (HSE employees only)"""
    db_observation = (
        db.query(SafetyObservation)
        .filter(SafetyObservation.id == observation_id)
        .first()
    )
    if not db_observation:
        raise HTTPException(status_code=404, detail="Safety observation not found")

    # Check if already resolved or closed
    if db_observation.status in [ObservationStatus.RESOLVED, ObservationStatus.CLOSED]:
        raise HTTPException(status_code=400, detail="Observation is already resolved or closed")

    # Update resolution fields
    db_observation.status = ObservationStatus.RESOLVED
    db_observation.resolved_by_id = resolved_by_id
    db_observation.resolved_at = datetime.utcnow()
    db_observation.resolution_notes = resolution.resolution_notes

    db.commit()
    db.refresh(db_observation)
    return SafetyObservationSchema.model_validate(db_observation).model_dump(mode="json")


def close_observation(
    db: Session,
    observation_id: UUID,
    close_data: SafetyObservationCloseSchema,
    closed_by_id: UUID,
) -> SafetyObservationSchema:
    """Close an invalid Safety observation (HSE/Manager only)"""
    db_observation = (
        db.query(SafetyObservation)
        .filter(SafetyObservation.id == observation_id)
        .first()
    )
    if not db_observation:
        raise HTTPException(status_code=404, detail="Safety observation not found")

    # Check if already resolved or closed
    if db_observation.status in [ObservationStatus.RESOLVED, ObservationStatus.CLOSED]:
        raise HTTPException(status_code=400, detail="Observation is already resolved or closed")

    # Update close fields
    db_observation.status = ObservationStatus.CLOSED
    db_observation.closed_by_id = closed_by_id
    db_observation.closed_at = datetime.utcnow()
    db_observation.close_reason = close_data.close_reason

    db.commit()
    db.refresh(db_observation)
    return SafetyObservationSchema.model_validate(db_observation).model_dump(mode="json")


def get_analytics(db: Session) -> dict:
    """Get analytics for Safety observations (managers and HSE only)"""
    from sqlalchemy import func
    
    # Total observations
    total = db.query(SafetyObservation).count()
    
    # Status breakdown
    status_counts = (
        db.query(
            SafetyObservation.status,
            func.count(SafetyObservation.id).label("count")
        )
        .group_by(SafetyObservation.status)
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
    
    # Observation categories distribution (count occurrences in arrays)
    observations_with_categories = (
        db.query(SafetyObservation.observation_categories)
        .filter(SafetyObservation.observation_categories.isnot(None))
        .all()
    )
    
    categories_count = {}
    for (categories,) in observations_with_categories:
        if categories:
            for category in categories:
                categories_count[category] = categories_count.get(category, 0) + 1

    # Observation types distribution
    observations_with_types = (
        db.query(SafetyObservation.observation_types)
        .filter(SafetyObservation.observation_types.isnot(None))
        .all()
    )
    
    types_count = {}
    for (types,) in observations_with_types:
        if types:
            for type_ in types:
                types_count[type_] = types_count.get(type_, 0) + 1
    
    # Facilities with most Safetys
    from app.api.facilities.models import Facility
    
    facilities_count = (
        db.query(
            SafetyObservation.facility_id,
            func.count(SafetyObservation.id).label("count")
        )
        .filter(SafetyObservation.facility_id.isnot(None))
        .group_by(SafetyObservation.facility_id)
        .order_by(func.count(SafetyObservation.id).desc())
        .limit(5)
        .all()
    )
    
    # Get facility names
    facility_ids = [f[0] for f in facilities_count]
    facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all()
    facility_name_map = {f.id: f.facility_name for f in facilities}
    
    top_facilities = [
        {
            "facility_id": str(facility_id),
            "facility_name": facility_name_map.get(facility_id, str(facility_id)),
            "count": count
        }
        for facility_id, count in facilities_count
    ]
    
    # Monthly trend (last 6 months)
    from datetime import datetime, timedelta
    six_months_ago = datetime.now() - timedelta(days=180)
    
    monthly_trend = (
        db.query(
            func.date_trunc('month', SafetyObservation.observation_date).label('month'),
            func.count(SafetyObservation.id).label('count')
        )
        .filter(SafetyObservation.observation_date >= six_months_ago.date())
        .group_by('month')
        .order_by('month')
        .all()
    )
    
    monthly_data = [
        {"month": month.strftime("%Y-%m") if month else None, "count": count}
        for month, count in monthly_trend
    ]
    
    return {
        "total_observations": total,
        "status_breakdown": status_breakdown,
        "categories_distribution": categories_count,
        "observation_types_distribution": types_count,
        "top_facilities": top_facilities,
        "monthly_trend": monthly_data,
    }


def get_observations_for_export(db: Session, observer_id: Optional[UUID] = None) -> list[dict]:
    """Get all Safety observations without pagination for CSV export."""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility
    
    # Status labels for export
    STATUS_LABELS = {
        "open": "Open",
        "in_progress": "In Progress",
        "resolved": "Resolved",
        "closed": "Closed",
    }
    
    query = db.query(SafetyObservation)
    
    if observer_id:
        query = query.filter(SafetyObservation.observer_id == observer_id)
    
    observations = query.order_by(SafetyObservation.observation_date.desc()).all()
    
    # Get all unique facility, observer, resolver, and closer IDs
    facility_ids = {obs.facility_id for obs in observations if obs.facility_id}
    observer_ids = {obs.observer_id for obs in observations if obs.observer_id}
    resolver_ids = {obs.resolved_by_id for obs in observations if obs.resolved_by_id}
    closer_ids = {obs.closed_by_id for obs in observations if obs.closed_by_id}
    
    # Fetch facilities and users in bulk
    facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all() if facility_ids else []
    users = db.query(User).filter(User.id.in_(observer_ids | resolver_ids | closer_ids)).all() if observer_ids or resolver_ids or closer_ids else []
    
    # Create lookup dictionaries
    facility_map = {f.id: f.facility_name for f in facilities}
    user_map = {u.id: u.name for u in users}
    
    result = []
    for obs in observations:
        # Format arrays as comma-separated strings
        observation_types_str = ", ".join(obs.observation_types) if obs.observation_types else ""
        observation_categories_str = ", ".join(obs.observation_categories) if obs.observation_categories else ""
        potential_impacts_str = ", ".join(obs.potential_impacts) if obs.potential_impacts else ""
        
        result.append({
            "observation_date": obs.observation_date.strftime("%Y-%m-%d") if obs.observation_date else "",
            "observation_time": obs.observation_time or "",
            "facility": facility_map.get(obs.facility_id, "") if obs.facility_id else "",
            "location_area": obs.location_area or "",
            "department_unit": obs.department_unit or "",
            "observer": user_map.get(obs.observer_id, "") if obs.observer_id else "",
            "observation_types": observation_types_str,
            "observation_categories": observation_categories_str,
            "category_other": obs.category_other or "",
            "observation_description": obs.observation_description or "",
            "potential_impacts": potential_impacts_str,
            "impact_explanation": obs.impact_explanation or "",
            "suggested_corrective_action": obs.suggested_corrective_action or "",
            "immediate_action_done": obs.immediate_action_done or "",
            "immediate_action_description": obs.immediate_action_description or "",
            "has_supporting_evidence": obs.has_supporting_evidence or "",
            "status": STATUS_LABELS.get(obs.status.value, obs.status.value) if obs.status else "",
            "resolved_by": user_map.get(obs.resolved_by_id, "") if obs.resolved_by_id else "",
            "resolved_at": obs.resolved_at.strftime("%Y-%m-%d %H:%M") if obs.resolved_at else "",
            "resolution_notes": obs.resolution_notes or "",
            "closed_by": user_map.get(obs.closed_by_id, "") if obs.closed_by_id else "",
            "closed_at": obs.closed_at.strftime("%Y-%m-%d %H:%M") if obs.closed_at else "",
            "close_reason": obs.close_reason or "",
        })
    
    return result
