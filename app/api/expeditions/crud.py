from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from fastapi.requests import Request
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.auth.models import User
from app.api.expeditions import schemas
from app.api.expeditions.models import Expedition, ExpeditionItem, ExpeditionStatus
from app.api.inventory.models import Inventory, LocationStatus
from app.core.schema_operations import parse_data_from_schema


def create_expedition(
    db: Session,
    expedition: schemas.CreateExpeditionSchema,
    user: User,
) -> schemas.ExpeditionSchema:
    """Create a new expedition for the current user."""
    db_expedition = Expedition(
        employee_id=user.id,
        status=ExpeditionStatus.ACTIVE,
        notes=expedition.notes,
    )
    db.add(db_expedition)
    db.commit()
    db.refresh(db_expedition)
    
    return get_expedition(db, db_expedition.id)


def get_expedition(db: Session, expedition_id: UUID) -> schemas.ExpeditionSchema:
    """Get an expedition by ID with all details."""
    expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    # Build response manually to include nested data
    result = schemas.ExpeditionSchema.model_validate(expedition)
    
    # Add items with inventory details
    result.items = []
    for item in expedition.items:
        item_schema = schemas.ExpeditionItemSchema.model_validate(item)
        if item.inventory:
            from app.api.inventory.schemas import InventorySchema
            item_schema.inventory = InventorySchema.model_validate(item.inventory)
        result.items.append(item_schema)
    
    return result


