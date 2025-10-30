from uuid import UUID

from app.api.auth.models import User
from app.core.dependencies import get_current_user_id, get_db_session_base
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db_session_base),
) -> User:
    
    user = db.query(User).filter_by(id=user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user
