import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.database import get_session
from app.models import Quote, QuoteItem, Product, Customer, User
from app.schemas import QuoteCreate, QuoteRead, QuoteUpdate
from app.core.pdf import generate_pdf_bytes
from app.core.accounting import money
from app.core.timeutils import now_local
from app.core.paths import BASE_DIR, TEMPLATES_DIR, REPORTS_DIR
from urllib.parse import quote as quote_url
from sqlalchemy.orm import selectinload
from decimal import Decimal
from app.api.deps import (
    get_current_user,
    get_current_active_admin,
    get_current_active_operativo_or_admin,
    require_role,
)
from app.models import RoleEnum, QuoteEstado
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()

def get_next_quote_folio(session: Session) -> str:
    current_year = now_local().year
    prefix = f"C{current_year}"
    
    # Busca cotizaciones del año actual
    all_folios = session.exec(select(Quote.folio_cotizacion).where(Quote.folio_cotizacion.like(f"{prefix}%"))).all()
    
    max_num = 0
    for f in all_folios:
        if f:
            # Elimina el -V# si lo tiene para basarnos en el número principal
            core = f.split('-V')[0]
            if core.startswith(prefix):
                try:
                    num_str = core[len(prefix):]
                    if num_str.isdigit():
                        num = int(num_str)
                        if num > max_num:
                            max_num = num
                except ValueError:
                    pass
                    
    return f"{prefix}{(max_num + 1):04d}"



@router.post("/", response_model=Quote)
def create_quote(
    *,
    session: Session = Depends(get_session),
    quote_in: QuoteCreate,
    current_user: User = Depends(get_current_active_admin)
):
    # 1. Validar cliente
    cliente = session.get(Customer, quote_in.cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # ── Validaciones y cálculos previos (sin persistir nada) ──────────────────
    items_validados = []  # (producto, cantidad, precio, costo)
    total_cotizacion = Decimal("0")
    utilidad_acumulada = Decimal("0")

    for item_in in quote_in.items:
        producto = session.get(Product, item_in.producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail=f"Producto {item_in.producto_id} no encontrado")

        # Validar stock disponible (solo para Productos, no para Servicios)
        es_servicio = (producto.categoria or "").strip().lower() == "servicio"
        if not es_servicio and producto.stock < item_in.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Producto '{producto.nombre}' no tiene suficiente stock. Disponible: {producto.stock}, Solicitado: {item_in.cantidad}"
            )

        # Usamos el precio unitario pactado manualmente desde el frontend
        precio_aplicado = Decimal(str(item_in.precio_unitario))
        costo_producto = Decimal(str(producto.costo or 0))
        items_validados.append((producto, item_in.cantidad, precio_aplicado, costo_producto))

        total_cotizacion += precio_aplicado * item_in.cantidad
        utilidad_acumulada += (precio_aplicado - costo_producto) * item_in.cantidad

    # 4. Calcular total, subtotal, IVA y utilidad
    if quote_in.total_manual is not None and quote_in.total_manual > 0:
        total_final = Decimal(str(quote_in.total_manual))
        if quote_in.requiere_factura:
            subtotal_final = total_final / Decimal("1.16")
            iva_final = total_final - subtotal_final
        else:
            subtotal_final = total_final
            iva_final = Decimal("0")
        costo_total = sum((cantidad * costo for _, cantidad, _, costo in items_validados), Decimal("0"))
        utilidad_final = subtotal_final - costo_total
    else:
        subtotal_final = total_cotizacion
        iva_final = subtotal_final * Decimal("0.16") if quote_in.requiere_factura else Decimal("0")
        total_final = subtotal_final + iva_final
        utilidad_final = utilidad_acumulada

    # Validar que el anticipo no exceda el total
    if quote_in.anticipo and Decimal(str(quote_in.anticipo)) > total_final:
        raise HTTPException(
            status_code=400,
            detail=f"El anticipo (${quote_in.anticipo}) no puede ser mayor que el total (${total_final})"
        )

    # ── Persistencia en una sola transacción ──────────────────────────────────
    db_quote = Quote(
        cliente_id=quote_in.cliente_id,
        filial=quote_in.filial,
        agente=quote_in.agente,
        notas=quote_in.notas,
        anticipo=quote_in.anticipo,
        tipo_pago=quote_in.tipo_pago,
        requiere_factura=quote_in.requiere_factura,
        fecha_inicio_pago=quote_in.fecha_inicio_pago,
        fecha_fin_pago=quote_in.fecha_fin_pago,
        plazo_semanas=quote_in.plazo_semanas,
        monto_semanal=quote_in.monto_semanal,
        padre_id=quote_in.padre_id,
        motivo_edicion=quote_in.motivo_edicion,
        version=1,
        subtotal=subtotal_final,
        iva=iva_final,
        total=total_final,
        utilidad_total=utilidad_final,
    )

    try:
        # Lógica de Mutación / Versión
        if quote_in.padre_id:
            madre = session.get(Quote, quote_in.padre_id)
            if not madre:
                raise HTTPException(status_code=400, detail="Cotización padre no existe")
            madre.estado = QuoteEstado.Sustituida.value
            session.add(madre)
            db_quote.version = madre.version + 1
            # Si la madre NO tenia folio por se antigua formamos la base
            if madre.folio_cotizacion:
                folio_base = madre.folio_cotizacion.split("-V")[0]
            else:
                folio_base = f"C{madre.fecha_creacion.year}{(madre.id or 0):04d}"
            db_quote.folio_cotizacion = f"{folio_base}-V{db_quote.version}"

        session.add(db_quote)
        session.flush()  # asigna ID dentro de la misma transacción

        # Si es nueva 100%, asignamos su folio usando el año actual y su ID recién creado
        if not quote_in.padre_id:
            db_quote.folio_cotizacion = get_next_quote_folio(session)

        # 3. Agregar items
        for producto, cantidad, precio_aplicado, _costo in items_validados:
            session.add(QuoteItem(
                cotizacion_id=db_quote.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio_aplicado,
            ))

        session.add(db_quote)
        session.commit()
        session.refresh(db_quote)
        return db_quote
    except HTTPException:
        session.rollback()
        raise


