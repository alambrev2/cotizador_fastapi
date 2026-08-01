# Tech Stack - Cotizador FastAPI

Stack tecnológico actual del proyecto `cotizador_fastapi`.

---

## Backend

| Componente       | Tecnología                                           |
| ---------------- | ---------------------------------------------------- |
| Framework        | FastAPI                                              |
| ORM              | SQLModel (SQLAlchemy + Pydantic)                     |
| Servidor ASGI    | Uvicorn                                              |
| Lenguaje         | Python 3.10+                                         |

## Base de Datos

| Componente | Detalle                              |
| ---------- | ------------------------------------ |
| Motor      | SQLite3                              |
| Archivo    | `data/database.db`                   |
| Migraciones| Scripts manuales en `scripts/migrations/` (sin Alembic) |

## Frontend

| Componente          | Tecnología                                     |
| ------------------- | ---------------------------------------------- |
| Motor de Plantillas | Jinja2                                         |
| Estilos             | Design System propio con variables CSS (~2069 líneas) |
| JavaScript          | Vanilla JS (sin frameworks)                    |
| Gráficas            | Chart.js (vía CDN)                             |

## Autenticación

| Componente   | Tecnología                     |
| ------------ | ------------------------------ |
| Tokens       | JWT (python-jose, HS256)       |
| Contraseñas  | bcrypt (passlib[bcrypt])       |
| Rate Limiting| En memoria (5 intentos/bloqueo)|

## Generación de PDFs

| Librería   | Uso                                          |
| ---------- | -------------------------------------------- |
| xhtml2pdf  | Cotizaciones, notas de remisión, reportes financieros, estados de cuenta |

## Procesamiento de Datos

| Librería | Uso                    |
| -------- | ---------------------- |
| pandas   | Manipulación de datos  |
| openpyxl | Lectura/escritura Excel|

## Documentación de API

| Herramienta   | URL                          |
| ------------- | ---------------------------- |
| Scalar        | `http://localhost:8000/scalar` |
| Swagger UI    | `http://localhost:8000/docs`   |

## Sistema de Folios

- Cotizaciones: `C{AÑO}{NUMERO}` (ej. `C20260001`)
- Versiones editadas: `C{AÑO}{NUMERO}-V{NUM}` (ej. `C20260001-V2`)
- Notas de Remisión: `N{AÑO}{NUMERO}` (ej. `N20260001`)

## Roles de Usuario

| Rol              | Descripción                         |
| ---------------- | ----------------------------------- |
| Administrador    | Acceso total                        |
| Operativo        | Cotizaciones, dashboard, proyectos  |
| Cliente          | Panel propio, estado de cuenta      |

## Dependencias Principales

```
fastapi, uvicorn, sqlmodel, pandas, openpyxl,
pydantic-settings, python-dotenv, email-validator,
scalar-fastapi, python-multipart, jinja2,
xhtml2pdf, passlib[bcrypt], python-jose[cryptography]
```
