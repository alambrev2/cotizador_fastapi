from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Payment, Quote, AccountCharge
from app.schemas import PaymentCreate, AccountChargeCreate
from pydantic import BaseModel
from fastapi import Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import selectinload
from app.core.pdf import generate_pdf_bytes
import os

# Obtener el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

router = APIRouter()

ESTADOS_COBRABLES = ['Pendiente', 'Cobranza Requerida']


@router.get("/active")
def read_active_statements(session: Session = Depends(get_session)):
    # Obtener cotizaciones con total > 0 que estén en estados cobrables
    query = (
        select(Quote)
        .options(selectinload(Quote.pagos))
        .options(selectinload(Quote.cliente))
        .where(Quote.total > 0)
        .where(Quote.estado.in_(ESTADOS_COBRABLES))
        .order_by(Quote.id.desc())
    )
    quotes = session.exec(query).all()

    active_accounts = []

    for q in quotes:
        total_pagado = sum([p.monto for p in q.pagos])
        saldo = float(q.total) - float(total_pagado)

        if saldo > 0.1:  # Tolerancia de centavos
            active_accounts.append(
                {
                    "id": q.id,
                    "cliente": q.cliente.nombre if q.cliente else "N/A",
                    "total": float(q.total),
                    "pagado": float(total_pagado),
                    "saldo": saldo,
                    "estado": q.estado,
                }
            )

    return active_accounts


@router.get("/active-customers")
def read_active_customers(session: Session = Depends(get_session)):
    """Obtiene lista de clientes con deuda activa (saldo inicial + cotizaciones - pagos)."""
    from app.models import Customer

    # Obtener todos los clientes con sus cotizaciones y TODOS sus pagos
    query = select(Customer).options(
        selectinload(Customer.cotizaciones).selectinload(Quote.pagos),
        selectinload(Customer.pagos),
        selectinload(Customer.cargos),
    )
    customers = session.exec(query).all()

    active_accounts = []

    for c in customers:
        active_counts = 0

        # Deuda de cotizaciones activas (con saldo pendiente post-abonos directos)
        for q in c.cotizaciones:
            if q.estado not in ESTADOS_COBRABLES:
                continue
            pagado_q = sum([float(p.monto) for p in q.pagos])
            saldo_q = float(q.total) - pagado_q
            if saldo_q > 0.1:
                active_counts += 1

        # Para los cargos (sin vinculación directa de pagos), se pagan con Abonos Globales
        abonos_globales = sum([float(p.monto) for p in c.pagos if not p.quote_id and not p.cargo_id])
        saldo_ini = float(c.saldo_inicial or 0)
        
        # Pagar saldo inicial primero
        if abonos_globales >= saldo_ini:
            abonos_globales -= saldo_ini
        else:
            abonos_globales = 0

        # Ver qué cargos quedaron sin pagar o pagados parcialmente
        sorted_cargos = sorted(c.cargos, key=lambda x: x.fecha)
        for cg in sorted_cargos:
            costo = float(cg.monto)
            if abonos_globales >= costo:
                abonos_globales -= costo
            else:
                if (costo - abonos_globales) > 0.1:
                    active_counts += 1
                abonos_globales = 0

        # Cálculos Económicos Exactos (Sin saldo_inicial estático)
        total_pagado_cliente = sum([float(p.monto) for p in c.pagos])
        total_comprado_sistema = sum([float(q.total) for q in c.cotizaciones if q.estado in ESTADOS_COBRABLES])
        total_cargos_extra = sum([float(cg.monto) for cg in c.cargos])

        # Deuda Histórica = Suma de todo lo cobrable + saldo inicial
        deuda_historica_cliente = total_comprado_sistema + total_cargos_extra + float(c.saldo_inicial or 0)
        
        # Saldo Global Pendiente = Deuda Total - Todo lo Pagado
        saldo_global_calculado = deuda_historica_cliente - total_pagado_cliente

        if saldo_global_calculado > 0.01:
            active_accounts.append(
                {
                    "cliente_id": c.id,
                    "cliente_nombre": c.nombre,
                    "total_deuda_global": deuda_historica_cliente,
                    "saldo_global": saldo_global_calculado,
                    "cotizaciones_activas": active_counts,
                }
            )

    return active_accounts


