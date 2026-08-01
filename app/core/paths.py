"""Rutas centralizadas del proyecto.

Toda referencia a directorios del proyecto debe salir de aquí en lugar de
duplicar cadenas de ``os.path.dirname(...)`` en cada módulo.
"""
from pathlib import Path

# Raíz del proyecto: cotizador_fastapi/
BASE_DIR = Path(__file__).resolve().parents[2]

# Directorios estándar
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
REPORTS_DIR = STATIC_DIR / "reports"
