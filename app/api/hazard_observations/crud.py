from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api.hazard_observations.models import HazardObservation, ObservationStatus
from app.api.hazard_observations.schemas import (
    HazardObservationCreateSchema,
    HazardObservationResolveSchema,
    HazardObservationSchema,
    HazardObservationUpdateSchema,
)
from app.utils.filter_utils import get_paginated_data


def create_observation(
    db: Session, observation: HazardObservationCreateSchema, observer_id: UUID
) -> HazardObservationSchema:
    """Create a new hazard observation"""
    observation_dict = observation.model_dump(exclude_unset=True)
    observation_dict["observer_id"] = observer_id

    # Convert enum lists to string lists for database storage
    if "hazard_types" in observation_dict and observation_dict["hazard_types"]:
        observation_dict["hazard_types"] = [ht.value for ht in observation_dict["hazard_types"]]
    if "potential_risks" in observation_dict and observation_dict["potential_risks"]:
        observation_dict["potential_risks"] = [pr.value for pr in observation_dict["potential_risks"]]
    if "unsafe_reasons" in observation_dict and observation_dict["unsafe_reasons"]:
        observation_dict["unsafe_reasons"] = [ur.value for ur in observation_dict["unsafe_reasons"]]
    if "control_measures" in observation_dict and observation_dict["control_measures"]:
        observation_dict["control_measures"] = [cm.value for cm in observation_dict["control_measures"]]

    db_observation = HazardObservation(**observation_dict)
    db.add(db_observation)
    db.commit()
    db.refresh(db_observation)

    return HazardObservationSchema.model_validate(db_observation).model_dump(mode="json")


def get_observation(db: Session, observation_id: UUID) -> HazardObservationSchema:
    """Get a single hazard observation by ID"""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility
    
    observation = (
        db.query(HazardObservation)
        .filter(HazardObservation.id == observation_id)
        .first()
    )
    if not observation:
        raise HTTPException(status_code=404, detail="Hazard observation not found")
    
    # Get facility name
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
    
    # Convert to dict and add names
    result = HazardObservationSchema.model_validate(observation).model_dump(mode="json")
    result["facility_name"] = facility_name
    result["observer_name"] = observer_name
    result["resolved_by_name"] = resolved_by_name
    
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
    """Get all hazard observations with filtering and pagination"""
    from app.api.auth.models import User
    from app.api.facilities.models import Facility
    
    query = db.query(HazardObservation)

    # Apply filters
    if observer_id:  # For employees - only show their own observations
        query = query.filter(HazardObservation.observer_id == observer_id)
    if facility_id:
        query = query.filter(HazardObservation.facility_id == facility_id)
    if status:
        query = query.filter(HazardObservation.status == status)
    if start_date:
        query = query.filter(HazardObservation.observation_date >= start_date)
    if end_date:
        query = query.filter(HazardObservation.observation_date <= end_date)

    # Use standard pagination utility
    result = get_paginated_data(
        db, request, HazardObservation, HazardObservationSchema, "observation_date"
    )
    
    # Enrich each observation with facility and observer names
    if result and "data" in result:
        # Get all unique facility, observer, and resolver IDs
        facility_ids = {obs["facility_id"] for obs in result["data"] if obs.get("facility_id")}
        observer_ids = {obs["observer_id"] for obs in result["data"] if obs.get("observer_id")}
        resolver_ids = {obs["resolved_by_id"] for obs in result["data"] if obs.get("resolved_by_id")}
        
        # Fetch facilities and users in bulk
        facilities = db.query(Facility).filter(Facility.id.in_(facility_ids)).all()
        users = db.query(User).filter(User.id.in_(observer_ids | resolver_ids)).all()
        
        # Create lookup dictionaries
        facility_map = {str(f.id): f.facility_name for f in facilities}
        user_map = {str(u.id): u.name for u in users}
        
        # Add names to each observation
        for obs in result["data"]:
            obs["facility_name"] = facility_map.get(obs.get("facility_id"))
            obs["observer_name"] = user_map.get(obs.get("observer_id"))
            obs["resolved_by_name"] = user_map.get(obs.get("resolved_by_id")) if obs.get("resolved_by_id") else None
    
    return result


