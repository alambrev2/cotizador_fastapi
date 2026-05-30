# Tech Stack - Cotizador FastAPI

Este documento detalla el stack tecnológico y la arquitectura actual del proyecto `cotizador_fastapi`.

## ⚙️ Backend
- **Framework**: FastAPI - Utilizado para la construcción de la API y la exposición de la lógica de negocio.
- **ORM**: SQLModel - Empleado para la interacción con la base de datos, combinando código de base de datos con validaciones de datos en Python.

## 🗄️ Base de Datos
- **Motor**: SQLite
- **Archivo**: `database.db`
- **Estructura**: La base de datos almacena la estructura de todos los modelos relacionales de nuestra aplicación, lo cual nos permite una gestión ágil de un entorno de pruebas y producción inicial.

## 🎨 Frontend
- **Motor de Plantillas**: Jinja2 - Utilizado para renderizar de forma dinámica las vistas HTML desde el servidor backend de FastAPI.
- **Estilos e Interfaz**: Tailwind CSS - Framework CSS empleado para el diseño y maquetación de la aplicación. El sistema cuenta con un diseño particular y consistente basado en una paleta de colores **'Azul Marino'**.

## 🧠 Lógica de Negocio
- **Sistema de Folios**: La aplicación genera y controla automáticamente una secuencia alfanumérica para el seguimiento de documentos:
  - Formato de Notas Remisorias: `N20260001`, `N20260002` ...
  - Formato de Cotizaciones: `C20260001`, `C20260002` ...
- **Módulos Específicos**:
  - **Calendario de Pagos de Servicios**: Este módulo permite controlar de manera estructurada los recordatorios y fechas para realizar los pagos correspondientes a servicios, optimizando nuestra operación y tesorería.

## 📦 Dependencias Principales
Las principales librerías utilizadas para hacer funcionar nuestro ecosistema incluyen:
- `fastapi` y `sqlmodel` (Pilares del código).
- `uvicorn`: Servidor ASGI de alto rendimiento para ejecutar e interactuar con la aplicación.
- `jinja2`: Para procesar nuestros templates HTML.
- `python-multipart`: Necesario en FastAPI para soportar peticiones y el procesamiento de datos provenientes de formularios (`Form(...)`).
- `pydantic`: Motor principal bajo FastAPI y SQLModel para validar los tipos de datos en la entrada y salida de la API.

---
*Nota: Este documento sirve como punto de referencia rápido para que el equipo de desarrollo conozca las bases tecnológicas fundamentales del sistema.*
