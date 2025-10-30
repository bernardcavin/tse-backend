from typing import Literal, Optional

from sqlalchemy.orm import Session

from app.api.auth import models
from app.core.security import pwd_context

# ---------------------------------------------------------------------------- #
#                                  USER LOGIN                                  #
# ---------------------------------------------------------------------------- #


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db: Session):
    user = get_user_by_username(db, username)

    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


def log_contribution(
    db: Session,
    user,
    action: Literal[
        "CREATED",
        "UPDATED",
        "EDITED",
        "DELETED",
        "APPROVED",
        "REJECTED",
        "SUBMITTED",
        "REVIEWED",
        "LOGIN",
        "LOGOUT",
    ],
    entity: str,
    entity_name: Optional[str] = None,
):
    """
    Inserts a user contribution entry in human-readable format.
    """

    username = user.username if user else "Someone"

    if action == "CREATED":
        description = f"{username} created a new {entity}" + (
            f" named '{entity_name}'" if entity_name else ""
        )
    if action == "UPDATED":
        description = f"{username} updated {entity}" + (
            f" '{entity_name}'" if entity_name else ""
        )
    elif action == "EDITED":
        description = f"{username} edited {entity}" + (
            f" '{entity_name}'" if entity_name else ""
        )
    elif action == "DELETED":
        description = f"{username} deleted {entity}" + (
            f" '{entity_name}'" if entity_name else ""
        )
    elif action == "APPROVED":
        description = f"{username} approved the {entity}" + (
            f" '{entity_name}'" if entity_name else ""
        )
    elif action == "REJECTED":
        description = f"{username} rejected the {entity}" + (
            f" '{entity_name}'" if entity_name else ""
        )
    elif action == "SUBMITTED":
        description = f"{username} submitted a {entity}" + (
            f" '{entity_name}'" if entity_name else ""
        )
    elif action == "REVIEWED":
        description = f"{username} reviewed the {entity}" + (
            f" '{entity_name}'" if entity_name else ""
        )
    elif action == "LOGIN":
        description = f"{username} logged in"
    elif action == "LOGOUT":
        description = f"{username} logged out"
    else:
        description = f"{username} performed {action} on {entity}" + (
            f" '{entity_name}'" if entity_name else ""
        )

    contribution = models.UserAction(
        user_id=user.id if user else None,
        action=action,
        entity=entity,
        entity_name=entity_name,
        description=description,
    )

    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    return contribution
