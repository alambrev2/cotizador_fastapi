# Cotizador FastAPI

Sistema de cotizaciones y gestión de clientes, productos y pagos construido con FastAPI.

## 📁 Estructura del Proyecto

```
cotizador_fastapi-main/
├── app/                      # Aplicación principal
│   ├── api/                  # Endpoints de la API
│   │   └── v1/
│   │       ├── endpoints/    # Rutas específicas (customers, quotes, etc.)
│   │       └── api.py        # Router principal
│   ├── core/                 # Configuración central
│   │   ├── config.py         # Configuración general
│   │   └── pdf.py            # Generación de PDFs
│   ├── database.py           # Conexión a base de datos
│   ├── main.py               # Aplicación FastAPI principal
│   ├── models.py             # Modelos de base de datos (SQLModel)
│   ├── schemas.py            # Schemas de Pydantic
│   ├── schemas/              # Schemas adicionales
│   ├── static/               # Archivos estáticos
│   │   ├── css/              # Estilos
│   │   └── reports/          # Reportes generados
│   └── templates/            # Plantillas Jinja2
│       └── pdf/              # Plantillas para PDFs
├── data/                     # Base de datos
│   ├── database.db           # Base de datos principal
│   └── cotizador.db          # Base de datos secundaria
├── logs/                     # Archivos de log
│   ├── error.log
│   └── uvicorn_error.log
├── scripts/                  # Scripts de utilidad
│   ├── migrations/           # Scripts de migración de base de datos
│   │   ├── init_db.py
│   │   ├── migrate_db.py
│   │   ├── migrate_db_v3.py
│   │   ├── migrate_db_v4.py
│   │   ├── migrate_cargos.py
│   │   ├── migrate_folio.py
│   │   ├── migrate_folio_quote.py
│   │   ├── migrate_marca.py
│   │   ├── migrate_payment_cargos.py
│   │   └── migrate_payments.py
│   └── debug/                # Scripts de debugging
│       ├── debug_pdf.py
│       ├── debug_server_data.py
│       ├── check_quote_schema.py
│       ├── check_schema.py
│       ├── check_sqlite.py
│       └── verify_persistence.py
├── temp/                     # Archivos temporales
│   ├── debug_output.pdf
│   ├── egresos.pdf
│   ├── ingresos.pdf
│   └── test_fpdf.pdf
├── tests/                    # Tests
│   └── test_api.py
├── .gitignore                # Archivos ignorados por Git
├── requirements.txt          # Dependencias de Python
└── TECH_STACK.md             # Documentación del stack tecnológico
```

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio:**
```bash
git clone <url-del-repositorio>
cd cotizador_fastapi-main
```

2. **Crear entorno virtual (recomendado):**
```bash
python -m venv venv
```

3. **Activar entorno virtual:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

5. **Inicializar base de datos:**
```bash
python scripts/migrations/init_db.py
```

6. **Ejecutar servidor:**
```bash
uvicorn app.main:app --reload
```

7. **Abrir en navegador:**
```
http://localhost:8000
```

### Configuración Opcional

Si deseas configurar variables de entorno, crea un archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=sqlite:///data/database.db
ENVIRONMENT=development
SECRET_KEY=tu-clave-secreta-aqui
BACKEND_CORS_ORIGINS=["http://localhost:8000"]
```

### Documentación de la API

Una vez que el servidor esté corriendo, puedes acceder a la documentación interactiva de la API en:
```
http://localhost:8000/scalar
```

## 📝 Notas de Reorganización

El proyecto ha sido reorganizado para mejorar su estructura y mantenibilidad:

- **Scripts de migración**: Movidos a `scripts/migrations/`
- **Scripts de debugging**: Movidos a `scripts/debug/`
- **Tests**: Movidos a `tests/`
- **Logs**: Movidos a `logs/`
- **Archivos temporales**: Movidos a `temp/`
- **Base de datos**: Movida a `data/`

Las referencias a la base de datos han sido actualizadas en:
- `app/database.py`: Ahora apunta a `data/database.db`
- `scripts/debug/check_sqlite.py`: Ahora apunta a `data/database.db`

## 🔧 Stack Tecnológico

Ver `TECH_STACK.md` para detalles completos del stack tecnológico.
