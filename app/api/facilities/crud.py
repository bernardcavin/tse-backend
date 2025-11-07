from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.api.facilities.models import Facility
from app.api.facilities.schemas import FacilitySchema
from app.core.schema_operations import parse_schema
from app.utils.filter_utils import get_options, get_paginated_data


def create_facility(db: Session, facility: FacilitySchema):
    db_facility = Facility(**parse_schema(facility))
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    return db_facility


def get_facility(db: Session, id: UUID):
    db_facility = db.query(Facility).get(id)
    return FacilitySchema.model_validate(db_facility)


def update_facility(db: Session, id: UUID, facility: FacilitySchema):
    db_facility = db.query(Facility).get(id)
    for key, value in parse_schema(facility).items():
        setattr(db_facility, key, value)
    db.commit()
    db.refresh(db_facility)
    return db_facility


def delete_facility(db: Session, id: UUID):
    db_facility = db.query(Facility).where(Facility.id == id).first()
    if db_facility is None:
        raise ValueError(f"Facility with id {id} does not exist")
    db_facility.soft_delete()
    db.commit()


def get_all_facilities(db: Session, request: Request):
    return get_paginated_data(db, request, Facility, FacilitySchema, "facility_name")


def get_facilities_options(db: Session):
    return get_options(db, Facility, "facility_name")


def get_facility_coordinates(db: Session, id: UUID):
    facility = db.query(Facility).where(Facility.id == id).first()
    if facility is None:
        raise ValueError("No facility found")
    return {
        "latitude": facility.latitude,
        "longitude": facility.longitude,
    }
