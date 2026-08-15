from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Payment, Quote, AccountCharge, User
from app.schemas import PaymentCreate, AccountChargeCreate
from pydantic import BaseModel
from fastapi import Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import selectinload
from app.core.pdf import generate_pdf_bytes
from app.api.deps import (
    get_current_user,
    get_current_active_admin,
    get_current_active_operativo_or_admin,
)
from app.models import RoleEnum
from app.core.accounting import DEBT_ESTADOS, calcular_saldo_cliente, saldo_de_cotizacion, money, sum_decimal, _decimal
from app.core.timeutils import now_local
from app.core.paths import BASE_DIR, TEMPLATES_DIR, REPORTS_DIR
from decimal import Decimal
import unicodedata, re
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


def _safe_name(text: str, max_len: int = 20) -> str:
    """Normaliza un nombre para usar en filename: sin acentos, solo alfanuméricos/guion bajo."""
    nfkd = unicodedata.normalize('NFKD', text or '')
    ascii_str = nfkd.encode('ascii', 'ignore').decode('ascii')
    clean = re.sub(r'[^\w]', '_', ascii_str).strip('_')
    clean = re.sub(r'_+', '_', clean)
    return clean[:max_len]


@router.get("/active")
def read_active_statements(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin)
):
    # Obtener cotizaciones con total > 0 que NO estén rechazadas o en borrador (opcional, pero asumimos que solo 'Enviada'/'Aprobada' cuentan)
    # Por lealtad al usuario, mostraremos todas las que tengan saldo, independientemente del estado,
    # aunque logico seria solo Aprobada. Vamos filtrar solo Aprobada para ser más limpios, o todas.
    # El usuario pidio "todos los estados activos". Asumiremos todas las cotizaciones con deuda.

    query = (
        select(Quote)
        .options(selectinload(Quote.pagos))
        .options(selectinload(Quote.cliente))
        .where(Quote.estado.in_(DEBT_ESTADOS))
        .order_by(Quote.id.desc())
    )
    quotes = session.exec(query).all()

    active_accounts = []

    for q in quotes:
        total_pagado = sum_decimal(p.monto for p in q.pagos)
        saldo = _decimal(q.total) - total_pagado

        if saldo > Decimal("0.1"):  # Tolerancia de centavos
            active_accounts.append(
                {
                    "id": q.id,
                    "cliente": q.cliente.nombre if q.cliente else "N/A",
                    "total": money(q.total),
                    "pagado": money(total_pagado),
                    "saldo": money(saldo),
                    "estado": q.estado,
                }
            )

    return active_accounts


@router.get("/active-customers")
def read_active_customers(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin)
):
    """Obtiene lista de clientes con deuda activa (saldo inicial + cotizaciones - pagos)."""
    from app.models import Customer

    # Obtener todos los clientes con sus cotizaciones y TODOS sus pagos
    query = select(Customer).options(
        selectinload(Customer.cotizaciones).selectinload(Quote.pagos),
        selectinload(Customer.pagos),
        selectinload(Customer.cargos).selectinload(AccountCharge.pagos),
    )
    customers = session.exec(query).all()

    active_accounts = []

    for c in customers:
        active_counts = 0

        for q in c.cotizaciones:
            if q.estado not in DEBT_ESTADOS:
                continue
            if saldo_de_cotizacion(q) > Decimal("0.1"):
                active_counts += 1

        # Para los cargos (sin vinculación directa de pagos), se pagan con Abonos Globales
        abonos_globales = sum_decimal(p.monto for p in c.pagos if not p.quote_id and not p.cargo_id)
        saldo_ini = _decimal(c.saldo_inicial or 0)
        
        # Pagar saldo inicial primero
        if abonos_globales >= saldo_ini:
            abonos_globales -= saldo_ini
        else:
            abonos_globales = Decimal("0")

        # Ver qué cargos quedaron sin pagar o pagados parcialmente
        sorted_cargos = sorted(c.cargos, key=lambda x: x.fecha)
        for cg in sorted_cargos:
            costo = _decimal(cg.monto)
            if abonos_globales >= costo:
                abonos_globales -= costo
            else:
                if (costo - abonos_globales) > Decimal("0.1"):
                    active_counts += 1
                abonos_globales = Decimal("0")

        # Totales económicos unificados (misma regla que todos los endpoints)
        fin = calcular_saldo_cliente(c)

        if fin["saldo"] > Decimal("0.01"):
            active_accounts.append(
                {
                    "cliente_id": c.id,
                    "cliente_nombre": c.nombre,
                    "total_deuda_global": money(fin["deuda_total"]),
                    "saldo_global": money(fin["saldo"]),
                    "cotizaciones_activas": active_counts,
                }
            )

    return active_accounts


