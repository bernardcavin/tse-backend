from uuid import UUID

from app.core.config import settings
from app.core.database import sessionmanager
from app.core.security import oauth2_scheme
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session


def get_db_session_base():
    with sessionmanager.session() as session:
        yield session

async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session_base),
) -> UUID:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        if payload is None:
            raise credentials_exception

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return UUID(user_id)


def get_db_session(user_id=Depends(get_current_user_id)):
  with sessionmanager.session() as session:
    session.info["user_id"] = user_id
    yield session