from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import Base, sessionmanager


def drop_existing_data(db: Session):
    drop_schema_query = text("DROP SCHEMA IF EXISTS public CASCADE;")
    create_schema_query = text("CREATE SCHEMA public;")

    db.execute(drop_schema_query)
    db.execute(create_schema_query)

    db.commit()


def reset_public_db():
    with sessionmanager.session() as session:
        from app.core import models  # noqa: F401

        drop_existing_data(session)
        Base.metadata.create_all(bind=sessionmanager._engine)


def delete_all_data():
    with sessionmanager.session() as session:
        from app.core import models  # noqa: F401

        drop_existing_data(session)