@router.get("/statement/customer/{customer_id}")
def get_customer_statement(
    *, session: Session = Depends(get_session), customer_id: int,
    current_user: User = Depends(get_current_user)
):
    """Obtiene estado de cuenta consolidado de un cliente."""
    # El cliente solo puede ver su propio estado
    if current_user.role == RoleEnum.Cliente:
        if current_user.cliente_id != customer_id:
            raise HTTPException(status_code=403, detail="Solo puedes ver tu propio estado de cuenta")
    elif current_user.role == RoleEnum.Operativo:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    # 1. Obtener cliente
    from app.models import Customer

    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # 2. Obtener todas sus cotizaciones aprobadas
    query = (
        select(Quote)
        .where(Quote.cliente_id == customer_id)
        .where(Quote.estado.in_(DEBT_ESTADOS))
        .options(selectinload(Quote.pagos))
        .order_by(Quote.fecha_creacion.desc())
    )
    quotes = session.exec(query).all()

    # Obtener Cargos
    from app.models import AccountCharge
    cargos_query = select(AccountCharge).where(AccountCharge.cliente_id == customer_id).options(selectinload(AccountCharge.pagos)).order_by(AccountCharge.fecha.desc())
    cargos = session.exec(cargos_query).all()
    total_cargos = sum_decimal(c.monto for c in cargos)

    # 3. Calcular pagos directos (sin cotización vinculada)
    from app.models import Payment

    direct_payments_query = (
        select(Payment)
        .where(Payment.cliente_id == customer_id)
        .where(Payment.quote_id.is_(None))
    )
    direct_payments = session.exec(direct_payments_query).all()
    total_abonos_directos = sum_decimal(p.monto for p in direct_payments)

    # 4. Calcular totales
    total_comprado = Decimal("0")
    total_pagado_quotes = Decimal("0")
    saldo_quotes = Decimal("0")

    quotes_data = []

    for q in quotes:
        pagado = sum_decimal(p.monto for p in q.pagos)
        saldo = _decimal(q.total) - pagado

        total_comprado += _decimal(q.total)
        total_pagado_quotes += pagado
        saldo_quotes += saldo

        quotes_data.append(
            {
                "id": q.id,
                "fecha": q.fecha_creacion,
                "total": money(q.total),
                "pagado": money(pagado),
                "saldo": money(saldo),
                "estado": q.estado,
                "folio_cotizacion": q.folio_cotizacion,
                "tipo_pago": q.tipo_pago,
                "monto_semanal": money(q.monto_semanal or 0),
                "plazo_semanas": q.plazo_semanas,
            }
        )

    # Totales globales unificados (misma regla que todos los endpoints)
    fin = calcular_saldo_cliente(customer)

    # Todos los pagos para el historial
    all_payments_query = select(Payment).where(Payment.cliente_id == customer_id).order_by(Payment.fecha_pago.desc())
    all_payments = session.exec(all_payments_query).all()

    return {
        "cliente": {
            "id": customer.id,
            "nombre": customer.nombre,
            "email": customer.email,
            "telefono": customer.telefono,
        },
        "global": {
            "total_comprado": money(fin["total_comprado"] + fin["total_cargos"]),
            "total_pagado": money(fin["total_pagado"]),
            "saldo_pendiente": money(fin["saldo"]),
            "abonos_directos": money(total_abonos_directos),
        },
        "cotizaciones": quotes_data,
        "cargos": [
            {
                "id": c.id,
                "fecha": c.fecha,
                "detalle": c.detalle,
                "monto": money(c.monto),
                "pagado": money(sum_decimal(p.monto for p in c.pagos)),
                "saldo": money(_decimal(c.monto) - sum_decimal(p.monto for p in c.pagos)),
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
                "monto": money(p.monto),
                "metodo": p.metodo_pago,
                "ref": p.referencia,
            }
            for p in direct_payments
        ],
        "todos_los_pagos": [
            {
                "id": p.id,
                "fecha": p.fecha_pago,
                "monto": money(p.monto),
                "metodo": p.metodo_pago,
                "ref": p.referencia,
                "quote_id": p.quote_id,
                "cargo_id": p.cargo_id
            }
            for p in all_payments
        ],
    }


