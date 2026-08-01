from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "Cotizador"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]
    
    # Security
    SECRET_KEY: str = "secret-key-change-in-production"
    
    # Environment
    ENVIRONMENT: str = "development"

    # Zona horaria del negocio (afecta "hoy/ahora" y los cortes mensuales)
    TIMEZONE: str = "America/Mexico_City"

    # Variables consumidas por el resto del proyecto vía os.getenv / settings.
    # Declaradas aquí para que .env sea aceptado por pydantic-settings.
    CORS_ORIGINS: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_BLOCK_MINUTES: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
