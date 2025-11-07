from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth.crud import log_contribution
from app.api.auth.utils import get_current_user
from app.api.inventory import crud, schemas
from app.core.dependencies import get_db_session
from app.core.schema_operations import create_api_response
from app.core.utils.request import get_request

router = APIRouter(prefix="/inventory")


@router.get(
    "/",
    summary="Get All inventory",
    tags=["Inventory"],
)
async def get_all_services(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    inventory = crud.get_all_inventory(db, request)
    return create_api_response(
        success=True, message="inventory retrieved successfully", data=inventory
    )


@router.post(
    "/",
    summary="Create Inventory",
    tags=["Inventory"],
)
async def create_inventory(
    inventory: schemas.InventorySchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.create_inventory(db, inventory)
    log_contribution(db, user, "CREATED", "inventory", inventory.item_name)
    return create_api_response(success=True, message="Inventory created successfully")


@router.get(
    "/{id}",
    summary="Get Inventory",
    tags=["Inventory"],
)
async def get_inventory(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    inventory = crud.get_inventory(db, id)
    return create_api_response(
        success=True, message="Inventory retrieved successfully", data=inventory
    )


@router.put(
    "/{id}",
    summary="Update Inventory",
    tags=["Inventory"],
)
async def update_inventory(
    id: UUID,
    inventory: schemas.InventorySchema,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.update_inventory(db, id, inventory)
    log_contribution(db, user, "UPDATED", "inventory", inventory.item_name)
    return create_api_response(success=True, message="Inventory updated successfully")


@router.delete(
    "/{id}",
    summary="Delete Inventory",
    tags=["Inventory"],
)
async def delete_inventory(
    id: UUID,
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    crud.delete_inventory(db, id)
    log_contribution(db, user, "DELETED", "inventory", f"id={id}")
    return create_api_response(success=True, message="Inventory deleted successfully")


@router.get(
    "/utils/options",
    summary="Get Inventory Options",
    tags=["Inventory"],
)
async def get_inventory_options(
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
    user=Depends(get_current_user),
):
    options = crud.get_inventory_options(db)
    return create_api_response(
        success=True, message="Inventory options retrieved successfully", data=options
    )