@router.get("/statement/customer/{customer_id}/pdf")
def get_customer_statement_pdf(
    *, session: Session = Depends(get_session), customer_id: int,
    full: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Genera estado de cuenta en PDF. Cliente solo puede ver el suyo."""
    # El cliente solo puede descargar su propio PDF
    if current_user.role == RoleEnum.Cliente:
        if current_user.cliente_id != customer_id:
            raise HTTPException(status_code=403, detail="Solo puedes descargar tu propio estado de cuenta")
    elif current_user.role == RoleEnum.Operativo:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    from app.models import Customer, AccountCharge

    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Obtener cotizaciones aprobadas
    quotes_query = select(Quote).where(
        Quote.cliente_id == customer_id,
        Quote.estado.in_(DEBT_ESTADOS)
    ).options(selectinload(Quote.pagos))
    quotes = session.exec(quotes_query).all()

    # Obtener cargos manuales
    cargos_query = select(AccountCharge).where(AccountCharge.cliente_id == customer_id)
    cargos = session.exec(cargos_query).all()

    # Obtener TODOS los pagos del cliente
    payments_query = select(Payment).where(Payment.cliente_id == customer_id)
    payments = session.exec(payments_query).all()

    # Totales globales unificados (misma regla que todos los endpoints)
    fin = calcular_saldo_cliente(customer)
    deuda_historica = money(fin["deuda_total"])
    saldo_pendiente = money(fin["saldo"])

    # Build movements timeline
    movements = []

    for q in quotes:
        if _decimal(q.total) > 0:
            movements.append({
                "raw_date": q.fecha_creacion,
                "fecha": q.fecha_creacion.strftime('%d/%m/%Y'),
                "origen": f"Cotización #{q.id}",
                "descripcion": f"Proyecto (Estado: {q.estado})",
                "tipo": "Cargo",
                "cargo": money(q.total),
                "abono": 0.0
            })

    for c in cargos:
        if _decimal(c.monto) > 0:
            movements.append({
                "raw_date": c.fecha,
                "fecha": c.fecha.strftime('%d/%m/%Y'),
                "origen": "Servicio Directo",
                "descripcion": c.detalle,
                "tipo": "Cargo",
                "cargo": money(c.monto),
                "abono": 0.0
            })

    for p in payments:
        if _decimal(p.monto) > 0:
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
                "abono": money(p.monto)
            })

    # Ordenar del más reciente al menos reciente
    movements.sort(key=lambda x: x["raw_date"], reverse=True)

    full_history = full  # alias semántico para el template
    if not full_history and len(movements) > 9:
        movements = movements[:9]

    tipo_documento = "Historial Completo" if full_history else "Últimos 9 Movimientos"

    try:
        html_content = templates.get_template("pdf/statement.html").render(
            client_name=customer.nombre,
            client_id=customer.id,
            client_email=customer.email,
            client_telefono=customer.telefono,
            fecha_generacion=now_local().strftime('%d/%m/%Y'),
            saldo_inicial=money(customer.saldo_inicial or 0),
            deuda_historica=deuda_historica,
            saldo_pendiente=saldo_pendiente,
            movements=movements,
            full_history=full_history,
            tipo_documento=tipo_documento,
        )
        bg_file_path = BASE_DIR / "FORMATO BASE PARA ESTADOS DE CUENTA (2) (2).pdf"
        pdf_bytes = generate_pdf_bytes(
            html_content,
            bg_pdf_path=str(bg_file_path) if bg_file_path.exists() else None
        )
        nombre_safe = _safe_name(customer.nombre)
        suffix = "_Completo" if full_history else "_Ultimos9"
        pdf_name = f"Estado_Cuenta_CLI{customer.id:04d}_{nombre_safe}{suffix}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{pdf_name}"'}
        )
    except Exception as e:
        logger.error("Error generando PDF de Estado de Cuenta: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno generando el estado de cuenta")


@router.post("/charges", response_model=AccountCharge)
def create_charge(
    *,
    session: Session = Depends(get_session),
    charge_in: AccountChargeCreate,
    current_user: User = Depends(get_current_active_admin)
):
    from app.models import Customer
    if not charge_in.cliente_id:
        raise HTTPException(status_code=400, detail="Debe vincular el cargo a un cliente.")
    
    cliente = session.get(Customer, charge_in.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    db_charge = AccountCharge.model_validate(charge_in.model_dump())
    session.add(db_charge)
    session.commit()
    session.refresh(db_charge)
    return db_charge


class RemissionRequest(BaseModel):
    charge_ids: List[int]


# ── GET: Descargar PDF de remisión existente por folio ────────────────────────
@router.get("/remission/{folio}")
def download_remission_by_folio(
    folio: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin),
):
    """Regenera y descarga el PDF de una remision existente dado su folio."""
    import os
    from app.models import Customer

    # 1. Buscar cargos cargando la relacion cliente explicitamente
    cargos = session.exec(
        select(AccountCharge)
        .where(AccountCharge.folio_nota == folio)
        .options(selectinload(AccountCharge.cliente))
    ).all()
    if not cargos:
        raise HTTPException(status_code=404, detail=f"No se encontro la remision con folio {folio}")

    cliente = cargos[0].cliente or session.get(Customer, cargos[0].cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente de la remision no encontrado")

    nombre_safe = _safe_name(cliente.nombre)
    pdf_filename = f"Remision_{folio}_CLI{cliente.id:04d}_{nombre_safe}.pdf"

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Buscar cualquier variante del PDF en disco
    existing = [f for f in os.listdir(str(REPORTS_DIR))
                if f.lower().startswith(f"remision_{folio.lower()}")]
    if existing:
        with open(str(REPORTS_DIR / existing[0]), "rb") as f:
            pdf_bytes = f.read()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{pdf_filename}"'},
        )

    # 3. Regenerar desde BD
    total_remission = sum_decimal(c.monto for c in cargos)
    try:
        html_content = templates.get_template("pdf/remission.html").render(
            cliente=cliente,
            cargos=cargos,
            total=money(total_remission),
            folio=folio,
        )
        pdf_bytes = generate_pdf_bytes(html_content)
        pdf_path = str(REPORTS_DIR / pdf_filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{pdf_filename}"'},
        )
    except Exception as e:
        logger.error("Error regenerando PDF de remisión: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno regenerando el PDF")

@router.post("/remission")
def generate_charge_remission(
    *,
    session: Session = Depends(get_session),
    req: RemissionRequest,
    current_user: User = Depends(get_current_active_admin)
):
    if not req.charge_ids:
        raise HTTPException(status_code=400, detail="Debe enviar al menos un cargo.")

    cargos = session.exec(select(AccountCharge).where(AccountCharge.id.in_(req.charge_ids))).all()
    if not cargos:
        raise HTTPException(status_code=404, detail="No se encontraron los cargos seleccionados.")

    cliente = cargos[0].cliente

    # ── Folio atómico ─────────────────────────────────────────────────────────
    # Para evitar carreras (dos remisiones concurrentes con el mismo folio),
    # primero adquirimos el lock de escritura con un flush, y SOLO después
    # calculamos el folio dentro de la misma transacción. SQLite serializa
    # escritores, así que el SELECT del folio ve el estado ya bloqueado.
    current_year = now_local().year
    prefix = f"N{current_year}"

    try:
        for c in cargos:
            c.documentado = True
            session.add(c)
        session.flush()  # adquiere el lock de escritura

        # Encontrar el último folio_nota con formato N{year}XXXX
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
            c.folio_nota = nuevo_folio
            c.estatus = 'Remisión Emitida'
            session.add(c)

        session.commit()
    except Exception:
        session.rollback()
        raise

    total_remission = sum_decimal(c.monto for c in cargos)

    # Generar PDF
    try:
        html_content = templates.get_template("pdf/remission.html").render(
            cliente=cliente,
            cargos=cargos,
            total=money(total_remission),
            folio=nuevo_folio
        )
        pdf_bytes = generate_pdf_bytes(html_content)

        # ── Guardar PDF permanentemente en disco ──────────────────────────────
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        pdf_filename = f"Remision_{nuevo_folio}_CLI{cliente.id:04d}_{_safe_name(cliente.nombre)}.pdf"
        pdf_path = str(REPORTS_DIR / pdf_filename)
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        # ─────────────────────────────────────────────────────────────────────

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{pdf_filename}"',
                "X-Folio-Nota": nuevo_folio,
                "X-PDF-Path": f"/static/reports/{pdf_filename}",
                "Access-Control-Expose-Headers": "X-Folio-Nota, X-PDF-Path"
            }
        )
    except Exception as e:
        logger.error("Error generando PDF de remisión: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno generando el PDF")


@router.post("/", response_model=Payment)
def create_payment(
    *, session: Session = Depends(get_session), payment_in: PaymentCreate,
    current_user: User = Depends(get_current_active_admin)
):
    if not payment_in.quote_id and not payment_in.cliente_id and not payment_in.cargo_id:
        raise HTTPException(
            status_code=400,
            detail="Debe vincular el pago a una cotización, a un cargo o a un cliente directamente.",
        )

    monto_pago = _decimal(payment_in.monto)
    if monto_pago <= 0:
        raise HTTPException(status_code=400, detail="El monto del pago debe ser mayor a cero")

    quote = None
    cargo = None
    cliente = None

    if payment_in.quote_id:
        quote = session.get(Quote, payment_in.quote_id)
        if not quote:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        # Coherencia: el pago debe pertenecer al mismo cliente de la cotización
        if payment_in.cliente_id and payment_in.cliente_id != quote.cliente_id:
            raise HTTPException(
                status_code=400,
                detail="El cliente del pago no coincide con el cliente de la cotización",
            )
        # Sin sobrepago sobre el saldo de la cotización
        if quote.estado in DEBT_ESTADOS:
            saldo = saldo_de_cotizacion(quote)
            if monto_pago > saldo + Decimal("0.01"):
                raise HTTPException(
                    status_code=400,
                    detail=f"El pago excede el saldo pendiente de la cotización (saldo: ${money(saldo)})",
                )

    if payment_in.cargo_id:
        cargo = session.get(AccountCharge, payment_in.cargo_id)
        if not cargo:
            raise HTTPException(status_code=404, detail="Cargo o Servicio no encontrado")
        # Coherencia: el pago debe pertenecer al mismo cliente del cargo
        if payment_in.cliente_id and payment_in.cliente_id != cargo.cliente_id:
            raise HTTPException(
                status_code=400,
                detail="El cliente del pago no coincide con el cliente del cargo",
            )
        # Sin sobrepago sobre el saldo del cargo
        pagado_cargo = sum_decimal(p.monto for p in (cargo.pagos or []))
        saldo_cargo = _decimal(cargo.monto) - pagado_cargo
        if monto_pago > saldo_cargo + Decimal("0.01"):
            raise HTTPException(
                status_code=400,
                detail=f"El pago excede el saldo pendiente del cargo (saldo: ${money(saldo_cargo)})",
            )

    if not quote and not cargo:
        # Abono global: debe existir el cliente vinculado
        from app.models import Customer
        cliente = session.get(Customer, payment_in.cliente_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

    db_payment = Payment.model_validate(payment_in.model_dump())
    session.add(db_payment)
    session.commit()
    session.refresh(db_payment)
    return db_payment


@router.get("/by-quote/{quote_id}", response_model=List[Payment])
def read_payments_by_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: int,
    current_user: User = Depends(get_current_active_admin)
):
    query = (
        select(Payment)
        .where(Payment.quote_id == quote_id)
        .order_by(Payment.fecha_pago.desc())
    )
    payments = session.exec(query).all()
    return payments


@router.get("/", response_model=List[Payment])
def read_payments(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_admin)
):
    query = (
        select(Payment)
        .options(selectinload(Payment.cliente))
        .order_by(Payment.fecha_pago.desc())
    )
    payments = session.exec(query).all()
    return payments


@router.get("/statement/{quote_id}")
def get_account_statement(
    *, session: Session = Depends(get_session), quote_id: int,
    current_user: User = Depends(get_current_user)
):
    # Obtener cotizacion con pagos
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # El cliente solo puede ver sus propias cotizaciones
    if current_user.role == RoleEnum.Cliente:
        if current_user.cliente_id != quote.cliente_id:
            raise HTTPException(status_code=403, detail="Solo puedes ver tu propio estado de cuenta")
    elif current_user.role == RoleEnum.Operativo:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")

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


@router.delete("/{payment_id}", status_code=204)
def delete_payment(
    *, session: Session = Depends(get_session), payment_id: int,
    current_user: User = Depends(get_current_active_admin)
):
    payment = session.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
        
    session.delete(payment)
    session.commit()
    return Response(status_code=204)

