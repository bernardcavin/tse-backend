from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.api.inventory.models import Inventory
from app.api.inventory.schemas import InventorySchema
from app.core.schema_operations import parse_schema
from app.utils.filter_utils import get_options, get_paginated_data


def create_inventory(db: Session, inventory: InventorySchema):
    db_inventory = Inventory(**parse_schema(inventory))
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory


def get_inventory(db: Session, id: UUID):
    db_inventory = db.query(Inventory).get(id)
    return InventorySchema.model_validate(db_inventory)


def update_inventory(db: Session, id: UUID, inventory: InventorySchema):
    db_inventory = db.query(Inventory).get(id)
    for key, value in parse_schema(inventory).items():
        if key == "storage_location":
            continue
        setattr(db_inventory, key, value)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory


def delete_inventory(db: Session, id: UUID):
    db_inventory = db.query(Inventory).where(Inventory.id == id).first()
    if db_inventory is None:
        raise ValueError(f"Inventory with id {id} does not exist")
    db_inventory.soft_delete()
    db.commit()


def get_all_inventory(db: Session, request: Request):
    return get_paginated_data(db, request, Inventory, InventorySchema, "item_name")


def get_inventory_options(db: Session):
    return get_options(db, Inventory, "item_name")
