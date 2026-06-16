from datetime import timedelta, datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.api import deps
from app.core import security
from app.database import get_session
from app.models import User
from app.schemas import Token
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── Rate Limiting (en memoria, sin Redis) ────────────────────────────────────
# { "ip": {"count": N, "blocked_until": datetime | None, "last_attempt": datetime} }
_login_attempts: dict[str, dict] = {}

MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
BLOCK_MINUTES = int(os.getenv("LOGIN_BLOCK_MINUTES", "5"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


def _get_client_ip(request: Request) -> str:
    """Extrae la IP real del cliente, considerando proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> None:
    """Lanza 429 si la IP está bloqueada por demasiados intentos fallidos."""
    record = _login_attempts.get(ip)
    if not record:
        return

    blocked_until = record.get("blocked_until")
    if blocked_until and datetime.utcnow() < blocked_until:
        remaining = int((blocked_until - datetime.utcnow()).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Demasiados intentos fallidos. Intenta de nuevo en {remaining} minuto(s)."
        )
    elif blocked_until and datetime.utcnow() >= blocked_until:
        # Bloqueo expirado — reiniciar contador
        _login_attempts.pop(ip, None)


def _record_failed_attempt(ip: str, username: str) -> None:
    """Registra un intento fallido. Bloquea la IP si supera el límite."""
    record = _login_attempts.setdefault(ip, {"count": 0, "blocked_until": None})
    record["count"] += 1
    record["last_attempt"] = datetime.utcnow()

    logger.warning(
        f"Login fallido | IP: {ip} | usuario: '{username}' | "
        f"intento #{record['count']}/{MAX_ATTEMPTS}"
    )

    if record["count"] >= MAX_ATTEMPTS:
        record["blocked_until"] = datetime.utcnow() + timedelta(minutes=BLOCK_MINUTES)
        logger.warning(
            f"IP {ip} BLOQUEADA por {BLOCK_MINUTES} minutos "
            f"después de {MAX_ATTEMPTS} intentos fallidos."
        )


def _clear_attempts(ip: str) -> None:
    """Limpia el contador al hacer login exitoso."""
    _login_attempts.pop(ip, None)


# ─── Endpoint de Login ─────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
def login_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    ip = _get_client_ip(request)

    # 1. Verificar rate limit ANTES de consultar la BD
    _check_rate_limit(ip)

    # 2. Buscar usuario y validar credenciales
    user = db.exec(select(User).where(User.username == form_data.username)).first()

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        # Mensaje genérico — no revelar si el usuario existe o no
        _record_failed_attempt(ip, form_data.username)
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Cuenta inactiva")

    # 3. Login exitoso — limpiar intentos previos
    _clear_attempts(ip)
    logger.info(f"Login exitoso | usuario: '{user.username}' | IP: {ip}")

    # 4. Generar token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(user.id, expires_delta=access_token_expires)

    # 5. Cookie reforzada
    is_production = ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,                          # No accesible desde JS
        max_age=security.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="strict",                      # Protege contra CSRF
        secure=is_production,                   # HTTPS solo en producción
        path="/",
    )

    # 6. No retornar el token en el body (solo en cookie)
    return {
        "access_token": "",          # Vacío — el token real viaja solo en cookie
        "token_type": "bearer",
        "role": user.role.value,
        "username": user.username,
    }


@router.post("/logout")
def logout(response: Response) -> Any:
    response.delete_cookie(key="access_token", path="/", samesite="strict")
    return {"detail": "Sesión cerrada correctamente"}


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

