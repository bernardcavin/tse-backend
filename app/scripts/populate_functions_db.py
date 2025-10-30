import datetime

from sqlalchemy.orm import Session

from app.api.auth.models import User
from app.core.database import sessionmanager
from app.core.security import pwd_context


def data_exists(db: Session):
    if (
        len(db.query(User).all()) > 1
        and db.query(User).filter_by(username="manager").first() is not None
    ):
        return True
    else:
        return False


def create_user():
    with sessionmanager.session() as session:
        manager = User(
            name="Manager",
            username="manager",
            hashed_password=pwd_context.hash("manager"),
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )

        session.add(manager)
        session.commit()