@router.get("/", response_model=List[QuoteRead])
def read_quotes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    search: str = None,
    estado: str = None,
    current_user: User = Depends(get_current_active_operativo_or_admin),
):
    query = select(Quote).options(selectinload(Quote.cliente)).order_by(Quote.id.desc())
    if estado:
        query = query.where(Quote.estado == estado)
        
    if search:
        # Si es número, buscar por ID
        if search.isdigit():
            query = query.where(Quote.id == int(search))
        # Si empieza con C y tiene dígitos, buscar por folio
        elif search.upper().startswith('C') and any(c.isdigit() for c in search):
            query = query.where(Quote.folio_cotizacion.contains(search.upper()))
        else:
            # Buscar por nombre de cliente
            query = query.join(Customer).where(Customer.nombre.contains(search))

    quotes = session.exec(query.offset(offset).limit(limit)).all()
    return quotes


@router.get("/by-customer/{customer_id}", response_model=List[QuoteRead])
def read_quotes_by_customer(
    *,
    session: Session = Depends(get_session),
    customer_id: int,
    estado: str = None,
    current_user: User = Depends(get_current_user),
):
    """Obtiene todas las cotizaciones de un cliente específico.
    El cliente solo puede ver las propias; Admin y Operativo pueden ver cualquiera.
    """
    if current_user.role == RoleEnum.Cliente:
        if current_user.cliente_id != customer_id:
            raise HTTPException(status_code=403, detail="Solo puedes ver tus propias cotizaciones")

    query = (
        select(Quote)
        .where(Quote.cliente_id == customer_id)
        .options(selectinload(Quote.cliente), selectinload(Quote.items))
        .order_by(Quote.fecha_creacion.desc())
    )
    if estado:
        query = query.where(Quote.estado == estado)

    quotes = session.exec(query).all()
    return quotes