def get_all_expeditions(db: Session, request: Request):
    """Get all expeditions with pagination."""
    # Extract pagination parameters
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 15))
    status_param = request.query_params.get("status")
    
    query = db.query(Expedition)
    
    # Filter by status if provided
    if status_param:
        query = query.filter(Expedition.status == status_param)
    
    # Order by started_at descending
    query = query.order_by(Expedition.started_at.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    expeditions = query.offset(offset).limit(limit).all()
    
    # Convert to schemas with nested data
    result = []
    for exp in expeditions:
        exp_schema = get_expedition(db, exp.id)
        result.append(exp_schema)
    
    # Compute pagination metadata (matching get_paginated_data format)
    last_page = (total + limit - 1) // limit
    url = str(request.url).split("?")[0]
    
    meta = {
        "total": total,
        "perPage": limit,
        "currentPage": page,
        "lastPage": last_page,
        "firstPage": 1,
        "firstPageUrl": f"{url}?page=1&limit={limit}",
        "lastPageUrl": f"{url}?page={last_page}&limit={limit}",
        "nextPageUrl": f"{url}?page={min(page + 1, last_page)}&limit={limit}",
        "previousPageUrl": f"{url}?page={max(page - 1, 1)}&limit={limit}",
    }
    
    # Return paginated response
    return {"data": result, "meta": meta}




def add_item_to_expedition(
    db: Session,
    expedition_id: UUID,
    item: schemas.AddItemSchema,
) -> schemas.ExpeditionSchema:
    """Add an item to an expedition via scan or manual entry."""
    # Verify expedition exists and is active
    expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    if expedition.status != ExpeditionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Cannot add items to a non-active expedition"
        )
    
    # Verify inventory item exists
    inventory = db.query(Inventory).filter(Inventory.id == item.inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    # Check if item already exists in this expedition
    existing_item = (
        db.query(ExpeditionItem)
        .filter(
            and_(
                ExpeditionItem.expedition_id == expedition_id,
                ExpeditionItem.inventory_id == item.inventory_id,
            )
        )
        .first()
    )
    
    if existing_item:
        # Update quantity if item already exists
        existing_item.quantity += item.quantity
    else:
        # Create new expedition item
        db_item = ExpeditionItem(
            expedition_id=expedition_id,
            inventory_id=item.inventory_id,
            quantity=item.quantity,
        )
        db.add(db_item)
    
    # Update inventory location status to in_transit
    inventory.location_status = LocationStatus.in_transit
    
    db.commit()
    
    # Return updated expedition
    return get_expedition(db, expedition_id)


def update_item_quantity(
    db: Session,
    expedition_id: UUID,
    item_id: UUID,
    quantity: float,
) -> schemas.ExpeditionSchema:
    """Update the quantity of an item in an expedition."""
    item = (
        db.query(ExpeditionItem)
        .filter(
            and_(
                ExpeditionItem.id == item_id,
                ExpeditionItem.expedition_id == expedition_id,
            )
        )
        .first()
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Expedition item not found")
    
    item.quantity = quantity
    db.commit()
    
    return get_expedition(db, expedition_id)


def remove_item_from_expedition(
    db: Session,
    expedition_id: UUID,
    item_id: UUID,
) -> schemas.ExpeditionSchema:
    """Remove an item from an expedition."""
    item = (
        db.query(ExpeditionItem)
        .filter(
            and_(
                ExpeditionItem.id == item_id,
                ExpeditionItem.expedition_id == expedition_id,
            )
        )
        .first()
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Expedition item not found")
    
    # Get inventory to potentially restore status
    inventory = db.query(Inventory).filter(Inventory.id == item.inventory_id).first()
    
    # Delete the item
    db.delete(item)
    
    # Check if this inventory is in any other active expeditions
    if inventory:
        other_expeditions = (
            db.query(ExpeditionItem)
            .join(Expedition)
            .filter(
                and_(
                    ExpeditionItem.inventory_id == item.inventory_id,
                    Expedition.status == ExpeditionStatus.ACTIVE,
                )
            )
            .count()
        )
        
        # If no other active expeditions, restore to in_storage
        if other_expeditions == 0:
            inventory.location_status = LocationStatus.in_storage
    
    db.commit()
    
    return get_expedition(db, expedition_id)


def confirm_item(
    db: Session,
    expedition_id: UUID,
    item_id: UUID,
    confirm: schemas.ConfirmItemSchema,
) -> schemas.ExpeditionSchema:
    """Confirm an item's quantity when ending an expedition."""
    item = (
        db.query(ExpeditionItem)
        .filter(
            and_(
                ExpeditionItem.id == item_id,
                ExpeditionItem.expedition_id == expedition_id,
            )
        )
        .first()
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Expedition item not found")
    
    item.confirmed_quantity = confirm.confirmed_quantity
    item.confirmed_at = datetime.utcnow()
    
    db.commit()
    
    return get_expedition(db, expedition_id)


def end_expedition(
    db: Session,
    expedition_id: UUID,
    notes: Optional[str] = None,
) -> schemas.ExpeditionSchema:
    """End an active expedition and restore inventory status."""
    expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    if expedition.status != ExpeditionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Can only end active expeditions"
        )
    
    # Update expedition status
    expedition.status = ExpeditionStatus.COMPLETED
    expedition.ended_at = datetime.utcnow()
    if notes:
        expedition.notes = f"{expedition.notes}\n{notes}" if expedition.notes else notes
    
    # Restore all items to in_storage (if not in other active expeditions)
    for item in expedition.items:
        inventory = db.query(Inventory).filter(Inventory.id == item.inventory_id).first()
        if inventory:
            # Check if this item is in any other active expeditions
            other_expeditions = (
                db.query(ExpeditionItem)
                .join(Expedition)
                .filter(
                    and_(
                        ExpeditionItem.inventory_id == item.inventory_id,
                        Expedition.id != expedition_id,
                        Expedition.status == ExpeditionStatus.ACTIVE,
                    )
                )
                .count()
            )
            
            # If no other active expeditions, restore to in_storage
            if other_expeditions == 0:
                inventory.location_status = LocationStatus.in_storage
    
    db.commit()
    
    return get_expedition(db, expedition_id)


def cancel_expedition(
    db: Session,
    expedition_id: UUID,
) -> schemas.ExpeditionSchema:
    """Cancel an active expedition and restore inventory status."""
    expedition = db.query(Expedition).filter(Expedition.id == expedition_id).first()
    
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    if expedition.status != ExpeditionStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Can only cancel active expeditions"
        )
    
    # Update expedition status
    expedition.status = ExpeditionStatus.CANCELLED
    expedition.ended_at = datetime.utcnow()
    
    # Restore all items to in_storage (same logic as end_expedition)
    for item in expedition.items:
        inventory = db.query(Inventory).filter(Inventory.id == item.inventory_id).first()
        if inventory:
            other_expeditions = (
                db.query(ExpeditionItem)
                .join(Expedition)
                .filter(
                    and_(
                        ExpeditionItem.inventory_id == item.inventory_id,
                        Expedition.id != expedition_id,
                        Expedition.status == ExpeditionStatus.ACTIVE,
                    )
                )
                .count()
            )
            
            if other_expeditions == 0:
                inventory.location_status = LocationStatus.in_storage
    
    db.commit()
    
    return get_expedition(db, expedition_id)


def get_expedition_analytics(db: Session) -> schemas.ExpeditionAnalytics:
    """Get analytics data for expeditions dashboard."""
    total = db.query(func.count(Expedition.id)).scalar() or 0
    active = db.query(func.count(Expedition.id)).filter(
        Expedition.status == ExpeditionStatus.ACTIVE
    ).scalar() or 0
    completed = db.query(func.count(Expedition.id)).filter(
        Expedition.status == ExpeditionStatus.COMPLETED
    ).scalar() or 0
    cancelled = db.query(func.count(Expedition.id)).filter(
        Expedition.status == ExpeditionStatus.CANCELLED
    ).scalar() or 0
    
    # Get total items moved
    total_items = db.query(func.count(ExpeditionItem.id)).scalar() or 0
    
    # Get items currently in transit (in active expeditions)
    items_in_transit = (
        db.query(func.count(ExpeditionItem.id))
        .join(Expedition)
        .filter(Expedition.status == ExpeditionStatus.ACTIVE)
        .scalar() or 0
    )
    
    return schemas.ExpeditionAnalytics(
        total_expeditions=total,
        active_expeditions=active,
        completed_expeditions=completed,
        cancelled_expeditions=cancelled,
        total_items_moved=total_items,
        items_in_transit=items_in_transit,
    )
