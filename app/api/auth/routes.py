from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.auth import models, schemas
from app.api.auth.crud import (
    authenticate_user,
    can_view_all_employees,
    create_user,
    delete_user,
    get_all_employees,
    log_contribution,
    require_manager,
    update_profile,
    update_user,
)
from app.api.auth.utils import get_current_user
from app.core.dependencies import get_db_session, get_db_session_base
from app.core.schema_operations import create_api_response
from app.core.security import (
    create_access_token,
    get_current_token,
)
from app.core.utils.request import get_request

router = APIRouter(prefix="/auth")


# ---------------------------------------------------------------------------- #
#                                  USER LOGIN                                  #
# ---------------------------------------------------------------------------- #


@router.post(
    "/login",
    summary="Generate Token (JSON)",
    tags=["User"],
)
async def login_for_access_token(
    token_request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session_base),
    request=Depends(get_request),
    # user: schemas.GetUser = Depends(get_current_user),
):
    user = authenticate_user(token_request.username, token_request.password, db)
    if not user:
        return create_api_response(
            success=False,
            message="Incorrect username or password or Invalid account type",
            status_code=401,
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    log_contribution(db, user, "LOGIN", "user", user.name)
    return create_api_response(
        success=True,
        message="Login successful",
        data=schemas.TokenSchema(
            token_type="bearer",
            access_token=access_token,
        ),
    )


@router.get("/me", summary="Get details of currently logged in user", tags=["User"])
async def get_me(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
):
    return create_api_response(
        success=True,
        message="User retrieved successfully",
        data=schemas.UserSchema.model_validate(user),
    )


@router.post("/logout", summary="Logout User", tags=["User"])
async def logout(
    token: str = Depends(get_current_token),
    user: schemas.UserSchema = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
):
    log_contribution(db, user, "LOGOUT", "user", user.name)
    return create_api_response(success=True, message="Token expired successfully")


@router.put("/profile", summary="Update Own Profile", tags=["User"])
async def update_user_profile(
    profile_data: schemas.UpdateProfileSchema,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
):
    """Allow users to update their own profile data (personal fields only)"""
    updated_user = update_profile(
        db=db,
        user_id=user.id,
        username=profile_data.username,
        name=profile_data.name,
        nik=profile_data.nik,
        email=profile_data.email,
        phone_number=profile_data.phone_number,
        address=profile_data.address,
        emergency_contact_name=profile_data.emergency_contact_name,
        emergency_contact_phone=profile_data.emergency_contact_phone,
        password=profile_data.password,
    )

    log_contribution(db, user, "UPDATED", "profile", user.name)

    return create_api_response(
        success=True,
        message="Profile updated successfully",
        data=schemas.UserSchema.model_validate(updated_user),
    )


# ---------------------------------------------------------------------------- #
#                            EMPLOYEE MANAGEMENT                                #
# ---------------------------------------------------------------------------- #


@router.get(
    "/employees",
    summary="Get All Employees (Manager, HR, Finance)",
    tags=["Employee Management"],
)
async def get_employees(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
):
    # Verify user can view all employees (Manager, HR, or Finance)
    if not can_view_all_employees(user):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view all employees"
        )

    employees = get_all_employees(db)
    return create_api_response(
        success=True,
        message="Employees retrieved successfully",
        data=[schemas.UserSchema.model_validate(emp) for emp in employees],
    )


@router.get(
    "/employees/{employee_id}",
    summary="Get Employee by ID (Manager, HR, Finance)",
    tags=["Employee Management"],
)
async def get_employee(
    employee_id: UUID,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
):
    # Verify user can view all employees (Manager, HR, or Finance)
    if not can_view_all_employees(user):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view employee details"
        )

    # Get the employee
    employee = db.query(models.User).filter(models.User.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return create_api_response(
        success=True,
        message="Employee retrieved successfully",
        data=schemas.UserSchema.model_validate(employee),
    )


@router.post(
    "/employees",
    summary="Create Employee (Manager Only)",
    tags=["Employee Management"],
)
async def create_employee(
    employee_data: schemas.CreateEmployeeSchema,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
):
    # Verify user is manager
    require_manager(user)

    # Convert string role to enum
    role = (
        models.UserRole.MANAGER
        if employee_data.role == "MANAGER"
        else models.UserRole.EMPLOYEE
    )

    new_employee = create_user(
        db=db,
        username=employee_data.username,
        name=employee_data.name,
        password=employee_data.password,
        role=role,
        employee_num=employee_data.employee_num,
        email=employee_data.email,
        nik=employee_data.nik,
        position=employee_data.position,
        department=employee_data.department,
        phone_number=employee_data.phone_number,
        hire_date=employee_data.hire_date.isoformat() if employee_data.hire_date else None,
        address=employee_data.address,
        emergency_contact_name=employee_data.emergency_contact_name,
        emergency_contact_phone=employee_data.emergency_contact_phone,
    )

    log_contribution(db, user, "CREATED", "employee", new_employee.name)

    return create_api_response(
        success=True,
        message="Employee created successfully",
        data=schemas.UserSchema.model_validate(new_employee),
    )


@router.put(
    "/employees/{employee_id}",
    summary="Update Employee (Manager Only)",
    tags=["Employee Management"],
)
async def update_employee(
    employee_id: UUID,
    employee_data: schemas.UpdateEmployeeSchema,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
):
    # Verify user is manager
    require_manager(user)

    # Convert string role to enum if provided
    role = None
    if employee_data.role:
        role = (
            models.UserRole.MANAGER
            if employee_data.role == "MANAGER"
            else models.UserRole.EMPLOYEE
        )

    updated_employee = update_user(
        db=db,
        user_id=employee_id,
        username=employee_data.username,
        name=employee_data.name,
        password=employee_data.password,
        role=role,
        employee_num=employee_data.employee_num,
        email=employee_data.email,
        nik=employee_data.nik,
        position=employee_data.position,
        department=employee_data.department,
        phone_number=employee_data.phone_number,
        hire_date=employee_data.hire_date.isoformat() if employee_data.hire_date else None,
        address=employee_data.address,
        emergency_contact_name=employee_data.emergency_contact_name,
        emergency_contact_phone=employee_data.emergency_contact_phone,
    )

    log_contribution(db, user, "UPDATED", "employee", updated_employee.name)

    return create_api_response(
        success=True,
        message="Employee updated successfully",
        data=schemas.UserSchema.model_validate(updated_employee),
    )


@router.delete(
    "/employees/{employee_id}",
    summary="Delete Employee (Manager Only)",
    tags=["Employee Management"],
)
async def delete_employee(
    employee_id: UUID,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    request=Depends(get_request),
):
    # Verify user is manager
    require_manager(user)

    delete_user(db, employee_id)
    log_contribution(db, user, "DELETED", "employee", str(employee_id))

    return create_api_response(
        success=True,
        message="Employee deleted successfully",
    )

