import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn
from sqlmodel import SQLModel, create_engine
import scalar_fastapi
import httpx

app = FastAPI(title="Sistema de Gestión y Cotización Pro (v2026.1)")

# Esto asegura que encuentre la carpeta app/templates sin importar la terminal
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "app", "templates"))

# Base de Datos: conexión a database.db mediante SQLModel para persistencia
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/dashboard")
async def dashboard(request: Request):
    # Datos de Helena recuperados
    cliente_data = {"nombre": "HELENA", "saldo": 4847.19, "cotizaciones": 10}
    
    return templates.TemplateResponse(
        request, "dashboard.html", {"cliente": cliente_data}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
