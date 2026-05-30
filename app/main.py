from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from scalar_fastapi import get_scalar_api_reference
from app.database import create_db_and_tables
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


# Evento de startup para inicializar la base de datos
@app.on_event("startup")
async def startup_event():
    logger.info("Inicializando base de datos...")
    try:
        create_db_and_tables()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise


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


@app.get("/")
def read_root():
    return RedirectResponse(url="/dashboard")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


@app.get("/new-customer", include_in_schema=False)
async def new_customer(request: Request):
    return templates.TemplateResponse(request, "create_customer.html")


@app.get("/new-quote", include_in_schema=False)
async def new_quote(request: Request):
    return templates.TemplateResponse(request, "create_quote.html")


@app.get("/new-product", include_in_schema=False)
async def new_product(request: Request):
    return templates.TemplateResponse(request, "create_product.html")


@app.get("/dashboard", include_in_schema=False)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "quick_register.html")


@app.get("/customers", include_in_schema=False)
async def list_customers(request: Request):
    return templates.TemplateResponse(request, "list_customers.html")


@app.get("/products", include_in_schema=False)
async def list_products(request: Request):
    return templates.TemplateResponse(request, "list_products.html")


@app.get("/quotes", include_in_schema=False)
async def list_quotes(request: Request):
    return templates.TemplateResponse(request, "list_quotes.html")


@app.get("/customers/{customer_id}/edit", include_in_schema=False)
async def edit_customer(request: Request, customer_id: int):
    return templates.TemplateResponse(request, "edit_customer.html")


@app.get("/products/{product_id}/edit", include_in_schema=False)
async def edit_product(request: Request, product_id: int):
    return templates.TemplateResponse(request, "edit_product.html")


@app.get("/statement", include_in_schema=False)
async def statement_page(request: Request):
    return templates.TemplateResponse(request, "statement_view.html")


@app.get("/finance", include_in_schema=False)
async def finance_page(request: Request):
    return templates.TemplateResponse(request, "financial_summary.html")

@app.get("/projects", include_in_schema=False)
async def approved_projects(request: Request):
    # Trigger uvicorn template cache reload v4
    return templates.TemplateResponse(request, "approved_projects.html")