@router.get("/{quote_id}", response_model=QuoteRead)
def read_quote(
    *,
    session: Session = Depends(get_session),
    quote_id: int,
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    # Usamos selectinload para traer los items y el producto
    query = select(Quote).where(Quote.id == quote_id).options(selectinload(Quote.items), selectinload(Quote.cliente))
    quote = session.exec(query).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")
    return quote


@router.patch("/{quote_id}", response_model=Quote)
def update_quote(
    *, session: Session = Depends(get_session), quote_id: int, quote_in: QuoteUpdate,
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    db_quote = session.get(Quote, quote_id)
    if not db_quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    # Guardar estado anterior para detectar cambios
    old_estado = db_quote.estado

    quote_data = quote_in.model_dump(exclude_unset=True)
    for key, value in quote_data.items():
        setattr(db_quote, key, value)

    # Si cambió a "Aprobada", actualizar stock de productos
    if old_estado != QuoteEstado.Aprobada.value and db_quote.estado == QuoteEstado.Aprobada.value:
        # Cargar items de la cotización
        from sqlalchemy.orm import selectinload
        quote_with_items = session.exec(
            select(Quote).where(Quote.id == quote_id).options(selectinload(Quote.items))
        ).first()
        
        if quote_with_items:
            for item in quote_with_items.items:
                producto = session.get(Product, item.producto_id)
                if producto:
                    es_servicio = (producto.categoria or "").strip().lower() == "servicio"
                    if not es_servicio:
                        # Validar que haya suficiente stock antes de descontar
                        if producto.stock < item.cantidad:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Producto '{producto.nombre}' no tiene suficiente stock para aceptar la cotización. Disponible: {producto.stock}, Solicitado: {item.cantidad}"
                            )
                        # Descontar stock
                        producto.stock -= item.cantidad
                        session.add(producto)
                    
    # Si cambió de "Aprobada" a cualquier otro estado (Cancelada, Rechazada, Borrador), devolver stock
    elif old_estado == QuoteEstado.Aprobada.value and db_quote.estado != QuoteEstado.Aprobada.value:
        from sqlalchemy.orm import selectinload
        quote_with_items = session.exec(
            select(Quote).where(Quote.id == quote_id).options(selectinload(Quote.items))
        ).first()
        
        if quote_with_items:
            for item in quote_with_items.items:
                producto = session.get(Product, item.producto_id)
                if producto:
                    es_servicio = (producto.categoria or "").strip().lower() == "servicio"
                    if not es_servicio:
                        # Devolver stock solo para Productos
                        producto.stock += item.cantidad
                        session.add(producto)

    session.add(db_quote)
    session.commit()
    session.refresh(db_quote)
    return db_quote


@router.get("/{quote_id}/pdf")
def generate_quote_pdf(
    *,
    session: Session = Depends(get_session),
    quote_id: int,
    mostrar_precios: bool = Query(default=True, description="Si es False, oculta la columna de Precio Unitario en el PDF"),
    current_user: User = Depends(get_current_user)
):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    if current_user.role == RoleEnum.Cliente:
        if current_user.cliente_id != quote.cliente_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para descargar esta cotización")

    try:
        # Renderizar HTML con datos reales
        html_content = templates.get_template("pdf/quote.html").render(quote=quote, mostrar_precios=mostrar_precios)

        import unicodedata, re
        def _safe(t, n=20):
            s = unicodedata.normalize('NFKD', t or '').encode('ascii','ignore').decode()
            return re.sub(r'_+','_', re.sub(r'[^\w]','_', s)).strip('_')[:n]

        folio = quote.folio_cotizacion or f"COT{quote_id:04d}"
        cliente_nombre = quote.cliente.nombre if quote.cliente else "Cliente"
        pdf_title = f"Cotización {folio} - CLI{quote.cliente_id:04d}_{cliente_nombre}"
        filename_utf8 = f"Cotización {folio} CLI{quote.cliente_id:04d}_{cliente_nombre}.pdf"
        filename_ascii = f"Cotizacion_{folio}_CLI{quote.cliente_id:04d}_{_safe(cliente_nombre)}.pdf"

        bg_file_path = BASE_DIR / "FORMATO COTIZACIÓN.pdf"
        pdf_bytes = generate_pdf_bytes(
            html_content,
            bg_pdf_path=str(bg_file_path) if bg_file_path.exists() else None,
            title=pdf_title
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename_ascii}"; filename*=UTF-8\'\'{quote_url(filename_utf8)}',
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            },
        )
    except Exception as e:
        logger.error("Error generando PDF de cotización: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno generando el PDF")

