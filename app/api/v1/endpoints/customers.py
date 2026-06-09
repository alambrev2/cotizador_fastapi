# app/api/v1/endpoints/customers.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Customer, User
from fastapi import UploadFile, File, Response
from app.api.deps import get_current_active_admin, get_current_active_operativo_or_admin
import pandas as pd
from io import BytesIO
from openpyxl.styles import Font
import logging
import os
from datetime import datetime
from app.schemas import CustomerCreate, CustomerUpdate
from app.core.security import get_password_hash
from app.models import RoleEnum

# Obtener el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Asegurar que el directorio de logs exista
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# Configurar logging para errores de importación
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'error.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=Customer)
def create_customer(
    *,
    session: Session = Depends(get_session),
    customer_in: CustomerCreate,
    current_user: User = Depends(get_current_active_admin)
):
    customer = Customer(
        nombre=customer_in.nombre,
        email=customer_in.email,
        telefono=customer_in.telefono,
        direccion=customer_in.direccion,
        saldo_inicial=customer_in.saldo_inicial,
        consumo_2022=customer_in.consumo_2022,
        consumo_2023=customer_in.consumo_2023,
        consumo_2024=customer_in.consumo_2024
    )
    session.add(customer)
    session.commit()
    session.refresh(customer)
    
    if customer_in.username and customer_in.password:
        existing_user = session.exec(select(User).where(User.username == customer_in.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")
        new_user = User(
            username=customer_in.username,
            email=customer_in.email,
            role=RoleEnum.CLIENTE,
            hashed_password=get_password_hash(customer_in.password),
            cliente_id=customer.id
        )
        session.add(new_user)
        session.commit()

    return customer

@router.get("/export")
def export_excel_route(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin)
):
    customers = session.exec(select(Customer)).all()
    data = [{
        "Nombre Completo": c.nombre,
        "Correo Electrónico": c.email,
        "Teléfono": c.telefono or "",
        "Dirección": c.direccion or "",
        "Saldo Pendiente Actual (Saldo Inicial)": float(c.saldo_inicial or 0),
        "Consumo Total 2022": float(c.consumo_2022 or 0),
        "Consumo Total 2023": float(c.consumo_2023 or 0),
        "Consumo Total 2024": float(c.consumo_2024 or 0),
        "Consumo Total 2025": float(c.consumo_2025 or 0),
        "Consumo Total 2026": float(c.consumo_2026 or 0),
    } for c in customers]
    
    df = pd.DataFrame(data)
    io = BytesIO()
    with pd.ExcelWriter(io, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes')
        worksheet = writer.sheets['Clientes']
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            
    return Response(content=io.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={'Content-Disposition': 'attachment; filename="clientes.xlsx"'})

@router.get("/template")
def export_template_route(
    current_user: User = Depends(get_current_active_admin)
):
    data = [{
        "Nombre Completo": "Juan Perez",
        "Correo Electrónico": "juan@ejemplo.com",
        "Teléfono": "5551234567",
        "Dirección": "Av. Reforma 123",
        "Saldo Pendiente Actual (Saldo Inicial)": 0.0,
        "Consumo Total 2022": 5000.0,
        "Consumo Total 2023": 15000.0,
        "Consumo Total 2024": 30000.0,
        "Consumo Total 2025": 40000.0,
        "Consumo Total 2026": 50000.0,
    }]
    df = pd.DataFrame(data)
    io = BytesIO()
    with pd.ExcelWriter(io, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Plantilla Clientes')
        worksheet = writer.sheets['Plantilla Clientes']
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
            
    return Response(content=io.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={'Content-Disposition': 'attachment; filename="plantilla_clientes.xlsx"'})

@router.post("/import")
def import_excel_route(
    dry_run: bool = False,
    session: Session = Depends(get_session),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_admin)
):
    # Asegurar que el directorio de logs exista
    os.makedirs('logs', exist_ok=True)
    
    logger.info(f"Iniciando importación Excel. dry_run={dry_run}")
    
    try:
        contents = file.file.read()
        
        # Validar que el archivo no esté vacío
        if not contents:
            error_msg = "El archivo Excel está vacío"
            logger.error(f"Error de importación: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        df = pd.read_excel(BytesIO(contents))
        df = df.fillna("")
        
        logger.info(f"Archivo Excel leído. Filas: {len(df)}, Columnas: {list(df.columns)}")
        
        # Validar estructura del Excel (columnas requeridas)
        columnas_requeridas = [
            'Correo Electrónico',
            'Nombre Completo',
            'Saldo Pendiente Actual (Saldo Inicial)',
            'Consumo Total 2022',
            'Consumo Total 2023',
            'Consumo Total 2024',
            'Consumo Total 2025',
            'Consumo Total 2026'
        ]
        
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        if columnas_faltantes:
            error_msg = f"Faltan columnas requeridas en el Excel: {', '.join(columnas_faltantes)}"
            logger.error(f"Error de estructura del Excel: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validar que el Excel tenga datos
        if df.empty:
            error_msg = "El archivo Excel no tiene filas de datos"
            logger.error(f"Error de importación: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        count_new = 0
        count_updated = 0
        error_row = None
        
        logger.info(f"Iniciando procesamiento de {len(df)} filas")
        
        # Iniciar transacción para rollback completo en caso de error
        try:
            for index, row in df.iterrows():
                row_number = index + 2  # +2 porque pandas usa 0-index y Excel tiene encabezado en fila 1
                
                logger.info(f"Procesando fila {row_number}")
                
                try:
                    email = str(row.get('Correo Electrónico', '')).strip()
                    logger.info(f"Email en fila {row_number}: '{email}'")
                    if not email:
                        logger.warning(f"Fila {row_number} saltada: email vacío")
                        continue
                        
                    nombre = str(row.get('Nombre Completo', '')).strip()
                    telefono = str(row.get('Teléfono', ''))
                    direccion = str(row.get('Dirección', ''))
                    
                    # Validar tipos de datos numéricos con try/except
                    try:
                        saldo = float(row.get('Saldo Pendiente Actual (Saldo Inicial)', 0) or 0)
                    except (ValueError, TypeError):
                        error_msg = f"Error en fila {row_number}: 'Saldo Pendiente Actual (Saldo Inicial)' debe ser un número válido. Valor: {row.get('Saldo Pendiente Actual (Saldo Inicial)')}"
                        logger.error(error_msg)
                        error_row = row_number
                        raise ValueError(error_msg)
                    
                    try:
                        c_22 = float(row.get('Consumo Total 2022', 0) or 0)
                    except (ValueError, TypeError):
                        error_msg = f"Error en fila {row_number}: 'Consumo Total 2022' debe ser un número válido. Valor: {row.get('Consumo Total 2022')}"
                        logger.error(error_msg)
                        error_row = row_number
                        raise ValueError(error_msg)
                    
                    try:
                        c_23 = float(row.get('Consumo Total 2023', 0) or 0)
                    except (ValueError, TypeError):
                        error_msg = f"Error en fila {row_number}: 'Consumo Total 2023' debe ser un número válido. Valor: {row.get('Consumo Total 2023')}"
                        logger.error(error_msg)
                        error_row = row_number
                        raise ValueError(error_msg)
                    
                    try:
                        c_24 = float(row.get('Consumo Total 2024', 0) or 0)
                    except (ValueError, TypeError):
                        error_msg = f"Error en fila {row_number}: 'Consumo Total 2024' debe ser un número válido. Valor: {row.get('Consumo Total 2024')}"
                        logger.error(error_msg)
                        error_row = row_number
                        raise ValueError(error_msg)
                        
                    try:
                        c_25 = float(row.get('Consumo Total 2025', 0) or 0)
                    except (ValueError, TypeError):
                        error_msg = f"Error en fila {row_number}: 'Consumo Total 2025' debe ser un número válido. Valor: {row.get('Consumo Total 2025')}"
                        logger.error(error_msg)
                        error_row = row_number
                        raise ValueError(error_msg)
                        
                    try:
                        c_26 = float(row.get('Consumo Total 2026', 0) or 0)
                    except (ValueError, TypeError):
                        error_msg = f"Error en fila {row_number}: 'Consumo Total 2026' debe ser un número válido. Valor: {row.get('Consumo Total 2026')}"
                        logger.error(error_msg)
                        error_row = row_number
                        raise ValueError(error_msg)
                    
                    existing = session.exec(select(Customer).where(Customer.email == email)).first()
                    if existing:
                        if not dry_run:
                            if nombre: existing.nombre = nombre
                            if telefono: existing.telefono = telefono
                            if direccion: existing.direccion = direccion
                            existing.saldo_inicial = saldo
                            existing.consumo_2022 = c_22
                            existing.consumo_2023 = c_23
                            existing.consumo_2024 = c_24
                            existing.consumo_2025 = c_25
                            existing.consumo_2026 = c_26
                            session.add(existing)
                        count_updated += 1
                    else:
                        if not dry_run:
                            new_c = Customer(
                                nombre=nombre or "Desconocido",
                                email=email,
                                telefono=telefono,
                                direccion=direccion,
                                saldo_inicial=saldo,
                                consumo_2022=c_22,
                                consumo_2023=c_23,
                                consumo_2024=c_24,
                                consumo_2025=c_25,
                                consumo_2026=c_26
                            )
                            session.add(new_c)
                        count_new += 1
                        
                except ValueError as ve:
                    # Error de validación de datos - propagar para rollback
                    raise ve
                except Exception as e:
                    error_msg = f"Error inesperado en fila {row_number}: {str(e)}"
                    logger.error(error_msg)
                    error_row = row_number
                    raise Exception(error_msg)
            
            if not dry_run:
                session.commit()
            
            return {"creados": count_new, "actualizados": count_updated}
            
        except Exception as e:
            # Rollback completo en caso de cualquier error
            if not dry_run:
                session.rollback()
            
            # Devolver mensaje de error con número de fila si está disponible
            if error_row:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Error en la fila {error_row} del archivo Excel: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Error al procesar el archivo Excel: {str(e)}"
                )
                
    except HTTPException:
        # Re-lanzar excepciones HTTP ya manejadas
        raise
    except Exception as e:
        # Capturar cualquier error no esperado y hacer rollback
        if not dry_run:
            session.rollback()
        
        error_msg = f"Error crítico al procesar el archivo Excel: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/")
def read_customers(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    search: str = None,
    current_user: User = Depends(get_current_active_admin),
):
    from app.models import Quote
    from sqlalchemy.orm import selectinload

    query = select(Customer).options(
        selectinload(Customer.cotizaciones),
        selectinload(Customer.pagos),
        selectinload(Customer.cargos)
    )
    if search:
        query = query.where(
            (Customer.nombre.contains(search)) | (Customer.email.contains(search))
        )
    customers = session.exec(query.offset(offset).limit(limit)).all()

    # Calcular consumo total y saldo pendiente (Histórico + Sistema) por cliente
    results = []
    for c in customers:
        # Usar las relaciones precargadas para eficiencia
        system_total_comprado = sum([float(q.total) for q in c.cotizaciones if q.estado in ['Pendiente', 'Cobranza Requerida']])
        system_total_pagado = sum([float(p.monto) for p in c.pagos])
        system_total_cargos = sum([float(cg.monto) for cg in c.cargos])

        # Consumo acumulado (Total histórico + Total sistema + Cargos)
        total_historico = (
            float(c.consumo_2022 or 0)
            + float(c.consumo_2023 or 0)
            + float(c.consumo_2024 or 0)
            + float(c.consumo_2025 or 0)
            + float(c.consumo_2026 or 0)
        )
        total_acumulado = total_historico + system_total_comprado + system_total_cargos

        # Saldo pendiente global (Saldo inicial + Total sistema comprado + Cargos - Total sistema pagado)
        saldo_pendiente = (
            float(c.saldo_inicial or 0) + system_total_comprado + system_total_cargos - system_total_pagado
        )

        # Convertir a dict y añadir campos
        c_dict = c.model_dump()
        c_dict["total_consumo"] = total_acumulado
        c_dict["saldo_pendiente"] = saldo_pendiente
        results.append(c_dict)

    return results


@router.get("/{customer_id}", response_model=Customer)
def read_customer(
    *,
    session: Session = Depends(get_session),
    customer_id: int,
    current_user: User = Depends(get_current_active_admin)
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=Customer)
def update_customer(
    *,
    session: Session = Depends(get_session),
    customer_id: int,
    customer_update: CustomerUpdate,
    current_user: User = Depends(get_current_active_admin),
):
    db_customer = session.get(Customer, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Exclude unset fields from the update data
    customer_data = customer_update.model_dump(exclude_unset=True)
    
    # Remove username and password from customer_data since they go to User
    username = customer_data.pop("username", None)
    password = customer_data.pop("password", None)

    # Prevent historical fields from being updated via standard operations
    customer_data.pop("consumo_2022", None)
    customer_data.pop("consumo_2023", None)
    customer_data.pop("consumo_2024", None)
    customer_data.pop("consumo_2025", None)
    customer_data.pop("consumo_2026", None)
    customer_data.pop("saldo_inicial", None)

    db_customer.sqlmodel_update(customer_data)
    session.add(db_customer)

    # Actualizar o crear usuario
    if username or password:
        user = session.exec(select(User).where(User.cliente_id == db_customer.id)).first()
        if user:
            if username:
                # Verificar si el nuevo username no está ocupado
                if username != user.username:
                    existing = session.exec(select(User).where(User.username == username)).first()
                    if existing:
                        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")
                user.username = username
            if password:
                user.hashed_password = get_password_hash(password)
            session.add(user)
        else:
            if not username or not password:
                raise HTTPException(status_code=400, detail="Se requiere nombre de usuario y contraseña para crear la cuenta de acceso.")
            existing = session.exec(select(User).where(User.username == username)).first()
            if existing:
                raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")
            new_user = User(
                username=username,
                email=db_customer.email,
                role=RoleEnum.CLIENTE,
                hashed_password=get_password_hash(password),
                cliente_id=db_customer.id
            )
            session.add(new_user)

    session.commit()
    session.refresh(db_customer)
    return db_customer


@router.delete("/{customer_id}")
def delete_customer(
    *,
    session: Session = Depends(get_session),
    customer_id: int,
    current_user: User = Depends(get_current_active_admin)
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    session.delete(customer)
    session.commit()
    return {"ok": True}
