from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt
import bcrypt
import os
import logging

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Leer vida del token desde .env (default: 480 minutos = 8 horas)
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# Validar SECRET_KEY al arrancar
_WEAK_KEYS = {
    "",
    "your-secret-key-here-for-local-dev-only",
    "secret-key-change-in-production",
    "secret",
    "changeme",
}

if not SECRET_KEY or SECRET_KEY in _WEAK_KEYS:
    if ENVIRONMENT == "production":
        raise RuntimeError(
            "FATAL: SECRET_KEY no configurada o es demasiado débil. "
            "Genera una con: python -c \"import secrets; print(secrets.token_hex(64))\""
        )
    else:
        # En desarrollo: advertencia, pero permite arrancar
        logger.warning(
            "⚠️  ADVERTENCIA DE SEGURIDAD: SECRET_KEY no configurada o débil. "
            "Crea un archivo .env con una clave segura antes de pasar a producción."
        )
        SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
