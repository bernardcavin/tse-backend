from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, event, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Session,
    declarative_mixin,
    declared_attr,
    object_mapper,
    relationship,
    with_loader_criteria,
)


# ---------- CREATE ----------
@declarative_mixin
class CreateMixin:
    time_created = Column(DateTime(timezone=True), server_default=func.now())

    @declared_attr
    def created_by_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey(use_alter=True, column="users.id", ondelete="CASCADE", ))

    @declared_attr
    def created_by(cls):
        return relationship("User", foreign_keys=[cls.created_by_id])   # type: ignore

# ---------- UPDATE ----------
@declarative_mixin
class UpdateMixin:
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())

    @declared_attr
    def last_updated_by_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey(use_alter=True, column="users.id", ondelete="CASCADE", ))

    @declared_attr
    def last_updated_by(cls):
        return relationship("User", foreign_keys=[cls.last_updated_by_id])   # type: ignore

# ---------- SOFT DELETE ----------
@declarative_mixin
class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True))
    
    @declared_attr
    def deleted_by_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey(use_alter=True, column="users.id", ondelete="CASCADE", ), nullable=True)

    @declared_attr
    def deleted_by(cls):
        return relationship("User", foreign_keys=[cls.deleted_by_id], lazy="joined")  # type: ignore

    def soft_delete(self, user_id=None):
        """Mark record as deleted (instead of deleting it)."""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        if user_id:
            self.deleted_by_id = user_id


# ---------- AUTO AUDIT LISTENERS ----------
@event.listens_for(Session, "before_flush")
def auto_audit_fields(session, flush_context, instances):
    user_id = session.info.get("user_id")

    for obj in session.new:
        if hasattr(obj, "time_created") and getattr(obj, "time_created") is None:
            obj.time_created = datetime.now(timezone.utc)

        if hasattr(obj, "created_by_id") and getattr(obj, "created_by_id") is None:
            if user_id:
                obj.created_by_id = user_id

        if hasattr(obj, "last_updated"):
            obj.last_updated = datetime.now(timezone.utc)
        if hasattr(obj, "last_updated_by_id") and user_id:
            obj.last_updated_by_id = user_id

    for obj in session.dirty:
        if not session.is_modified(obj, include_collections=False):
            continue

        if hasattr(obj, "last_updated"):
            obj.last_updated = datetime.now(timezone.utc)
        if hasattr(obj, "last_updated_by_id") and user_id:
            obj.last_updated_by_id = user_id

        # Handle soft delete auditing
        if hasattr(obj, "is_deleted") and obj.is_deleted and not getattr(obj, "deleted_at", None):
            obj.deleted_at = datetime.now(timezone.utc)
            if user_id and hasattr(obj, "deleted_by_id"):
                obj.deleted_by_id = user_id


# ---------- GLOBAL FILTER ----------
@event.listens_for(Session, "do_orm_execute")
def _add_soft_delete_filter(execute_state):
    """Auto-exclude soft-deleted rows unless 'include_deleted=True' is set."""
    if not execute_state.execution_options.get("include_deleted", False):
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.is_deleted == False,   # type: ignore  # noqa: E712
                include_aliases=True,
            )
        )

@event.listens_for(Session, "before_flush")
def cascade_soft_delete(session, flush_context, instances):
    user_id = session.info.get("user_id")

    for obj in session.dirty:
        if hasattr(obj, "is_deleted") and obj.is_deleted:
            mapper = object_mapper(obj)
            for prop in mapper.relationships:
                # only cascade on delete-enabled relationships
                if not prop.cascade.delete_orphan and not prop.cascade.delete:
                    continue
                related_objs = getattr(obj, prop.key)
                if not related_objs:
                    continue

                # handle both single and list relationships
                if isinstance(related_objs, list):
                    for child in related_objs:
                        if hasattr(child, "soft_delete") and not child.is_deleted:
                            child.soft_delete(user_id=user_id)
                else:
                    if hasattr(related_objs, "soft_delete") and not related_objs.is_deleted:
                        related_objs.soft_delete(user_id=user_id)