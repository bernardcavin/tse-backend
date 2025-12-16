from typing import List, Literal, Optional

from fastapi import HTTPException, status
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


# ---------------------------------------------------------------------------- #
#                              EMPLOYEE MANAGEMENT                              #
# ---------------------------------------------------------------------------- #


def get_all_employees(db: Session) -> List[models.User]:
    """Get all users (employees and managers)"""
    return db.query(models.User).all()


def create_user(
    db: Session,
    username: str,
    name: str,
    password: str,
    role: models.UserRole = models.UserRole.EMPLOYEE,
    employee_num: Optional[str] = None,
    email: Optional[str] = None,
    nik: Optional[str] = None,
    position: Optional[str] = None,
    department: Optional[str] = None,
    phone_number: Optional[str] = None,
    hire_date: Optional[str] = None,
    address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None,
) -> models.User:
    """Create a new user (employee or manager)"""
    # Check if username already exists
    existing_user = get_user_by_username(db, username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    from datetime import datetime

    hashed_password = pwd_context.hash(password)
    new_user = models.User(
        username=username,
        name=name,
        employee_num=employee_num,
        email=email,
        nik=nik,
        position=position,
        department=department,
        phone_number=phone_number,
        hire_date=datetime.fromisoformat(hire_date) if hire_date else None,
        address=address,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_phone=emergency_contact_phone,
        hashed_password=hashed_password,
        role=role,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(
    db: Session,
    user_id,
    username: Optional[str] = None,
    name: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[models.UserRole] = None,
    employee_num: Optional[str] = None,
    email: Optional[str] = None,
    nik: Optional[str] = None,
    position: Optional[str] = None,
    department: Optional[str] = None,
    phone_number: Optional[str] = None,
    hire_date: Optional[str] = None,
    address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None,
) -> models.User:
    """Update user details"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if username:
        # Check if new username is taken by another user
        existing_user = get_user_by_username(db, username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
        user.username = username

    if name:
        user.name = name

    if employee_num is not None:
        user.employee_num = employee_num

    if email is not None:
        user.email = email

    if nik is not None:
        user.nik = nik

    if position is not None:
        user.position = position

    if department is not None:
        user.department = department

    if phone_number is not None:
        user.phone_number = phone_number

    if hire_date is not None:
        from datetime import datetime
        user.hire_date = datetime.fromisoformat(hire_date) if hire_date else None

    if address is not None:
        user.address = address

    if emergency_contact_name is not None:
        user.emergency_contact_name = emergency_contact_name

    if emergency_contact_phone is not None:
        user.emergency_contact_phone = emergency_contact_phone

    if password:
        user.hashed_password = pwd_context.hash(password)

    if role:
        user.role = role

    from datetime import datetime

    user.updated_at = datetime.now()

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id) -> bool:
    """Delete a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()
    return True


# ---------------------------------------------------------------------------- #
#                          ROLE-BASED AUTHORIZATION                            #
# ---------------------------------------------------------------------------- #


def require_manager(user: models.User):
    """Dependency to require manager role"""
    if user.role != models.UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation requires manager privileges",
        )
    return user

