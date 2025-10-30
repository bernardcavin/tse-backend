import contextlib
import uuid
from typing import Any, Iterator

from app.core.config import settings
from app.utils.model_bases.audit_base import CreateMixin, SoftDeleteMixin, UpdateMixin
from app.utils.models_utils import to_jsonable_dict
from sqlalchemy import (
    JSON,
    UUID,
    Boolean,
    Column,
    Connection,
    DateTime,
    String,
    create_engine,
    event,
    func,
    inspect,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker


class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_engine(host, **engine_kwargs)
        self._sessionmaker = sessionmaker(
            autocommit=False, bind=self._engine, autoflush=True
        )

    def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.contextmanager
    def connect(self) -> Iterator[Connection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise

    @contextlib.contextmanager
    def session(self) -> Iterator[Session]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()  # type: ignore
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


sessionmanager = DatabaseSessionManager(
    str(settings.DATABASE_URI), {"echo": settings.SQL_ECHO}
)

DeclarativeBase = declarative_base()

class Base(DeclarativeBase, CreateMixin, UpdateMixin, SoftDeleteMixin):
    __abstract__ = True



class DataChange(Base):
    __tablename__ = "data_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    table_name = Column(String, nullable=False)
    action = Column(String, nullable=False)  # INSERT, UPDATE, DELETE
    row_id = Column(String, nullable=True)
    changed_data = Column(JSON, nullable=True)
    success = Column(Boolean, default=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

def track_changes(session, flush_context):
    # INSERT
    for obj in session.new:
        if isinstance(obj, Base) and obj.__tablename__ not in ["data_changes", "user_actions"]:
            change = DataChange(
                table_name=obj.__tablename__,
                action="INSERT",
                row_id=str(getattr(obj, "id", None)),
                changed_data=to_jsonable_dict(obj),
            )
            session.add(change)

    # UPDATE
    for obj in session.dirty:
        state = inspect(obj)
        if state.modified and obj.__tablename__ not in ["data_changes", "user_actions"]:
            change = DataChange(
                table_name=obj.__tablename__,
                action="UPDATE",
                row_id=str(getattr(obj, "id", None)),
                changed_data=to_jsonable_dict(obj, only_changed=True),
            )
            session.add(change)

    # DELETE
    for obj in session.deleted:
        if isinstance(obj, Base) and obj.__tablename__ not in ["data_changes", "user_actions"]:
            change = DataChange(
                table_name=obj.__tablename__,
                action="DELETE",
                row_id=str(getattr(obj, "id", None)),
                changed_data=to_jsonable_dict(obj),
            )
            session.add(change)

event.listen(Session, "after_flush", track_changes)