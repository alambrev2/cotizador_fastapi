from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.api import deps
from app.core import security
from app.database import get_session
from app.models import User
from app.schemas import Token

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    response: Response,
    db: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = db.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    # Set HTTPOnly Cookie for browser sessions
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False  # Allow http locally
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role.value,
        "username": user.username,
    }

@router.post("/logout")
def logout(response: Response) -> Any:
    response.delete_cookie(key="access_token")
    return {"detail": "Successfully logged out"}

@router.get("/me")
def get_me(current_user: User = Depends(deps.get_current_user)) -> Any:
    """Retorna información del usuario autenticado actual."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "cliente_id": current_user.cliente_id,
    }
