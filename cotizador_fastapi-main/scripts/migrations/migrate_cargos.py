import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import SQLModel
from app.database import engine
from app.models import AccountCharge

# Crear tablas faltantes
print("Creando tabla accountcharge si no existe...")
SQLModel.metadata.create_all(engine)
print("Migración completada con éxito.")
