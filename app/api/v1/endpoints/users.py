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
    from sqlalchemy.orm import selectinload
    query = select(User).options(selectinload(User.cliente_vinculado))
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


# ── GENERACIÓN MASIVA DE CUENTAS DE CLIENTES ─────────────────────────────────

import secrets
import string

def _generar_contrasena(longitud: int = 12) -> str:
    """Genera contraseña segura aleatoria."""
    chars = string.ascii_letters + string.digits + "!@#$%"
    pwd = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%"),
    ]
    pwd += [secrets.choice(chars) for _ in range(longitud - 4)]
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)

def _generar_username(email: str, nombre: str, db: Session) -> str:
    """Genera username único a partir del email."""
    base = email.split("@")[0].lower() if email else nombre.lower().replace(" ", "")
    base = "".join(c for c in base if c.isalnum() or c == ".")[:30]
    username = base
    counter = 1
    while db.exec(select(User).where(User.username == username)).first():
        username = f"{base}{counter}"
        counter += 1
    return username


@router.post("/generar-cuentas-clientes")
def generar_cuentas_clientes(
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    """
    Genera automáticamente cuentas de acceso (rol Cliente) para todos los clientes
    que aún no tengan un usuario vinculado. Retorna la lista de cuentas creadas.
    """
    customers = db.exec(select(Customer)).all()
    creados = []
    omitidos = 0
    vinculados = 0

    for cliente in customers:
        if not cliente.email:
            omitidos += 1
            continue

        existing = db.exec(select(User).where(User.email == cliente.email)).first()
        if existing:
            # Vincular si existe pero no está enlazado al cliente
            if not existing.cliente_id:
                existing.cliente_id = cliente.id
                db.add(existing)
                vinculados += 1
            else:
                omitidos += 1
            continue

        username = _generar_username(cliente.email, cliente.nombre, db)
        password = _generar_contrasena()

        import secrets
        from datetime import datetime, timedelta
        token = secrets.token_urlsafe(32)

        nuevo = User(
            username=username,
            email=cliente.email,
            role=RoleEnum.Cliente,
            hashed_password=get_password_hash(password),
            cliente_id=cliente.id,
            is_active=True,
            magic_token=token,
            magic_token_expires=datetime.utcnow() + timedelta(days=30),
        )
        db.add(nuevo)
        creados.append({
            "nombre_cliente": cliente.nombre,
            "email": cliente.email,
            "username": username,
            "password": password,
            "telefono": cliente.telefono,
            "magic_token": token,
        })

    db.commit()

    return {
        "creados": len(creados),
        "vinculados": vinculados,
        "omitidos": omitidos,
        "cuentas": creados,
    }




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
    import secrets
    from datetime import datetime, timedelta
    user = _get_user_or_404(user_id, db)
    new_password = payload.get("password", "")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    user.hashed_password = get_password_hash(new_password)
    
    # También generar y guardar el token mágico
    token = secrets.token_urlsafe(32)
    user.magic_token = token
    user.magic_token_expires = datetime.utcnow() + timedelta(days=30)
    
    db.add(user)
    db.commit()
    return {
        "detail": "Contraseña actualizada correctamente",
        "magic_token": token
    }

@router.post("/{user_id}/magic-token")
def generate_user_magic_token(
    user_id: int,
    db: Session = Depends(get_session),
    _admin: User = Depends(get_current_active_admin),
):
    import secrets
    from datetime import datetime, timedelta
    user = _get_user_or_404(user_id, db)
    token = secrets.token_urlsafe(32)
    user.magic_token = token
    user.magic_token_expires = datetime.utcnow() + timedelta(days=30)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"magic_token": token}


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
    
    is_client = user.role == RoleEnum.Cliente or user.role == "Cliente"
    customer_id = user.cliente_id
    
    try:
        # 1. Eliminar al usuario primero y guardar para evitar restricciones de llave foránea
        db.delete(user)
        db.commit()
        
        # 2. Eliminación en cascada si es un usuario Cliente
        if is_client and customer_id:
            from app.models import Customer, Quote, QuoteItem, Payment, AccountCharge
            customer = db.get(Customer, customer_id)
            if customer:
                # Eliminar Quotes y QuoteItems asociados
                quotes = db.exec(select(Quote).where(Quote.cliente_id == customer.id)).all()
                for q in quotes:
                    items = db.exec(select(QuoteItem).where(QuoteItem.cotizacion_id == q.id)).all()
                    for item in items:
                        db.delete(item)
                    # Eliminar pagos ligados a la cotización
                    pagos_quote = db.exec(select(Payment).where(Payment.quote_id == q.id)).all()
                    for pq in pagos_quote:
                        db.delete(pq)
                    db.delete(q)
                
                # Eliminar Pagos directos del cliente
                pagos = db.exec(select(Payment).where(Payment.cliente_id == customer.id)).all()
                for p in pagos:
                    db.delete(p)
                    
                # Eliminar Cargos
                cargos = db.exec(select(AccountCharge).where(AccountCharge.cliente_id == customer.id)).all()
                for c in cargos:
                    db.delete(c)
                    
                # Eliminar todos los usuarios (cuentas) asociados al cliente
                usuarios = db.exec(select(User).where(User.cliente_id == customer.id)).all()
                for u in usuarios:
                    if u.id != user.id: # El usuario actual ya está marcado para borrar
                        db.delete(u)
                    
                # Eliminar el Customer
                db.delete(customer)

        db.commit()
        return {"detail": "Usuario eliminado exitosamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
