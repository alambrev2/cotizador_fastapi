# ANÁLISIS DEL SISTEMA - Cotizador Pro

## 1. Descripción General

**Cotizador Pro** es un sistema web de gestión empresarial desarrollado con **FastAPI** (Python) que integra:

-   Cotizaciones profesionales con generación de PDF
-   Control de inventario y catálogo de productos
-   Administración de clientes con historial financiero
-   Gestión de pagos, cargos, abonos y remisiones
-   Control financiero (ingresos, egresos, estado de resultados)
-   Importación/exportación masiva de datos desde Excel
-   Portal de clientes con estado de cuenta simplificado
-   Dashboard ejecutivo con métricas y alertas
-   Autenticación por roles con JWT y tokens mágicos

---

## 2. Arquitectura del Sistema

### 2.1 Patrón Arquitectónico

El sistema sigue una **arquitectura en capas** con patrón **MVC ligero**:

```
┌─────────────────────────────────────────────────────────┐
│                   Capa de Presentación                   │
│   Jinja2 Templates (19 HTML) + CSS propio + Vanilla JS   │
├─────────────────────────────────────────────────────────┤
│                   Capa de API (REST)                     │
│   FastAPI Routers → Endpoints (auth, CRUDs, reports)     │
├─────────────────────────────────────────────────────────┤
│                 Capa de Lógica de Negocio                 │
│   Core (config, security, PDF) + Schemas Pydantic        │
├─────────────────────────────────────────────────────────┤
│                 Capa de Acceso a Datos                   │
│   SQLModel (SQLAlchemy ORM) → SQLite3                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Estructura de Directorios

```
cotizador_fastapi/
├── app/                              # Aplicación principal
│   ├── main.py                       # Punto de entrada FastAPI
│   ├── database.py                   # Configuración BD (SQLite)
│   ├── models.py                     # Modelos SQLModel
│   ├── schemas.py                    # Schemas Pydantic
│   ├── api/
│   │   ├── deps.py                   # Dependencias (auth, roles)
│   │   └── v1/
│   │       ├── api.py                # Router principal
│   │       └── endpoints/            # 10 controladores
│   ├── core/
│   │   ├── config.py                 # Settings (pydantic-settings)
│   │   ├── security.py               # JWT, bcrypt, rate limiting
│   │   └── pdf.py                    # Generación PDF (xhtml2pdf)
│   ├── schemas/
│   │   └── cotizacion.py             # Schema legacy
│   ├── static/
│   │   ├── css/styles.css            # Design system (~2069 líneas)
│   │   ├── js/notifications.js       # Notificaciones frontend
│   │   └── reports/                  # PDFs generados
│   └── templates/
│       ├── *.html                    # 19 vistas Jinja2
│       └── pdf/                      # 4 plantillas PDF
├── data/database.db                  # Base de datos SQLite
├── scripts/                          # Utilidades
│   ├── migrations/                   # 10 migraciones de BD
│   └── debug/                        # 6 scripts de depuración
├── tests/                            # Pruebas unitarias
├── logs/                             # Logs del sistema
├── temp/                             # Archivos temporales
├── archivos_prueba/                  # Excel de muestra
├── requirements.txt
├── setup.py                          # Inicialización del proyecto
└── .env                              # Configuración local
```

---

## 3. Stack Tecnológico

| Componente            | Tecnología                                                   |
| --------------------- | ------------------------------------------------------------ |
| **Lenguaje**          | Python 3.10+                                                 |
| **Framework Web**     | FastAPI                                                      |
| **ORM**               | SQLModel (SQLAlchemy + Pydantic)                             |
| **Base de Datos**     | SQLite3                                                      |
| **Templates**         | Jinja2                                                       |
| **Frontend**          | HTML5 + CSS propio (Design System) + JavaScript vanilla      |
| **Autenticación**     | JWT (python-jose) + bcrypt (passlib)                         |
| **PDF**               | xhtml2pdf (cotizaciones, remisiones, estados de cuenta)      |
| **Excel**             | pandas + openpyxl                                            |
| **Servidor ASGI**     | Uvicorn                                                      |
| **Doc. API**          | Scalar FastAPI + Swagger UI                                  |
| **Validación**        | Pydantic v2                                                  |
| **Configuración**     | pydantic-settings + python-dotenv                            |
| **Gráficas**          | Chart.js (CDN)                                               |

---

## 4. Modelos de Datos y Relaciones

### 4.1 Diagrama Entidad-Relación

```
Customer (1) ──< (N) Quote
Customer (1) ──< (N) Payment
Customer (1) ──< (N) AccountCharge
Customer (1) ──< (N) User (vía cliente_id)
Quote (1) ──< (N) QuoteItem
Quote (1) ──< (N) Payment
Quote (1) ──< (1) Quote (vía padre_id para versionado)
AccountCharge (1) ──< (N) Payment
Product (1) ──< (N) QuoteItem
```

### 4.2 Entidades Principales

| Entidad           | Propósito                             | Campos Clave                                               |
| ----------------- | ------------------------------------- | ---------------------------------------------------------- |
| **Customer**      | Clientes                              | nombre, email, teléfono, saldo_inicial, consumo_anual      |
| **Product**       | Productos / inventario                | nombre, marca, costo, precio_menudeo, precio_mayoreo, stock |
| **Quote**         | Cotizaciones                          | cliente, total, IVA, folio (C20260001), estado, tipo_pago  |
| **QuoteItem**     | Items de cotización                   | producto, cantidad, precio_unitario                        |
| **Payment**       | Pagos / abonos                        | monto, método, referencia, vinculo (quote/cargo/cliente)   |
| **AccountCharge** | Cargos / servicios                    | detalle, monto, folio_nota (N20260001), estatus            |
| **Expense**       | Gastos operativos                     | descripción, monto, fecha, categoría                       |
| **OtherIncome**   | Ingresos varios                       | descripción, monto, fecha, categoría                       |
| **ScheduledExpense** | Gastos programados                 | descripción, monto, frecuencia, estatus, CLABE             |
| **User**          | Usuarios del sistema                  | username, email, role, hashed_password, magic_token        |

### 4.3 Sistema de Folios

| Documento        | Formato         | Ejemplo       |
| ---------------- | --------------- | ------------- |
| Cotización       | `C{AÑO}{NUM}`   | `C20260001`   |
| Versión editada  | `C{AÑO}{NUM}-V{N}` | `C20260001-V2` |
| Nota de Remisión | `N{AÑO}{NUM}`   | `N20260001`   |

### 4.4 Estados de Cotización

`Borrador` → `Enviada` → `Aprobación Solicitada` → `Aprobada` | `Rechazada`
       ↓
`Pendiente` → `Cobranza Requerida` → `Finalizada`
       ↓
`Sustituida` (al crear una nueva versión) | `Cancelada`

---

## 5. Endpoints de la API

### 5.1 Autenticación (`/api/v1/auth`)

| Método | Ruta            | Descripción          | Acceso    |
| ------ | --------------- | -------------------- | --------- |
| POST   | `/auth/login`   | Login (JWT en cookie)| Público   |
| POST   | `/auth/logout`  | Cerrar sesión        | Cualquiera|
| GET    | `/auth/me`      | Usuario actual       | Auth      |

### 5.2 Usuarios (`/api/v1/users`)

| Método | Ruta                                    | Descripción              | Acceso |
| ------ | --------------------------------------- | ------------------------ | ------ |
| GET    | `/users/`                               | Listar usuarios          | Admin  |
| GET    | `/users/customers-without-user`          | Clientes sin usuario     | Admin  |
| POST   | `/users/generar-cuentas-clientes`        | Generar cuentas masivas  | Admin  |
| POST   | `/users/`                               | Crear usuario            | Admin  |
| GET    | `/users/{id}`                           | Detalle usuario          | Admin  |
| PUT    | `/users/{id}`                           | Editar usuario           | Admin  |
| DELETE | `/users/{id}`                           | Eliminar usuario         | Admin  |
| PUT    | `/users/{id}/toggle`                    | Activar/desactivar       | Admin  |
| POST   | `/users/{id}/reset-password`            | Resetear contraseña      | Admin  |
| POST   | `/users/{id}/magic-token`               | Generar token mágico     | Admin  |

### 5.3 Clientes (`/api/v1/customers`)

| Método | Ruta                     | Descripción                     | Acceso |
| ------ | ------------------------ | ------------------------------- | ------ |
| POST   | `/customers/`            | Crear cliente                   | Admin  |
| GET    | `/customers/`            | Listar (búsqueda + paginación)  | Admin  |
| GET    | `/customers/export`      | Exportar a Excel                | Admin  |
| GET    | `/customers/template`    | Descargar plantilla Excel       | Admin  |
| POST   | `/customers/import`      | Importar desde Excel (dry-run)  | Admin  |
| GET    | `/customers/{id}`        | Detalle cliente                 | Admin  |
| PATCH  | `/customers/{id}`        | Actualizar cliente              | Admin  |
| DELETE | `/customers/{id}`        | Eliminar cliente (cascada)      | Admin  |

### 5.4 Productos (`/api/v1/products`)

| Método | Ruta                     | Descripción                     | Acceso |
| ------ | ------------------------ | ------------------------------- | ------ |
| POST   | `/products/`             | Crear producto                  | Admin  |
| GET    | `/products/`             | Listar (búsqueda + filtro)      | Admin  |
| GET    | `/products/export`       | Exportar catálogo a Excel       | Admin  |
| GET    | `/products/template`     | Descargar plantilla Excel       | Admin  |
| POST   | `/products/import`       | Importar desde Excel            | Admin  |
| GET    | `/products/{id}`         | Detalle producto                | Admin  |
| PATCH  | `/products/{id}`         | Actualizar producto             | Admin  |
| DELETE | `/products/{id}`         | Eliminar producto               | Admin  |

### 5.5 Cotizaciones (`/api/v1/quotes`)

| Método | Ruta                                 | Descripción                          | Acceso             |
| ------ | ------------------------------------ | ------------------------------------ | ------------------ |
| POST   | `/quotes/`                           | Crear cotización + items             | Admin/Operativo    |
| GET    | `/quotes/`                           | Listar (filtros estado, búsqueda)    | Admin/Operativo    |
| GET    | `/quotes/by-customer/{customer_id}`  | Cotizaciones por cliente             | Auth (propias)     |
| GET    | `/quotes/{id}`                       | Detalle                              | Admin/Operativo    |
| PATCH  | `/quotes/{id}`                       | Actualizar (estado, stock)           | Admin/Operativo    |
| GET    | `/quotes/{id}/pdf`                   | Generar PDF                          | Auth (propia)      |
| GET    | `/quotes/public/{id}/pdf`            | PDF público (sin auth)               | Público            |
| PATCH  | `/quotes/{id}/client-status`         | Cliente responde                     | Auth               |
| POST   | `/quotes/{id}/send-email`            | Enviar por email con PDF             | Admin/Operativo    |
| POST   | `/quotes/{id}/report`                | Subir reporte operativo (PDF)        | Admin/Operativo    |

### 5.6 Pagos (`/api/v1/payments`)

| Método | Ruta                                        | Descripción                        | Acceso          |
| ------ | ------------------------------------------- | ---------------------------------- | --------------- |
| POST   | `/payments/`                                | Registrar pago                     | Admin           |
| GET    | `/payments/`                                | Listar pagos                       | Admin           |
| GET    | `/payments/active`                          | Cuentas activas con saldo          | Admin           |
| GET    | `/payments/active-customers`                | Clientes con deuda activa          | Admin           |
| GET    | `/payments/by-quote/{quote_id}`             | Pagos de cotización                | Admin           |
| GET    | `/payments/statement/{quote_id}`            | Estado de cuenta por cotización    | Admin           |
| GET    | `/payments/statement/customer/{customer_id}`| Estado de cuenta consolidado       | Admin/Cliente   |
| GET    | `/payments/statement/customer/{customer_id}/pdf` | PDF estado de cuenta          | Admin/Cliente   |
| POST   | `/payments/charges`                         | Crear cargo/servicio               | Admin           |
| POST   | `/payments/remission`                       | Generar nota de remisión           | Admin           |
| GET    | `/payments/remission/{folio}`               | Descargar PDF remisión             | Admin           |
| DELETE | `/payments/{id}`                            | Eliminar pago                      | Admin           |

### 5.7 Gastos, Ingresos y Dashboard

| Método | Ruta                                    | Descripción                     | Acceso      |
| ------ | --------------------------------------- | ------------------------------- | ----------- |
| POST   | `/expenses/`                            | Registrar gasto                 | Admin       |
| GET    | `/expenses/`                            | Listar gastos                   | Admin       |
| DELETE | `/expenses/{id}`                        | Eliminar gasto                  | Admin       |
| POST   | `/incomes/`                             | Registrar ingreso               | Admin       |
| GET    | `/incomes/`                             | Listar ingresos                 | Admin       |
| DELETE | `/incomes/{id}`                         | Eliminar ingreso                | Admin       |
| GET    | `/dashboard/summary`                    | Resumen ejecutivo               | Auth        |
| GET    | `/dashboard/analytics`                  | Métricas y alertas              | Auth        |
| GET    | `/dashboard/pnl`                        | Estado de resultados P&L        | Auth        |
| GET    | `/dashboard/export/ingresos`            | Exportar ingresos a PDF         | Auth        |
| GET    | `/dashboard/export/egresos`             | Exportar egresos a PDF          | Auth        |

### 5.8 Gastos Programados (`/api/v1/scheduled-expenses`)

| Método | Ruta                           | Descripción              | Acceso |
| ------ | ------------------------------ | ------------------------ | ------ |
| POST   | `/scheduled-expenses/`         | Crear gasto programado   | Auth   |
| GET    | `/scheduled-expenses/`         | Listar                   | Auth   |
| PATCH  | `/scheduled-expenses/{id}`     | Actualizar               | Auth   |
| DELETE | `/scheduled-expenses/{id}`     | Eliminar                 | Auth   |

### 5.9 Rutas HTML (Frontend Server-Side en `main.py`)

| Método | Ruta                        | Descripción                      |
| ------ | --------------------------- | -------------------------------- |
| GET    | `/`                         | Raíz (redirige según rol)        |
| GET    | `/login`                    | Página de login                  |
| GET    | `/login-magico`             | Login con token mágico           |
| GET    | `/unauthorized`             | Acceso denegado                  |
| GET    | `/dashboard`                | Dashboard principal              |
| GET    | `/client-dashboard`         | Panel de cliente                 |
| GET    | `/projects`                 | Proyectos aprobados              |
| GET    | `/customers`                | Lista de clientes                |
| GET    | `/products`                 | Lista de productos               |
| GET    | `/quotes`                   | Lista de cotizaciones            |
| GET    | `/new-customer`             | Crear cliente                    |
| GET    | `/new-product`              | Crear producto                   |
| GET    | `/new-quote`                | Crear cotización                 |
| GET    | `/edit-customer/{id}`       | Editar cliente                   |
| GET    | `/edit-product/{id}`        | Editar producto                  |
| GET    | `/statement`                | Estado de cuenta                 |
| GET    | `/finance`                  | Resumen financiero               |
| GET    | `/users`                    | Lista de usuarios                |

---

## 6. Sistema de Autenticación y Roles

### 6.1 Roles

| Rol              | Descripción                                       |
| ---------------- | ------------------------------------------------- |
| **Administrador**| Acceso total al sistema                           |
| **Operativo**    | Cotizaciones, proyectos, dashboard (sin admin)    |
| **Cliente**      | Panel simplificado, estado de cuenta, responder    |

### 6.2 Mecanismo

1.  **Login**: POST `/api/v1/auth/login` con `OAuth2PasswordRequestForm`
2.  **JWT**: Token firmado con HS256, almacenado en cookie HttpOnly, SameSite=Strict
3.  **Duración**: Configurable en `.env` (default 480 min = 8 horas)
4.  **Rate Limiting**: Bloqueo de IP tras 5 intentos fallidos (5 minutos)
5.  **Token Mágico**: Login sin contraseña para clientes vía `/login-magico`

### 6.3 Dependencias (`app/api/deps.py`)

-   `get_current_user()` - Usuario desde JWT (cookie o header)
-   `get_current_active_admin()` - Solo Administrador
-   `get_current_active_operativo_or_admin()` - Operativo o Admin
-   `get_current_active_cliente()` - Solo Cliente
-   `require_role(*roles)` - Factory para roles arbitrarios
-   `get_current_user_pages()` - Para rutas HTML (redirige a /login)
-   `get_admin_only_page()` - Páginas HTML exclusivas de Admin

---

## 7. Funcionalidades Clave

### 7.1 Importación/Exportación Excel

-   **Clientes**: Importación con validación, dry-run, detección de duplicados por email
-   **Productos**: Importación con validación de datos, precio, stock
-   **Exportación**: Catálogo completo de clientes y productos a Excel
-   **Plantillas**: Descarga de formatos predefinidos

### 7.2 Generación de PDFs

-   **Cotizaciones**: Con logo, datos del cliente, items, totales, condiciones de pago
-   **Notas de Remisión**: Con folio N20260001, cargos asociados
-   **Estados de Cuenta**: Saldo inicial, compras, pagos, saldo pendiente
-   **Reportes Financieros**: Ingresos vs egresos mensuales

### 7.3 Versionado de Cotizaciones

-   Al editar una cotización aceptada, se crea una nueva versión
-   Folio original: `C20260001`
-   Nueva versión: `C20260001-V2`
-   La versión anterior queda marcada como "Sustituida"

### 7.4 Control de Inventario

-   Al aceptar cotización: descuento automático del stock
-   Al rechazar cotización: devolución automática del stock
-   Alertas de stock mínimo en dashboard

### 7.5 Conciliación Financiera

```
Saldo Pendiente = Saldo Inicial + Suma(Cotizaciones) + Suma(Cargos) - Suma(Pagos)
```

### 7.6 Dashboard y Alertas

-   Saldo total por cobrar
-   Flujo de caja (ingresos - egresos del mes)
-   Cotizaciones pendientes de respuesta
-   Clientes con deuda vencida (>30 días)
-   Productos con stock por debajo del mínimo
-   Reportes operativos pendientes de subir

---

## 8. Seguridad

-   **Contraseñas**: bcrypt via passlib
-   **JWT**: HS256 con SECRET_KEY
-   **Cookies**: HttpOnly, SameSite=Strict, Secure solo en producción
-   **Rate Limiting**: En memoria, 5 intentos fallidos = bloqueo 5 min
-   **CORS**: Configurable via .env
-   **Validación de SECRET_KEY**: Rechaza claves débiles en producción

---

## 9. Base de Datos

-   **Motor**: SQLite3
-   **Archivo**: `data/database.db`
-   **ORM**: SQLModel sobre SQLAlchemy
-   **Migraciones**: Scripts manuales en `scripts/migrations/` (sin Alembic)

---

## 10. Frontend

-   **Motor de templates**: Jinja2 (server-side rendering)
-   **Estilos**: Design system propio con ~2069 líneas de CSS
-   **Componentes**: Sidebar, cards, tablas, formularios, botones, modales, badges, alertas
-   **Gráficas**: Chart.js (vía CDN)
-   **JavaScript**: Vanilla JS, sin frameworks

---

## 11. Pruebas

| Archivo              | Descripción                                       |
| -------------------- | ------------------------------------------------- |
| `tests/test_api.py`  | Prueba básica de la API FastAPI                   |
| `tests/test_adjustments.py` | Lógica de pagos, filiales, alertas        |
| `tests/test_new_flows.py`   | Token mágico, cambio de estado por cliente |

**Nota**: Las pruebas se ejecutan como scripts independientes (no usan pytest) y operan sobre la BD real.

---

## 12. Configuración del Entorno (`.env`)

```
SECRET_KEY=<clave_aleatoria_64_caracteres_hex>
ENVIRONMENT=development
PROJECT_NAME=Cotizador
PROJECT_VERSION=1.0.0
BACKEND_CORS_ORIGINS=["*"]
ACCESS_TOKEN_EXPIRE_MINUTES=480
LOGIN_MAX_ATTEMPTS=5
LOGIN_BLOCK_MINUTES=5
```

---

## 13. Observaciones y Deuda Técnica

1.  **Migraciones**: No hay sistema automático (Alembic). Las migraciones son scripts Python manuales.
2.  **Pruebas**: No usan pytest ni BD de prueba aislada. Operan sobre la BD real.
3.  **Schemas duplicados**: `app/schemas.py` (principal) y `app/schemas/cotizacion.py` (legacy, posiblemente no usado).
4.  **Scratch files**: Hay 22 scripts exploratorios en `scratch/` que no deberían estar en producción.
5.  **Dependencia faltante**: `fpdf2` se usa en dashboard.py pero no está en `requirements.txt`.
6.  **Sin Docker**: No hay Dockerfile ni docker-compose.yml.
7.  **Sin CI/CD**: No hay integración continua configurada.
8.  **Logging**: Configurado en múltiples módulos con FileHandler + StreamHandler.
