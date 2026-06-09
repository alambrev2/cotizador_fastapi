from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.api.deps import (
    get_current_user_pages,
    get_admin_only_page,
    get_operativo_or_admin_page,
)
from app.models import User, RoleEnum
from scalar_fastapi import get_scalar_api_reference
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cotizador API",
    description="API para gestión de cotizaciones",
    version="1.0.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Iniciando aplicación Cotizador API")

# Obtener el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Asegurar que los directorios necesarios existan
os.makedirs(os.path.join(BASE_DIR, "app", "static", "reports"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "temp"), exist_ok=True)


# Middleware de excepciones global
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

app.include_router(api_router, prefix="/api/v1")


# ─── Rutas Públicas ───────────────────────────────────────────────────────────

@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/unauthorized", include_in_schema=False)
async def unauthorized_page(request: Request):
    return templates.TemplateResponse(request, "unauthorized.html")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


# ─── Ruta Raíz: redirige según rol ───────────────────────────────────────────

@app.get("/")
def read_root(request: Request):
    """Redirige al dashboard correcto según el rol del usuario."""
    from app.database import get_session
    from app.api.deps import get_current_user_pages
    # Si no hay cookie, redirigir a login
    if not request.cookies.get("access_token"):
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/dashboard")


# ─── Dashboard Inteligente (redirige según rol) ───────────────────────────────

@app.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request, current_user: User = Depends(get_current_user_pages)):
    """Redirige al panel correcto según el rol del usuario autenticado."""
    if current_user.role == RoleEnum.CLIENTE:
        return RedirectResponse(url="/client-dashboard")
    elif current_user.role == RoleEnum.OPERATIVO:
        return RedirectResponse(url="/projects")
    else:  # ADMINISTRADOR
        return templates.TemplateResponse(request, "quick_register.html", {
            "current_user": {"username": current_user.username, "role": current_user.role.value}
        })


# ─── Panel Cliente (solo rol Cliente) ────────────────────────────────────────

@app.get("/client-dashboard", include_in_schema=False)
async def client_dashboard(request: Request, current_user: User = Depends(get_current_user_pages)):
    """Panel simplificado para clientes: solo ven su estado de cuenta."""
    if current_user.role not in [RoleEnum.CLIENTE]:
        # Admin y Operativo que accedan aquí van al dashboard normal
        return RedirectResponse(url="/dashboard")

    from app.database import get_session
    from sqlmodel import Session
    from sqlalchemy.orm import selectinload
    from app.models import Customer

    db = next(get_session())
    try:
        cliente = None
        if current_user.cliente_id:
            cliente = db.exec(
                __import__('sqlmodel', fromlist=['select']).select(Customer)
                .where(Customer.id == current_user.cliente_id)
                .options(
                    selectinload(Customer.pagos),
                    selectinload(Customer.cargos),
                    selectinload(Customer.cotizaciones),
                )
            ).first()
    finally:
        db.close()

    return templates.TemplateResponse(request, "client_dashboard.html", {
        "user": current_user,
        "cliente": cliente,
    })


# ─── Rutas Admin + Operativo ──────────────────────────────────────────────────

@app.get("/projects", include_in_schema=False)
async def approved_projects(request: Request, current_user: User = Depends(get_operativo_or_admin_page)):
    return templates.TemplateResponse(request, "approved_projects.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


# ─── Rutas Solo Administrador ─────────────────────────────────────────────────

@app.get("/new-customer", include_in_schema=False)
async def new_customer(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "create_customer.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/new-quote", include_in_schema=False)
async def new_quote(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "create_quote.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/new-product", include_in_schema=False)
async def new_product(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "create_product.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/customers", include_in_schema=False)
async def list_customers(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "list_customers.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/products", include_in_schema=False)
async def list_products(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "list_products.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/quotes", include_in_schema=False)
async def list_quotes(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "list_quotes.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/customers/{customer_id}/edit", include_in_schema=False)
async def edit_customer(request: Request, customer_id: int, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "edit_customer.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/products/{product_id}/edit", include_in_schema=False)
async def edit_product(request: Request, product_id: int, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "edit_product.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/statement", include_in_schema=False)
async def statement_page(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "statement_view.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/finance", include_in_schema=False)
async def finance_page(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "financial_summary.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })


@app.get("/users", include_in_schema=False)
async def list_users_page(request: Request, current_user: User = Depends(get_admin_only_page)):
    return templates.TemplateResponse(request, "list_users.html", {
        "current_user": {"username": current_user.username, "role": current_user.role.value}
    })
