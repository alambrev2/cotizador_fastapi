# app/api/v1/endpoints/customers.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Customer
from fastapi import UploadFile, File, Response
import pandas as pd
from io import BytesIO
from openpyxl.styles import Font

router = APIRouter()


@router.post("/", response_model=Customer)
def create_customer(*, session: Session = Depends(get_session), customer: Customer):
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer

@router.get("/export")
def export_excel_route(session: Session = Depends(get_session)):
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
def export_template_route():
    data = [{
        "Nombre Completo": "Juan Perez",
        "Correo Electrónico": "juan@ejemplo.com",
        "Teléfono": "5551234567",
        "Dirección": "Av. Reforma 123",
        "Saldo Pendiente Actual (Saldo Inicial)": 0.0,
        "Consumo Total 2022": 5000.0,
        "Consumo Total 2023": 15000.0,
        "Consumo Total 2024": 30000.0,
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
def import_excel_route(dry_run: bool = False, session: Session = Depends(get_session), file: UploadFile = File(...)):
    contents = file.file.read()
    df = pd.read_excel(BytesIO(contents))
    df = df.fillna("")
    
    count_new = 0
    count_updated = 0
    
    for _, row in df.iterrows():
        email = str(row.get('Correo Electrónico', '')).strip()
        if not email: continue
            
        nombre = str(row.get('Nombre Completo', '')).strip()
        telefono = str(row.get('Teléfono', ''))
        direccion = str(row.get('Dirección', ''))
        saldo = float(row.get('Saldo Pendiente Actual (Saldo Inicial)', 0) or 0)
        c_22 = float(row.get('Consumo Total 2022', 0) or 0)
        c_23 = float(row.get('Consumo Total 2023', 0) or 0)
        c_24 = float(row.get('Consumo Total 2024', 0) or 0)
        
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
                    consumo_2024=c_24
                )
                session.add(new_c)
            count_new += 1
            
    if not dry_run:
        session.commit()
    
    return {"creados": count_new, "actualizados": count_updated}


@router.get("/")
def read_customers(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    search: str = None,
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
        system_total_comprado = sum([float(q.total) for q in c.cotizaciones])
        system_total_pagado = sum([float(p.monto) for p in c.pagos])
        system_total_cargos = sum([float(cg.monto) for cg in c.cargos])

        # Consumo acumulado (Total histórico + Total sistema + Cargos)
        total_historico = (
            float(c.consumo_2022 or 0)
            + float(c.consumo_2023 or 0)
            + float(c.consumo_2024 or 0)
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
def read_customer(*, session: Session = Depends(get_session), customer_id: int):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=Customer)
def update_customer(
    *,
    session: Session = Depends(get_session),
    customer_id: int,
    customer_update: Customer,
):
    db_customer = session.get(Customer, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Exclude unset fields from the update data
    customer_data = customer_update.model_dump(exclude_unset=True)
    db_customer.sqlmodel_update(customer_data)

    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer


@router.delete("/{customer_id}")
def delete_customer(*, session: Session = Depends(get_session), customer_id: int):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    session.delete(customer)
    session.commit()
    return {"ok": True}
