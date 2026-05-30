from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlmodel import Session, select
from app.database import get_session
from app.core.security import ALGORITHM, SECRET_KEY
from app.models import User, RoleEnum

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)

def get_current_user(
    db: Session = Depends(get_session), token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = payload.get("sub")
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    if not token_data:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = db.get(User, int(token_data))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != RoleEnum.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user

def get_current_active_operativo_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in [RoleEnum.ADMINISTRADOR, RoleEnum.OPERATIVO]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user
