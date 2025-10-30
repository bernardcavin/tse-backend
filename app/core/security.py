from datetime import datetime, timedelta
from functools import wraps

from app.core.config import settings
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.ROOT_PATH}/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_token(token: str = Depends(oauth2_scheme)) -> str:
    return token


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def authorize(role: list):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("user")
            if user is not None:
                user_role = user.role.value.lower()
                if user_role not in [role.lower() for role in role]:
                    raise HTTPException(
                        status_code=403,
                        detail="User is not authorized to access this resource",
                    )
            else:
                raise HTTPException(status_code=401, detail="Unauthorized")
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def refresh_token(current_token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            current_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        new_payload = payload.copy()
        expire = datetime.now() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        new_payload["exp"] = expire
        new_token = jwt.encode(
            new_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return {"access_token": new_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token for refresh",
            headers={"WWW-Authenticate": "Bearer"},
        )