@router.get("/statement/customer/{customer_id}")
def get_customer_statement(
    *, session: Session = Depends(get_session), customer_id: int
):
    """Obtiene estado de cuenta consolidado de un cliente."""
    # 1. Obtener cliente
    from app.models import Customer

    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # 2. Obtener todas sus cotizaciones con estados cobrables
    query = (
        select(Quote)
        .where(Quote.cliente_id == customer_id)
        .where(Quote.estado.in_(ESTADOS_COBRABLES))
        .options(selectinload(Quote.pagos))
        .order_by(Quote.fecha_creacion.desc())
    )
    quotes = session.exec(query).all()

    # Obtener Cargos
    from app.models import AccountCharge
    cargos_query = select(AccountCharge).where(AccountCharge.cliente_id == customer_id).options(selectinload(AccountCharge.pagos)).order_by(AccountCharge.fecha.desc())
    cargos = session.exec(cargos_query).all()
    total_cargos = sum([float(c.monto) for c in cargos])

    # 3. Calcular pagos directos (sin cotización vinculada)
    from app.models import Payment

    direct_payments_query = (
        select(Payment)
        .where(Payment.cliente_id == customer_id)
        .where(Payment.quote_id.is_(None))
    )
    direct_payments = session.exec(direct_payments_query).all()
    total_abonos_directos = sum([float(p.monto) for p in direct_payments])

    # 4. Calcular totales
    total_comprado = 0.0
    total_pagado_quotes = 0.0
    saldo_quotes = 0.0

    quotes_data = []

    for q in quotes:
        pagado = sum([float(p.monto) for p in q.pagos])
        saldo = float(q.total) - pagado

        total_comprado += float(q.total)
        total_pagado_quotes += pagado
        saldo_quotes += saldo

        quotes_data.append(
            {
                "id": q.id,
                "fecha": q.fecha_creacion,
                "total": float(q.total),
                "pagado": pagado,
                "saldo": saldo,
                "estado": q.estado,
            }
        )

    # El saldo global incluye puramente la suma: Saldo Inicial + Total Comprado + Total Cargos - Total Pagado
    deuda_historica = float(customer.saldo_inicial or 0) + total_comprado + total_cargos
    total_pagado = total_pagado_quotes + total_abonos_directos
    saldo_global = deuda_historica - total_pagado

    return {
        "cliente": {
            "id": customer.id,
            "nombre": customer.nombre,
            "email": customer.email,
            "telefono": customer.telefono,
        },
        "global": {
            "total_comprado": total_comprado + total_cargos,
            "total_pagado": total_pagado_quotes + total_abonos_directos,
            "saldo_pendiente": saldo_global,
            "abonos_directos": total_abonos_directos,
        },
        "cotizaciones": quotes_data,
        "cargos": [
            {
                "id": c.id,
                "fecha": c.fecha,
                "detalle": c.detalle,
                "monto": float(c.monto),
                "pagado": sum([float(p.monto) for p in c.pagos]),
                "saldo": float(c.monto) - sum([float(p.monto) for p in c.pagos]),
                "documentado": c.documentado,
                "folio_nota": c.folio_nota,
                "estatus": c.estatus,
            }
            for c in cargos
        ],
        "pagos_directos": [
            {
                "id": p.id,
                "fecha": p.fecha_pago,
                "monto": float(p.monto),
                "metodo": p.metodo_pago,
                "ref": p.referencia,
            }
            for p in direct_payments
        ],
    }


