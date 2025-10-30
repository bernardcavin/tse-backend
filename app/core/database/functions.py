import os

from sqlalchemy import text

from app.core.database import sessionmanager


def drop_existing_data():
    with sessionmanager.session() as session:
        from app.core import models  # noqa: F401

        engine = sessionmanager._engine

        dialect = engine.dialect.name  # type: ignore

        if dialect == "sqlite":
            db_url = str(engine.url)  # type: ignore
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    session.close()
                    engine.dispose()  # type: ignore
                    os.remove(db_path)
                    print(f"🧨 Nuked SQLite DB file: {db_path}")
            else:
                print("⚠️ SQLite memory DB or invalid path — skipping nuke.")
        else:
            drop_schema_query = text("DROP SCHEMA IF EXISTS public CASCADE;")
            create_schema_query = text("CREATE SCHEMA public;")
            session.execute(drop_schema_query)
            session.execute(create_schema_query)
            session.commit()
