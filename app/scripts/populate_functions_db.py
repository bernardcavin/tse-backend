import datetime

from sqlalchemy.orm import Session

from app.api.auth.models import User, UserRole
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


def create_user(
  db,
  username,
  name,
  password,
  role
):

    manager = User(
        name=name,
        username=username,
        role=role,
        hashed_password=pwd_context.hash(password),
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )

    db.add(manager)
    db.commit()

def create_users():
    """Create sample manager and employee users for testing"""
    with sessionmanager.session() as db:

      create_user(
                  db=db,
                  username="manager",
                  name="Test Manager",
                  password="manager123",
                  role=UserRole.MANAGER,
              )
      create_user(
                  db=db,
                  username="employee",
                  name="Test Employee",
                  password="employee123",
                  role=UserRole.EMPLOYEE,
              )