def update_observation(
    db: Session, observation_id: UUID, observation: HazardObservationUpdateSchema
) -> HazardObservationSchema:
    """Update a hazard observation"""
    db_observation = (
        db.query(HazardObservation)
        .filter(HazardObservation.id == observation_id)
        .first()
    )
    if not db_observation:
        raise HTTPException(status_code=404, detail="Hazard observation not found")

    update_data = observation.model_dump(exclude_unset=True)

    # Convert enum lists to string lists for database storage
    if "hazard_types" in update_data and update_data["hazard_types"]:
        update_data["hazard_types"] = [ht.value for ht in update_data["hazard_types"]]
    if "potential_risks" in update_data and update_data["potential_risks"]:
        update_data["potential_risks"] = [pr.value for pr in update_data["potential_risks"]]
    if "unsafe_reasons" in update_data and update_data["unsafe_reasons"]:
        update_data["unsafe_reasons"] = [ur.value for ur in update_data["unsafe_reasons"]]
    if "control_measures" in update_data and update_data["control_measures"]:
        update_data["control_measures"] = [cm.value for cm in update_data["control_measures"]]

    for key, value in update_data.items():
        setattr(db_observation, key, value)

    db.commit()
    db.refresh(db_observation)
    return HazardObservationSchema.model_validate(db_observation).model_dump(mode="json")


def delete_observation(db: Session, observation_id: UUID) -> None:
    """Delete a hazard observation (managers only)"""
    db_observation = (
        db.query(HazardObservation)
        .filter(HazardObservation.id == observation_id)
        .first()
    )
    if not db_observation:
        raise HTTPException(status_code=404, detail="Hazard observation not found")

    db.delete(db_observation)
    db.commit()


def resolve_observation(
    db: Session,
    observation_id: UUID,
    resolution: HazardObservationResolveSchema,
    resolved_by_id: UUID,
) -> HazardObservationSchema:
    """Resolve a hazard observation (HSE employees only)"""
    db_observation = (
        db.query(HazardObservation)
        .filter(HazardObservation.id == observation_id)
        .first()
    )
    if not db_observation:
        raise HTTPException(status_code=404, detail="Hazard observation not found")

    # Check if already resolved
    if db_observation.status == ObservationStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Observation is already resolved")

    # Update resolution fields
    db_observation.status = ObservationStatus.RESOLVED
    db_observation.resolved_by_id = resolved_by_id
    db_observation.resolved_at = datetime.utcnow()
    db_observation.resolution_notes = resolution.resolution_notes

    db.commit()
    db.refresh(db_observation)
    return HazardObservationSchema.model_validate(db_observation).model_dump(mode="json")


def get_analytics(db: Session) -> dict:
    """Get analytics for hazard observations (managers and HSE only)"""
    from sqlalchemy import func
    
    # Total observations
    total = db.query(HazardObservation).count()
    
    # Status breakdown
    status_counts = (
        db.query(
            HazardObservation.status,
            func.count(HazardObservation.id).label("count")
        )
        .group_by(HazardObservation.status)
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
    
    # Hazard types distribution (count occurrences in arrays)
    observations_with_types = (
        db.query(HazardObservation.hazard_types)
        .filter(HazardObservation.hazard_types.isnot(None))
        .all()
    )
    
    hazard_types_count = {}
    for (types,) in observations_with_types:
        if types:
            for hazard_type in types:
                hazard_types_count[hazard_type] = hazard_types_count.get(hazard_type, 0) + 1
    
    # Facilities with most hazards
    from app.api.facilities.models import Facility
    
    facilities_count = (
        db.query(
            HazardObservation.facility_id,
            func.count(HazardObservation.id).label("count")
        )
        .group_by(HazardObservation.facility_id)
        .order_by(func.count(HazardObservation.id).desc())
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
            func.date_trunc('month', HazardObservation.observation_date).label('month'),
            func.count(HazardObservation.id).label('count')
        )
        .filter(HazardObservation.observation_date >= six_months_ago.date())
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
        "hazard_types_distribution": hazard_types_count,
        "top_facilities": top_facilities,
        "monthly_trend": monthly_data,
    }
