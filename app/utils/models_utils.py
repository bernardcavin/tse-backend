from fastapi.encoders import jsonable_encoder
from sqlalchemy import inspect
from sqlalchemy.orm import (
    RelationshipProperty,
    class_mapper,
    object_session,
)


def update_sqlalchemy_object(target_obj, source_obj, session):
    """
    Recursively updates an SQLAlchemy object with values from another,
    handling nested objects and removing unused relationships.
    """
    if not source_obj:
        return

    mapper = class_mapper(target_obj.__class__)

    for prop in mapper.attrs:
        if hasattr(prop, "key"):
            attr_name = prop.key
            source_value = getattr(source_obj, attr_name, None)
            target_value = getattr(target_obj, attr_name, None)

            if isinstance(prop, RelationshipProperty):
                if prop.uselist:  # Handle list relationships
                    # source_ids = {obj.id for obj in source_value} if source_value else set()
                    target_items = list(target_value) if target_value else []

                    # Delete unused objects
                    # for obj in target_items:
                    #     if obj.id not in source_ids:
                    #         session.delete(obj)
                    #         target_items.remove(obj)

                    # Update or add new objects
                    for obj in source_value or []:
                        existing_obj = next(
                            (t for t in target_items if t.id == obj.id), None
                        )
                        if existing_obj:
                            update_sqlalchemy_object(existing_obj, obj, session)
                        else:
                            target_items.append(obj)

                    setattr(target_obj, attr_name, target_items)
                else:  # Handle single object relationships
                    if source_value is not None:
                        if target_value is None:
                            setattr(target_obj, attr_name, source_value)
                        else:
                            update_sqlalchemy_object(
                                target_value, source_value, session
                            )
            else:
                if source_value is not None:
                    setattr(target_obj, attr_name, source_value)

    session.add(target_obj)


def safe_first(query):
    """Run .first() and ensure we always get a result object."""
    result = query.first()
    if result is None:
        # Return a dummy object with all fields as 0
        from types import SimpleNamespace

        return SimpleNamespace()
    return result


def to_jsonable_dict(obj, only_changed=False):
    state = inspect(obj)
    if only_changed:
        attrs = [
            attr
            for attr in state.mapper.column_attrs
            if state.attrs[attr.key].history.has_changes()
        ]
    else:
        attrs = state.mapper.column_attrs

    raw = {attr.key: state.attrs[attr.key].value for attr in attrs}
    return jsonable_encoder(raw)


def set_related_attr(obj, rel_name: str, fk_name: str, rel_class, attr: str, value):
    rel = getattr(obj, rel_name, None)
    if rel is None:
        fk_val = getattr(obj, fk_name, None)
        if fk_val:
            session = object_session(obj)
            if session:
                rel = session.get(rel_class, fk_val)
                setattr(obj, rel_name, rel)
        if rel is None:
            rel = rel_class()
            setattr(obj, rel_name, rel)

    # find out if attr is column or relationship
    mapper = inspect(rel_class)
    if attr in mapper.relationships:
        # expect ORM objects, not dicts
        if isinstance(value, dict):
            raise ValueError(f"{attr} expects ORM objects, not dicts: {value}")
        if isinstance(value, list) and any(isinstance(v, dict) for v in value):
            raise ValueError(f"{attr} expects list of ORM objects, not dicts: {value}")
        setattr(rel, attr, value)
    else:
        # just a column
        setattr(rel, attr, value)