@router.get("/statement/customer/{customer_id}/pdf")
def get_customer_statement_pdf(*, session: Session = Depends(get_session), customer_id: int):
    """Genera estado de cuenta en PDF listando movimientos cronológicos."""
    from app.models import Customer, AccountCharge
    from datetime import datetime

    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Obtener cotizaciones con estados cobrables
    quotes_query = select(Quote).where(
        Quote.cliente_id == customer_id,
        Quote.estado.in_(ESTADOS_COBRABLES)
    ).options(selectinload(Quote.pagos))
    quotes = session.exec(quotes_query).all()

    # Obtener cargos manuales
    cargos_query = select(AccountCharge).where(AccountCharge.cliente_id == customer_id)
    cargos = session.exec(cargos_query).all()

    # Obtener TODOS los pagos del cliente
    payments_query = select(Payment).where(Payment.cliente_id == customer_id)
    payments = session.exec(payments_query).all()

    total_comprado = sum([float(q.total) for q in quotes])
    total_cargos = sum([float(c.monto) for c in cargos])
    total_pagos = sum([float(p.monto) for p in payments])

    deuda_historica = float(customer.saldo_inicial or 0) + total_comprado + total_cargos
    saldo_pendiente = deuda_historica - total_pagos

    # Build movements timeline
    movements = []

    for q in quotes:
        if float(q.total) > 0:
            movements.append({
                "raw_date": q.fecha_creacion,
                "fecha": q.fecha_creacion.strftime('%d/%m/%Y'),
                "origen": f"Cotización #{q.id}",
                "descripcion": f"Proyecto (Estado: {q.estado})",
                "tipo": "Cargo",
                "cargo": float(q.total),
                "abono": 0.0
            })

    for c in cargos:
        if float(c.monto) > 0:
            movements.append({
                "raw_date": c.fecha,
                "fecha": c.fecha.strftime('%d/%m/%Y'),
                "origen": "Servicio Directo",
                "descripcion": c.detalle,
                "tipo": "Cargo",
                "cargo": float(c.monto),
                "abono": 0.0
            })

    for p in payments:
        if float(p.monto) > 0:
            ref = f" - Ref: {p.referencia}" if p.referencia else ""
            if p.quote_id:
                vinculo = f" Cot. #{p.quote_id}"
            elif p.cargo_id:
                vinculo = f" Servicio #{p.cargo_id}"
            else:
                vinculo = " Abono Global"
            movements.append({
                "raw_date": p.fecha_pago,
                "fecha": p.fecha_pago.strftime('%d/%m/%Y'),
                "origen": f"Pago a{vinculo}",
                "descripcion": f"Método: {p.metodo_pago}{ref}",
                "tipo": "Abono",
                "cargo": 0.0,
                "abono": float(p.monto)
            })

    # Sort chronological
    movements.sort(key=lambda x: x["raw_date"])

    try:
        html_content = templates.get_template("pdf/statement.html").render(
            client_name=customer.nombre,
            client_id=customer.id,
            client_email=customer.email,
            client_telefono=customer.telefono,
            fecha_generacion=datetime.now().strftime('%d/%m/%Y'),
            saldo_inicial=float(customer.saldo_inicial or 0),
            deuda_historica=deuda_historica,
            saldo_pendiente=saldo_pendiente,
            movements=movements
        )
        pdf_bytes = generate_pdf_bytes(html_content)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=estado_cuenta_{customer.id}.pdf"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generando PDF de Estado de Cuenta: {str(e)}")


