"""
Script de Diagnóstico para Cotizador FastAPI
Ejecuta este script para verificar que todo esté configurado correctamente
"""
import sys
import os
import subprocess

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_python_version():
    print_section("1. Versión de Python")
    version = sys.version
    print(f"✓ Versión: {version}")
    if sys.version_info < (3, 10):
        print("⚠ ADVERTENCIA: Se recomienda Python 3.10 o superior")
    else:
        print("✓ Versión compatible")

def check_current_directory():
    print_section("2. Directorio Actual")
    cwd = os.getcwd()
    print(f"✓ Directorio actual: {cwd}")
    
    # Verificar que estamos en el directorio correcto
    if os.path.exists("app") and os.path.exists("requirements.txt"):
        print("✓ Estructura del proyecto detectada correctamente")
    else:
        print("✗ ERROR: No estás en el directorio raíz del proyecto")
        print("  Debes estar en el directorio que contiene la carpeta 'app' y 'requirements.txt'")

def check_virtualenv():
    print_section("3. Entorno Virtual")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Entorno virtual activado")
        print(f"  Prefix: {sys.prefix}")
    else:
        print("⚠ ADVERTENCIA: Entorno virtual NO activado")
        print("  Activa el entorno virtual:")
        print("  - Windows: venv\\Scripts\\activate")
        print("  - Linux/Mac: source venv/bin/activate")

def check_dependencies():
    print_section("4. Dependencias Instaladas")
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlmodel",
        "pandas",
        "openpyxl",
        "xhtml2pdf",
        "fpdf2",
        "jinja2",
        "pydantic-settings",
        "python-dotenv"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NO INSTALADO")
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Faltan {len(missing)} paquetes:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstala las dependencias faltantes:")
        print("  pip install -r requirements.txt")
    else:
        print("\n✓ Todas las dependencias están instaladas")

def check_directories():
    print_section("5. Directorios Necesarios")
    required_dirs = [
        "app",
        "app/api",
        "app/api/v1",
        "app/api/v1/endpoints",
        "app/core",
        "app/models",
        "app/templates",
        "app/static",
        "scripts",
        "scripts/migrations"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - NO EXISTE")
            missing_dirs.append(dir_path)
    
    # Verificar directorios que deben crearse
    optional_dirs = ["data", "logs", "temp", "app/static/reports"]
    print("\nDirectorios opcionales (se crean automáticamente):")
    for dir_path in optional_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path}")
        else:
            print(f"⚠ {dir_path} - No existe (se creará)")
    
    if missing_dirs:
        print(f"\n✗ Faltan {len(missing_dirs)} directorios obligatorios")
        print("  La estructura del proyecto está incompleta")

def check_database():
    print_section("6. Base de Datos")
    db_path = "data/database.db"
    
    if os.path.exists(db_path):
        print(f"✓ Archivo de base de datos existe: {db_path}")
        size = os.path.getsize(db_path)
        print(f"  Tamaño: {size} bytes")
        
        # Intentar conectar a la base de datos
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if tables:
                print(f"✓ Base de datos tiene {len(tables)} tablas:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("⚠ Base de datos existe pero NO tiene tablas")
                print("  Ejecuta: python scripts/migrations/init_db.py")
            
            conn.close()
        except Exception as e:
            print(f"✗ Error al conectar a la base de datos: {e}")
    else:
        print(f"✗ Base de datos NO existe: {db_path}")
        print("  Ejecuta: python scripts/migrations/init_db.py")

def check_env_file():
    print_section("7. Archivo .env")
    if os.path.exists(".env"):
        print("✓ Archivo .env existe")
    else:
        print("⚠ Archivo .env NO existe")
        print("  Ejecuta: python setup.py")
    
    if os.path.exists(".env.example"):
        print("✓ Archivo .env.example existe")
    else:
        print("✗ Archivo .env.example NO existe")

def check_imports():
    print_section("8. Prueba de Importación de Módulos")
    try:
        # Agregar directorio raíz al path
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
        sys.path.insert(0, BASE_DIR)
        
        print(f"  BASE_DIR: {BASE_DIR}")
        
        # Intentar importar módulos principales
        from app.database import create_db_and_tables, engine
        print("✓ app.database")
        
        from app.models import Customer, Product, Quote
        print("✓ app.models")
        
        from app.main import app
        print("✓ app.main")
        
        print("\n✓ Todos los módulos principales se importan correctamente")
    except Exception as e:
        print(f"✗ Error al importar módulos: {e}")
        print("  Verifica que estás en el directorio raíz del proyecto")

def main():
    print("\n" + "="*60)
    print("  DIAGNÓSTICO DEL PROYECTO COTIZADOR FASTAPI")
    print("="*60)
    
    check_python_version()
    check_current_directory()
    check_virtualenv()
    check_dependencies()
    check_directories()
    check_database()
    check_env_file()
    check_imports()
    
    print_section("RESUMEN")
    print("Si hay errores marcados con ✗, resuélvelos antes de continuar.")
    print("Si hay advertencias marcadas con ⚠, se recomienda resolverlas.")
    print("\nPara más ayuda, consulta el archivo INSTRUCCIONES_OTRA_PC.md")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
