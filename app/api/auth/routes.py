from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.auth import models, schemas
from app.api.auth.crud import (
    authenticate_user,
    log_contribution,
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
