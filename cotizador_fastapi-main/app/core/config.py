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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
