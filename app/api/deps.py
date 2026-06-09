from typing import Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlmodel import Session, select
from app.database import get_session
from app.core.security import ALGORITHM, SECRET_KEY
from app.models import User, RoleEnum

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)

def get_current_user(
    request: Request,
    db: Session = Depends(get_session),
    token: str = Depends(reusable_oauth2)
) -> User:
    if not token:
        token = request.cookies.get("access_token")
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
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
    if current_user.role != RoleEnum.Administrador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user

def get_current_active_operativo_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in [RoleEnum.Administrador, RoleEnum.Operativo]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user

def get_current_active_cliente(
    current_user: User = Depends(get_current_user),
) -> User:
    """Permite solo al perfil Cliente acceder a su dashboard simplificado."""
    if current_user.role != RoleEnum.Cliente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user

def require_role(*roles: RoleEnum):
    """Factory de dependencia: permite cualquiera de los roles indicados."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este recurso"
            )
        return current_user
    return dependency

def get_current_user_pages(
    request: Request,
    db: Session = Depends(get_session)
) -> User:
    """Para rutas de paginas HTML: redirige a /login si no esta autenticado."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = payload.get("sub")
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    user = db.get(User, int(token_data))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )
    return user


def get_admin_only_page(
    request: Request,
    db: Session = Depends(get_session)
) -> User:
    """Para paginas exclusivas de Administrador: redirige a /login o /unauthorized."""
    user = get_current_user_pages(request, db)
    if user.role != RoleEnum.Administrador:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/unauthorized"}
        )
    return user


def get_operativo_or_admin_page(
    request: Request,
    db: Session = Depends(get_session)
) -> User:
    """Para paginas de Operativo o Admin."""
    user = get_current_user_pages(request, db)
    if user.role not in [RoleEnum.Administrador, RoleEnum.Operativo]:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/unauthorized"}
        )
    return user

