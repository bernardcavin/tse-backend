from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.api.contacts.models import Contact
from app.api.contacts.schemas import ContactSchema
from app.core.schema_operations import parse_schema
from app.utils.filter_utils import get_options, get_paginated_data


def create_contact(db: Session, contact: ContactSchema):
    db_contact = Contact(**parse_schema(contact))
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def get_contact(db: Session, id: UUID):
    db_contact = db.query(Contact).get(id)
    return ContactSchema.model_validate(db_contact)


def update_contact(db: Session, id: UUID, contact: ContactSchema):
    db_contact = db.query(Contact).get(id)
    for key, value in parse_schema(contact).items():
        setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, id: UUID):
    db_contact = db.query(Contact).where(Contact.id == id).first()
    if db_contact is None:
        raise ValueError(f"Contact with id {id} does not exist")
    db_contact.soft_delete()
    db.commit()


def get_all_contacts(db: Session, request: Request):
    return get_paginated_data(db, request, Contact, ContactSchema, "name")


def get_contacts_options(db: Session):
    return get_options(db, Contact, "name")


def get_zone_options(db: Session):
    """Get distinct zone values for autocomplete."""
    zones = (
        db.query(Contact.zone)
        .filter(Contact.zone.isnot(None))
        .filter(Contact.zone != "")
        .distinct()
        .all()
    )
    return [{"value": z[0], "label": z[0]} for z in zones if z[0]]


def get_all_contacts_for_export(db: Session) -> list[dict]:
    """Get all contacts without pagination for CSV export."""
    contacts = (
        db.query(Contact)
        .filter(Contact.deleted_at.is_(None))
        .order_by(Contact.name)
        .all()
    )
    
    result = []
    for contact in contacts:
        regional_str = "-"
        if contact.regional and contact.regional > 0:
            regional_str = f"Regional {contact.regional}"
        
        result.append({
            "name": contact.name or "",
            "company": contact.company or "",
            "regional": regional_str,
            "zone": contact.zone or "",
            "field": contact.field or "",
            "email": contact.email or "",
            "phone": contact.phone or "",
            "position": contact.position or "",
            "address": contact.address or "",
            "notes": contact.notes or "",
        })
    
    return result