@router.post("/charges", response_model=AccountCharge)
def create_charge(*, session: Session = Depends(get_session), charge_in: AccountChargeCreate):
    from app.models import Customer
    if not charge_in.cliente_id:
        raise HTTPException(status_code=400, detail="Debe vincular el cargo a un cliente.")
    
    cliente = session.get(Customer, charge_in.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    db_charge = AccountCharge.from_orm(charge_in)
    session.add(db_charge)
    session.commit()
    session.refresh(db_charge)
    return db_charge


class RemissionRequest(BaseModel):
    charge_ids: List[int]

@router.post("/remission")
def generate_charge_remission(*, session: Session = Depends(get_session), req: RemissionRequest):
    if not req.charge_ids:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un cargo.")

    cargos = session.exec(select(AccountCharge).where(AccountCharge.id.in_(req.charge_ids))).all()
    if not cargos:
        raise HTTPException(status_code=404, detail="No se encontraron los cargos seleccionados.")

    cliente = cargos[0].cliente
    
    current_year = datetime.now().year
    prefix = f"N{current_year}"
    
    # Encontrar el último folio_nota con formato N2026XXX
    all_folios = session.exec(select(AccountCharge.folio_nota).where(AccountCharge.folio_nota.like(f"{prefix}%"))).all()
    max_num = 0
    for f in all_folios:
        if f:
            core = f.split('-')[0]
            if core.startswith(prefix):
                try:
                    num_str = core[len(prefix):]
                    if num_str.isdigit():
                        num = int(num_str)
                        if num > max_num:
                            max_num = num
                except ValueError:
                    pass
                
    nuevo_folio = f"{prefix}{(max_num + 1):04d}"
    
    for c in cargos:
        c.documentado = True
        c.folio_nota = nuevo_folio
        c.estatus = 'Remisión Emitida'
        session.add(c)
        
    session.commit()

    total_remission = sum([float(c.monto) for c in cargos])

    # Generar PDF
    try:
        html_content = templates.get_template("pdf/remission.html").render(
            cliente=cliente,
            cargos=cargos,
            total=total_remission,
            folio=nuevo_folio
        )
        pdf_bytes = generate_pdf_bytes(html_content)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="remision_{nuevo_folio}.pdf"',
                "X-Folio-Nota": nuevo_folio,
                "Access-Control-Expose-Headers": "X-Folio-Nota"
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")


@router.post("/", response_model=Payment)
def create_payment(
    *, session: Session = Depends(get_session), payment_in: PaymentCreate
):
    if not payment_in.quote_id and not payment_in.cliente_id and not payment_in.cargo_id:
        raise HTTPException(
            status_code=400,
            detail="Debe vincular el pago a una cotización, a un cargo o a un cliente directamente.",
        )

    if payment_in.quote_id:
        quote = session.get(Quote, payment_in.quote_id)
        if not quote:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")

    if payment_in.cargo_id:
        cargo = session.get(AccountCharge, payment_in.cargo_id)
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo o Servicio no encontrado")

    db_payment = Payment.from_orm(payment_in)
    session.add(db_payment)
    session.commit()
    session.refresh(db_payment)
    return db_payment


@router.get("/by-quote/{quote_id}", response_model=List[Payment])
def read_payments_by_quote(*, session: Session = Depends(get_session), quote_id: int):
    query = (
        select(Payment)
        .where(Payment.quote_id == quote_id)
        .order_by(Payment.fecha_pago.desc())
    )
    payments = session.exec(query).all()
    return payments


@router.get("/", response_model=List[Payment])
def read_payments(*, session: Session = Depends(get_session)):
    query = (
        select(Payment)
        .options(selectinload(Payment.cliente))
        .order_by(Payment.fecha_pago.desc())
    )
    payments = session.exec(query).all()
    return payments


@router.get("/statement/{quote_id}")
def get_account_statement(*, session: Session = Depends(get_session), quote_id: int):
    # Obtener cotizacion con pagos
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # query payments explicitly to ensure fresh data
    query = (
        select(Payment).where(Payment.quote_id == quote_id).order_by(Payment.fecha_pago)
    )
    payments = session.exec(query).all()

    total_pagado = sum([p.monto for p in payments])
    saldo_pendiente = quote.total - total_pagado

    # Análisis de progreso
    progreso = 0
    if quote.total > 0:
        progreso = (total_pagado / quote.total) * 100

    return {
        "quote": quote,
        "total_pagado": total_pagado,
        "saldo_pendiente": saldo_pendiente,
        "progreso": round(progreso, 1),
        "pagos": payments,
    }