@router.get("/public/{quote_id}/pdf")
def generate_quote_pdf_public(
    *,
    session: Session = Depends(get_session),
    quote_id: int,
    mostrar_precios: bool = Query(default=True, description="Si es False, oculta la columna de Precio Unitario en el PDF")
):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    try:
        # Renderizar HTML con datos reales
        html_content = templates.get_template("pdf/quote.html").render(quote=quote, mostrar_precios=mostrar_precios)

        import unicodedata, re
        def _safe(t, n=20):
            s = unicodedata.normalize('NFKD', t or '').encode('ascii','ignore').decode()
            return re.sub(r'_+','_', re.sub(r'[^\w]','_', s)).strip('_')[:n]

        folio = quote.folio_cotizacion or f"COT{quote_id:04d}"
        cliente_nombre = quote.cliente.nombre if quote.cliente else "Cliente"
        pdf_title = f"Cotización {folio} - CLI{quote.cliente_id:04d}_{cliente_nombre}"
        filename_utf8 = f"Cotización {folio} CLI{quote.cliente_id:04d}_{cliente_nombre}.pdf"
        filename_ascii = f"Cotizacion_{folio}_CLI{quote.cliente_id:04d}_{_safe(cliente_nombre)}.pdf"

        bg_file_path = BASE_DIR / "FORMATO COTIZACIÓN.pdf"
        pdf_bytes = generate_pdf_bytes(
            html_content,
            bg_pdf_path=str(bg_file_path) if bg_file_path.exists() else None,
            title=pdf_title
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename_ascii}"; filename*=UTF-8\'\'{quote_url(filename_utf8)}',
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            },
        )
    except Exception as e:
        logger.error("Error generando PDF público de cotización: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno generando el PDF")

from pydantic import BaseModel
class ClientStatusUpdate(BaseModel):
    estado: str
    notas: Optional[str] = None

@router.patch("/{quote_id}/client-status")
def client_update_quote_status(
    *,
    session: Session = Depends(get_session),
    quote_id: int,
    payload: ClientStatusUpdate,
    current_user: User = Depends(get_current_user)
):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    if current_user.role == RoleEnum.Cliente:
        if current_user.cliente_id != quote.cliente_id:
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta cotización")

    if quote.estado != QuoteEstado.Enviada.value:
        raise HTTPException(status_code=400, detail="Solo puedes responder a cotizaciones enviadas")

    if payload.estado not in [QuoteEstado.Aprobacion_Solicitada.value, QuoteEstado.Rechazada.value]:
        raise HTTPException(status_code=400, detail="Estado de respuesta no permitido")

    quote.estado = payload.estado
    if payload.notas:
        existing_notes = quote.notas or ""
        quote.notas = f"{existing_notes}\n[Comentario del Cliente {now_local().strftime('%d/%m/%Y')}]: {payload.notas}".strip()

    session.add(quote)
    session.commit()
    session.refresh(quote)
    return {"message": "Respuesta enviada con éxito", "estado": quote.estado}

