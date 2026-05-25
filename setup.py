"""
Script de inicialización del proyecto Cotizador FastAPI
Crea todos los directorios necesarios y configura el entorno
"""
import os
import sys

def setup_project():
    """Crea los directorios necesarios para el proyecto"""
    
    # Obtener el directorio base del script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Directorios a crear
    directories = [
        "data",
        "logs",
        "temp",
        "app/static/reports",
    ]
    
    print("🚀 Inicializando proyecto Cotizador FastAPI...")
    print(f"📁 Directorio base: {BASE_DIR}\n")
    
    # Crear cada directorio
    for directory in directories:
        dir_path = os.path.join(BASE_DIR, directory)
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Directorio creado/verificado: {directory}")
        except Exception as e:
            print(f"❌ Error creando directorio {directory}: {e}")
            return False
    
    # Verificar archivo .env
    env_example = os.path.join(BASE_DIR, ".env.example")
    env_file = os.path.join(BASE_DIR, ".env")
    
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            print(f"\n⚠️  No se encontró archivo .env")
            print(f"📝 Copiando .env.example a .env...")
            try:
                import shutil
                shutil.copy(env_example, env_file)
                print(f"✅ Archivo .env creado desde .env.example")
                print(f"⚠️  Por favor revisa y ajusta los valores en .env según tu entorno")
            except Exception as e:
                print(f"❌ Error copiando .env.example: {e}")
                return False
        else:
            print(f"\n⚠️  No se encontró .env.example")
            print(f"📝 Creando archivo .env básico...")
            try:
                with open(env_file, "w") as f:
                    f.write("# Configuración del Proyecto Cotizador FastAPI\n")
                    f.write("PROJECT_NAME=Cotizador\n")
                    f.write("PROJECT_VERSION=1.0.0\n")
                    f.write("BACKEND_CORS_ORIGINS=[\"*\"]\n")
                    f.write("SECRET_KEY=secret-key-change-in-production\n")
                    f.write("ENVIRONMENT=development\n")
                print(f"✅ Archivo .env básico creado")
            except Exception as e:
                print(f"❌ Error creando .env: {e}")
                return False
    else:
        print(f"\n✅ Archivo .env ya existe")
    
    print("\n" + "="*50)
    print("✨ Inicialización completada exitosamente!")
    print("="*50)
    print("\n📋 Pasos siguientes:")
    print("1. Crear entorno virtual: python -m venv venv")
    print("2. Activar entorno virtual:")
    print("   - Windows: venv\\Scripts\\activate")
    print("   - Linux/Mac: source venv/bin/activate")
    print("3. Instalar dependencias: pip install -r requirements.txt")
    print("4. Inicializar base de datos: python scripts/migrations/init_db.py")
    print("5. Iniciar servidor: uvicorn app.main:app --reload")
    print("\n🌐 El servidor estará disponible en: http://localhost:8000")
    print("="*50)
    
    return True

if __name__ == "__main__":
    success = setup_project()
    sys.exit(0 if success else 1)
