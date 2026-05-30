"""
Script para exportar/importar la base de datos SQLite
Permite transferir datos entre computadoras
"""
import sys
import os
import shutil
from datetime import datetime

# Agregar el directorio raíz del proyecto al sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def export_database():
    """Exporta la base de datos a un archivo con fecha"""
    db_source = os.path.join(BASE_DIR, "data", "database.db")
    
    if not os.path.exists(db_source):
        print(f"❌ Error: No existe la base de datos en {db_source}")
        return False
    
    # Crear directorio de backups si no existe
    backup_dir = os.path.join(BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Crear nombre de archivo con fecha
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"database_backup_{timestamp}.db")
    
    try:
        shutil.copy2(db_source, backup_file)
        size = os.path.getsize(backup_file)
        print(f"✅ Base de datos exportada exitosamente")
        print(f"   Archivo: {backup_file}")
        print(f"   Tamaño: {size} bytes ({size/1024:.2f} KB)")
        print(f"\n📋 Para transferir a otra computadora:")
        print(f"   1. Copia el archivo: {backup_file}")
        print(f"   2. Pégalo en la otra computadora en la carpeta 'data/'")
        print(f"   3. Renómbralo a 'database.db'")
        return True
    except Exception as e:
        print(f"❌ Error al exportar: {e}")
        return False

def import_database(backup_file):
    """Importa una base de datos desde un archivo de backup"""
    db_destination = os.path.join(BASE_DIR, "data", "database.db")
    
    if not os.path.exists(backup_file):
        print(f"❌ Error: No existe el archivo de backup {backup_file}")
        return False
    
    # Crear directorio data si no existe
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Hacer backup del archivo actual si existe
        if os.path.exists(db_destination):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            old_backup = os.path.join(data_dir, f"database_old_{timestamp}.db")
            shutil.copy2(db_destination, old_backup)
            print(f"📦 Backup de base de datos actual guardado en: {old_backup}")
        
        # Copiar el nuevo archivo
        shutil.copy2(backup_file, db_destination)
        size = os.path.getsize(db_destination)
        print(f"✅ Base de datos importada exitosamente")
        print(f"   Archivo: {db_destination}")
        print(f"   Tamaño: {size} bytes ({size/1024:.2f} KB)")
        print(f"\n🚀 Reinicia el servidor para ver los datos")
        return True
    except Exception as e:
        print(f"❌ Error al importar: {e}")
        return False

def main():
    print("="*60)
    print("  EXPORTAR/IMPORTAR BASE DE DATOS")
    print("="*60)
    
    print("\nOpciones:")
    print("1. Exportar base de datos (para transferir a otra PC)")
    print("2. Importar base de datos (desde archivo de backup)")
    
    choice = input("\nSelecciona una opción (1 o 2): ").strip()
    
    if choice == "1":
        export_database()
    elif choice == "2":
        backup_file = input("Ingresa la ruta del archivo de backup: ").strip()
        import_database(backup_file)
    else:
        print("❌ Opción no válida")

if __name__ == "__main__":
    main()
