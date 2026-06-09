# 📊 Cotizador Pro - FastAPI

Sistema moderno y profesional de cotizaciones, gestión de clientes, control de inventario y facturación/pagos, construido con **FastAPI** y **SQLModel**.

---

## 🌟 Características Principales

*   **👥 Gestión de Clientes**: Registro completo de clientes, saldos iniciales y tracking de consumo anual.
*   **📦 Control de Inventario**: Gestión de productos con soporte para precios de menudeo, mayoreo y alertas de inventario mínimo.
*   **📄 Cotizaciones en PDF**: Generación automatizada de cotizaciones profesionales, notas de remisión y estados de cuenta en formato PDF.
*   **💰 Control Financiero y Pagos**: Dashboard con balances netos, cálculo automatizado de ingresos/gastos y conciliación de saldos de clientes.
*   **📥 Importación Inteligente (Excel)**: Módulo de importación masiva de productos y clientes desde Excel con validación de datos en tiempo real y reversión en caso de errores.

---

## 📁 Estructura del Proyecto

```text
cotizador_fastapi-main/
├── app/                        # Aplicación principal
│   ├── api/v1/endpoints/       # Controladores de la API (clientes, productos, etc.)
│   ├── core/                   # Configuraciones del sistema y utilidades de PDF
│   ├── schemas/                # Modelos de validación de datos (Pydantic)
│   ├── static/                 # Archivos estáticos frontend (CSS, JS)
│   ├── templates/              # Vistas HTML y plantillas para PDFs Jinja2
│   ├── database.py             # Configuración de base de datos (SQLite)
│   ├── models.py               # Modelos de base de datos (SQLModel)
│   └── main.py                 # Punto de entrada de FastAPI
├── archivos_prueba/            # Excels de muestra para importaciones
├── data/                       # Archivos de la base de datos SQLite (ignorado en Git)
├── logs/                       # Historial de logs del sistema (ignorado en Git)
├── scripts/                    # Scripts de migración y depuración
├── tests/                      # Pruebas unitarias de la API
├── .gitignore                  # Reglas de exclusión para Git
└── requirements.txt            # Dependencias del proyecto
```

---

## 🚀 Instalación y Uso

Sigue estos pasos para levantar la aplicación en tu entorno local:

### 1. Requisitos Previos
*   **Python 3.10 o superior**
*   **pip** (Administrador de paquetes de Python)

### 2. Clonar el Repositorio
```bash
# Descargar el proyecto desde GitHub
# Descomprimir el archivo zip
# Entrar a la carpeta del proyecto
cd cotizador_fastapi-main
```

### 3. Inicializar el Proyecto (Nuevo paso)
Ejecuta el script de inicialización para crear los directorios necesarios:
```bash
python setup.py
```

Este script creará automáticamente:
- Directorio `data/` para la base de datos
- Directorio `logs/` para los logs del sistema
- Directorio `temp/` para archivos temporales
- Directorio `app/static/reports/` para reportes PDF
- Archivo `.env` con configuración básica (si no existe)

### 4. Crear Entorno Virtual e Instalar Dependencias
```bash
# Crear el entorno virtual (Recomendado)
python -m venv venv

# Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar librerías necesarias
pip install -r requirements.txt
```

### 5. Preparar la Base de Datos
Crea las tablas iniciales en la base de datos SQLite ejecutando:
```bash
python scripts/migrations/init_db.py
```

### 6. Iniciar el Servidor de Desarrollo
Para evitar que el recargador automático escanee archivos innecesarios de `venv`, limita la recarga al directorio `app`:
```bash
uvicorn app.main:app --reload --reload-dir app
```

Una vez activo, abre tu navegador e ingresa a:
👉 [http://localhost:8000](http://localhost:8000)

---

## 📋 Documentación de la API

FastAPI genera documentación automática para todos los endpoints. Con el servidor encendido, puedes acceder a ella en:

*   **Interactive API Docs (Scalar)**: [http://localhost:8000/scalar](http://localhost:8000/scalar)
*   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔧 Stack Tecnológico

*   **Backend**: FastAPI, SQLModel (SQLAlchemy + Pydantic)
*   **Base de Datos**: SQLite3
*   **Frontend**: HTML5, Vanilla JS, Bootstrap 5 (Estilos premium y adaptables)
*   **Reportes**: FPDF2 para la generación dinámica de documentos PDF
*   **Manejo de archivos**: Pandas y Openpyxl para procesamiento de hojas Excel