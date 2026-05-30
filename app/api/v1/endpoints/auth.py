from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
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
    db: Session = Depends(get_session), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = db.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
