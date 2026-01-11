from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.expeditions import crud, schemas
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/expeditions", tags=["Expeditions"])


@router.post(
    "",
    summary="Create New Expedition",
)
async def create_expedition(
    expedition: schemas.CreateExpeditionSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Start a new expedition for the current user."""
    result = crud.create_expedition(db, expedition, user)
    log_contribution(db, user, "CREATED", "expedition", f"id={result.id}")
    return create_api_response(
        success=True, message="Expedition created successfully", data=result
    )


@router.get(
    "",
    summary="Get All Expeditions",
)
async def get_all_expeditions(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Get all expeditions with optional filtering."""
    expeditions = crud.get_all_expeditions(db, request)
    return create_api_response(
        success=True, message="Expeditions retrieved successfully", data=expeditions
    )


@router.get(
    "/{expedition_id}",
    summary="Get Expedition Details",
)
async def get_expedition(
    expedition_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Get detailed information about a specific expedition."""
    expedition = crud.get_expedition(db, expedition_id)
    return create_api_response(
        success=True, message="Expedition retrieved successfully", data=expedition
    )


@router.post(
    "/{expedition_id}/scan",
    summary="Scan Barcode to Add Item",
)
async def scan_item(
    expedition_id: UUID,
    item: schemas.AddItemSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Add an item to an expedition by scanning its barcode."""
    expedition = crud.add_item_to_expedition(db, expedition_id, item)
    log_contribution(
        db, user, "UPDATED", "expedition", f"Added item to expedition {expedition_id}"
    )
    return create_api_response(
        success=True, message="Item added to expedition successfully", data=expedition
    )


@router.post(
    "/{expedition_id}/items",
    summary="Manually Add Item",
)
async def add_item(
    expedition_id: UUID,
    item: schemas.AddItemSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Manually add an item to an expedition."""
    expedition = crud.add_item_to_expedition(db, expedition_id, item)
    log_contribution(
        db, user, "UPDATED", "expedition", f"Added item to expedition {expedition_id}"
    )
    return create_api_response(
        success=True, message="Item added to expedition successfully", data=expedition
    )


@router.put(
    "/{expedition_id}/items/{item_id}",
    summary="Update Item Quantity",
)
async def update_item_quantity(
    expedition_id: UUID,
    item_id: UUID,
    update: schemas.UpdateItemQuantitySchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Update the quantity of an item in an expedition."""
    expedition = crud.update_item_quantity(db, expedition_id, item_id, update.quantity)
    log_contribution(
        db, user, "UPDATED", "expedition", f"Updated item quantity in expedition {expedition_id}"
    )
    return create_api_response(
        success=True, message="Item quantity updated successfully", data=expedition
    )


@router.delete(
    "/{expedition_id}/items/{item_id}",
    summary="Remove Item from Expedition",
)
async def remove_item(
    expedition_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Remove an item from an expedition."""
    expedition = crud.remove_item_from_expedition(db, expedition_id, item_id)
    log_contribution(
        db, user, "UPDATED", "expedition", f"Removed item from expedition {expedition_id}"
    )
    return create_api_response(
        success=True, message="Item removed from expedition successfully", data=expedition
    )


@router.post(
    "/{expedition_id}/items/{item_id}/confirm",
    summary="Confirm Item Quantity",
)
async def confirm_item(
    expedition_id: UUID,
    item_id: UUID,
    confirm: schemas.ConfirmItemSchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Confirm an item's quantity when ending an expedition."""
    expedition = crud.confirm_item(db, expedition_id, item_id, confirm)
    return create_api_response(
        success=True, message="Item confirmed successfully", data=expedition
    )


@router.post(
    "/{expedition_id}/end",
    summary="End Expedition",
)
async def end_expedition(
    expedition_id: UUID,
    end_data: schemas.EndExpeditionSchema = None,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """End an active expedition and restore inventory status."""
    notes = end_data.notes if end_data else None
    expedition = crud.end_expedition(db, expedition_id, notes)
    log_contribution(db, user, "UPDATED", "expedition", f"Ended expedition {expedition_id}")
    return create_api_response(
        success=True, message="Expedition ended successfully", data=expedition
    )


@router.post(
    "/{expedition_id}/cancel",
    summary="Cancel Expedition",
)
async def cancel_expedition(
    expedition_id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Cancel an active expedition and restore inventory status."""
    expedition = crud.cancel_expedition(db, expedition_id)
    log_contribution(db, user, "UPDATED", "expedition")
    return create_api_response(
        success=True, message="Expedition cancelled successfully", data=expedition
    )


@router.get(
    "/analytics/stats",
    summary="Get Expedition Analytics",
)
async def get_analytics(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    """Get analytics data for expeditions dashboard."""
    analytics = crud.get_expedition_analytics(db)
    return create_api_response(
        success=True, message="Analytics retrieved successfully", data=analytics
    )
