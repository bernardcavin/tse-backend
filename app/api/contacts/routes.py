from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.contacts import crud, schemas
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/contacts")


@router.get(
    "",
    summary="Get All Contacts",
    tags=["Contact"],
)
async def get_all_contacts(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    contacts = crud.get_all_contacts(db, request)
    return create_api_response(
        success=True, message="Contacts retrieved successfully", data=contacts
    )


@router.post(
    "",
    summary="Create Contact",
    tags=["Contact"],
)
async def create_contact(
    contact: schemas.ContactSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.create_contact(db, contact)
    log_contribution(db, user, "CREATED", "contact", contact.name)
    return create_api_response(success=True, message="Contact created successfully")


@router.post(
    "/bulk",
    summary="Bulk Import Contacts",
    tags=["Contact"],
)
async def bulk_import_contacts(
    contacts: list[schemas.ContactSchema],
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    created_count = 0
    for contact in contacts:
        try:
            crud.create_contact(db, contact)
            created_count += 1
        except Exception as e:
            # Continue with other contacts if one fails
            pass
    log_contribution(db, user, "IMPORTED", "contacts", f"{created_count} contacts")
    return create_api_response(
        success=True,
        message=f"Successfully imported {created_count} of {len(contacts)} contacts",
        data={"created": created_count, "total": len(contacts)},
    )


@router.get(
    "/utils/options",
    summary="Get Contact Options",
    tags=["Contact"],
)
async def get_contact_options(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    options = crud.get_contacts_options(db)
    return create_api_response(
        success=True, message="Contact options retrieved successfully", data=options
    )


@router.get(
    "/utils/zones",
    summary="Get Zone Options",
    tags=["Contact"],
)
async def get_zone_options(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    options = crud.get_zone_options(db)
    return create_api_response(
        success=True, message="Zone options retrieved successfully", data=options
    )


@router.get(
    "/export/csv",
    summary="Export Contacts to CSV",
    tags=["Contact"],
)
async def export_contacts_csv(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Export all contacts data for CSV download."""
    contacts = crud.get_all_contacts_for_export(db)
    return create_api_response(
        success=True, message="Contacts exported successfully", data=contacts
    )


@router.get(
    "/{id}",
    summary="Get Contact",
    tags=["Contact"],
)
async def get_contact(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    contact = crud.get_contact(db, id)
    return create_api_response(
        success=True, message="Contact retrieved successfully", data=contact
    )


@router.put(
    "/{id}",
    summary="Update Contact",
    tags=["Contact"],
)
async def update_contact(
    id: UUID,
    contact: schemas.ContactSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_contact(db, id, contact)
    log_contribution(db, user, "UPDATED", "contact", contact.name)
    return create_api_response(success=True, message="Contact updated successfully")


@router.delete(
    "/{id}",
    summary="Delete Contact",
    tags=["Contact"],
)
async def delete_contact(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.delete_contact(db, id)
    log_contribution(db, user, "DELETED", "contact", f"id={id}")
    return create_api_response(success=True, message="Contact deleted successfully")
