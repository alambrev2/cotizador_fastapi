"""
CRUD completo de Usuarios — exclusivo para Administrador.
Endpoints:
  GET    /api/v1/users/           → lista todos
  POST   /api/v1/users/           → crea (operativo o cliente)
  GET    /api/v1/users/{id}       → detalle
  PUT    /api/v1/users/{id}       → edita
  DELETE /api/v1/users/{id}       → elimina (soft-disable o hard delete)
  PUT    /api/v1/users/{id}/toggle → activa / desactiva
  POST   /api/v1/users/{id}/reset-password → resetea contraseña
  GET    /api/v1/users/customers-without-user → clientes sin cuenta
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.api.deps import get_current_active_admin
from app.database import get_session
from app.models import User, Customer, RoleEnum
from app.core.security import get_password_hash
from app.schemas import UserCreate, UserRead, UserUpdate, UserAdminCreate

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_user_or_404(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# ── LIST ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[UserRead])
def list_users(
    role: Optional[str] = Query(None),
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    return db.exec(query.order_by(User.id.desc())).all()


# ── CLIENTES SIN CUENTA ───────────────────────────────────────────────────────

@router.get("/customers-without-user")
def customers_without_user(
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    """Retorna los clientes que aún no tienen un usuario vinculado."""
    customers_with_user_ids = db.exec(
        select(User.cliente_id).where(User.cliente_id != None)
    ).all()
    query = select(Customer)
    if customers_with_user_ids:
        query = query.where(Customer.id.not_in(customers_with_user_ids))
    customers = db.exec(query.order_by(Customer.nombre)).all()
    return [{"id": c.id, "nombre": c.nombre, "email": c.email} for c in customers]


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=UserRead, status_code=201)
def create_user(
    payload: UserAdminCreate,
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    # Unicidad username
    if db.exec(select(User).where(User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    # Unicidad email
    if db.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
    # Si se vincula cliente, verificar que exista
    if payload.cliente_id:
        if not db.get(Customer, payload.cliente_id):
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

    user = User(
        username=payload.username,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        cliente_id=payload.cliente_id,
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── READ ──────────────────────────────────────────────────────────────────────

@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    return _get_user_or_404(user_id, db)


# ── UPDATE ────────────────────────────────────────────────────────────────────

@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    user = _get_user_or_404(user_id, db)

    if payload.username and payload.username != user.username:
        if db.exec(select(User).where(User.username == payload.username)).first():
            raise HTTPException(status_code=400, detail="Nombre de usuario ya en uso")
        user.username = payload.username

    if payload.email and payload.email != user.email:
        if db.exec(select(User).where(User.email == payload.email)).first():
            raise HTTPException(status_code=400, detail="Correo ya en uso")
        user.email = payload.email

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.cliente_id is not None:
        if payload.cliente_id == 0:
            user.cliente_id = None
        else:
            if not db.get(Customer, payload.cliente_id):
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            user.cliente_id = payload.cliente_id

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── TOGGLE ACTIVE ─────────────────────────────────────────────────────────────

@router.put("/{user_id}/toggle", response_model=UserRead)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    user = _get_user_or_404(user_id, db)
    user.is_active = not user.is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── RESET PASSWORD ────────────────────────────────────────────────────────────

@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: dict,
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    user = _get_user_or_404(user_id, db)
    new_password = payload.get("password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    return {"detail": "Contraseña actualizada correctamente"}


# ── DELETE ────────────────────────────────────────────────────────────────────

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_session),
    admin: User = Depends(get_current_active_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    user = _get_user_or_404(user_id, db)
    db.delete(user)
    db.commit()
    return {"detail": "Usuario eliminado"}