@router.post("/{quote_id}/send-email")
def send_quote_email(
    *,
    session: Session = Depends(get_session),
    quote_id: int,
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    quote = session.get(Quote, quote_id)
    if not quote or not quote.cliente:
        raise HTTPException(status_code=404, detail="Cotización o cliente no encontrado")

    if not quote.cliente.email:
        raise HTTPException(status_code=400, detail="El cliente no tiene un correo electrónico registrado")

    try:
        # 1. Generar el PDF
        html_content = templates.get_template("pdf/quote.html").render(quote=quote)
        pdf_bytes = generate_pdf_bytes(html_content)
        folio = quote.folio_cotizacion or f"COT{quote_id:04d}"
        pdf_name = f"Cotizacion_{folio}.pdf"

        # 2. Preparar el correo
        import smtplib
        from email.message import EmailMessage
        import os

        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
            # Simular envío
            print(f"--- SIMULACIÓN DE ENVÍO DE CORREO ---")
            print(f"Para: {quote.cliente.email}")
            print(f"Asunto: Tu Cotización {folio} - Cotizador Pro")
            print(f"Adjunto: {pdf_name} ({len(pdf_bytes)} bytes)")
            print(f"-------------------------------------")
            return {"message": "Correo simulado con éxito (Faltan credenciales SMTP reales en .env)"}

        msg = EmailMessage()
        msg['Subject'] = f"Tu Cotización {folio} - Cotizador Pro"
        msg['From'] = smtp_user
        msg['To'] = quote.cliente.email

        msg.set_content(f"""Hola {quote.cliente.nombre},

Adjunto encontrarás la cotización solicitada ({folio}).

Total: ${money(quote.total):,.2f}

Si tienes alguna duda, responde a este correo.

Saludos,
El equipo de Cotizador Pro""")

        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=pdf_name)

        with smtplib.SMTP_SSL(smtp_server, int(smtp_port)) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        # Si se quiere, actualizar el estado a "Enviada" si estaba en Borrador
        if quote.estado == QuoteEstado.Borrador.value:
            quote.estado = QuoteEstado.Enviada.value
            session.add(quote)
            session.commit()

        return {"message": "Correo enviado con éxito"}

    except Exception as e:
        logger.error("Error enviando correo de cotización: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno enviando el correo")

@router.post("/{quote_id}/report", response_model=QuoteRead)
async def upload_operative_report(
    *,
    session: Session = Depends(get_session),
    quote_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    db_quote = session.get(Quote, quote_id)
    if not db_quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports_dir = str(REPORTS_DIR)

    import unicodedata, re

    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".xls", ".xlsx"}

    # Sanitizar: quitar rutas, normalizar nombre y validar extensión
    raw_name = os.path.basename(file.filename or "")
    base, ext = os.path.splitext(raw_name)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Extensión no permitida. Permitidas: {', '.join(sorted(allowed_extensions))}")

    nfkd = unicodedata.normalize("NFKD", base)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", ascii_name).strip("_")
    safe_name = re.sub(r"_+", "_", safe_name) or "reporte"
    safe_filename = f"{safe_name}{ext.lower()}"

    file_path = os.path.join(reports_dir, f"quote_{quote_id}_{safe_filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_quote.reporte_operativo_path = f"/static/reports/quote_{quote_id}_{safe_filename}"
    session.add(db_quote)
    session.commit()
    session.refresh(db_quote)
    return db_quote


@router.post("/{quote_id}/report2", response_model=QuoteRead)
async def upload_operative_report_2(
    *,
    session: Session = Depends(get_session),
    quote_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    """Sube el segundo PDF de reporte operativo (documento complementario)."""
    db_quote = session.get(Quote, quote_id)
    if not db_quote:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    import unicodedata, re

    allowed_extensions = {".pdf"}

    raw_name = os.path.basename(file.filename or "")
    base, ext = os.path.splitext(raw_name)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF para este campo.")

    nfkd = unicodedata.normalize("NFKD", base)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", ascii_name).strip("_")
    safe_name = re.sub(r"_+", "_", safe_name) or "reporte2"
    safe_filename = f"{safe_name}{ext.lower()}"

    file_path = os.path.join(str(REPORTS_DIR), f"quote_{quote_id}_doc2_{safe_filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_quote.reporte_operativo_path_2 = f"/static/reports/quote_{quote_id}_doc2_{safe_filename}"
    session.add(db_quote)
    session.commit()
    session.refresh(db_quote)
    return db_quote
