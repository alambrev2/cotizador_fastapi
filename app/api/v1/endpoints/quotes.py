import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.database import get_session
from app.models import Quote, QuoteItem, Product, Customer, User
from app.schemas import QuoteCreate, QuoteRead, QuoteUpdate
from app.core.pdf import generate_pdf_bytes
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import datetime
from app.api.deps import (
    get_current_user,
    get_current_active_admin,
    get_current_active_operativo_or_admin,
    require_role,
)
from app.models import RoleEnum

# Obtener el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

router = APIRouter()

def get_next_quote_folio(session: Session) -> str:
    current_year = datetime.now().year
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

    # 2. Crear objeto Cotización vacio
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
        version=1
    )

    # Lógica de Mutación / Versión
    if quote_in.padre_id:
        madre = session.get(Quote, quote_in.padre_id)
        if madre:
            madre.estado = "Sustituida"
            session.add(madre)
            db_quote.version = madre.version + 1
            # Si la madre NO tenia folio por se antigua formamos la base
            if madre.folio_cotizacion:
                folio_base = madre.folio_cotizacion.split('-V')[0]
            else:
                folio_base = f"C{madre.fecha_creacion.year}{(madre.id or 0):04d}"
            db_quote.folio_cotizacion = f"{folio_base}-V{db_quote.version}"
        else:
            raise HTTPException(status_code=400, detail="Cotización padre no existe")

    session.add(db_quote)
    session.commit()
    session.refresh(db_quote)  # Obtener ID nuevo
    
    # Si es nueva 100%, asignamos su folio usando el año actual y su ID recién creado
    if not quote_in.padre_id:
        db_quote.folio_cotizacion = get_next_quote_folio(session)
        session.add(db_quote)
        session.commit()
        session.refresh(db_quote)

    total_cotizacion = 0.0
    utilidad_acumulada = 0.0

    # 3. Procesar items
    for item_in in quote_in.items:
        producto = session.get(Product, item_in.producto_id)
        if not producto:
            raise HTTPException(
                status_code=404, detail=f"Producto {item_in.producto_id} no encontrado"
            )

        # Validar stock disponible
        if producto.stock < item_in.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Producto '{producto.nombre}' no tiene suficiente stock. Disponible: {producto.stock}, Solicitado: {item_in.cantidad}"
            )

        # Usamos el precio unitario pactado manualmente desde el frontend
        precio_aplicado = Decimal(str(item_in.precio_unitario))

        subtotal = precio_aplicado * item_in.cantidad
        total_cotizacion += float(subtotal)
        
        # Lógica de Utilidad basada en costo real actual
        utilidad_item = (precio_aplicado - producto.costo) * item_in.cantidad
        utilidad_acumulada += float(utilidad_item)

        db_item = QuoteItem(
            cotizacion_id=db_quote.id,
            producto_id=producto.id,
            cantidad=item_in.cantidad,
            precio_unitario=precio_aplicado,
        )
        session.add(db_item)

    # 4. Actualizar total y utilidades de la cotización
    if quote_in.total_manual is not None and quote_in.total_manual > 0:
        db_quote.total = Decimal(str(quote_in.total_manual))
        if quote_in.requiere_factura:
            db_quote.subtotal = db_quote.total / Decimal('1.16')
            db_quote.iva = db_quote.total - db_quote.subtotal
        else:
            db_quote.subtotal = db_quote.total
            db_quote.iva = Decimal('0')
            
        # Recalcular utilidad: Subtotal - Costo Total de los productos
        costo_total = sum((item.cantidad * session.get(Product, item.producto_id).costo) for item in quote_in.items)
        db_quote.utilidad_total = db_quote.subtotal - costo_total
    else:
        db_quote.subtotal = Decimal(str(total_cotizacion))
        db_quote.iva = db_quote.subtotal * Decimal('0.16') if quote_in.requiere_factura else Decimal('0')
        db_quote.total = db_quote.subtotal + db_quote.iva
        db_quote.utilidad_total = Decimal(str(utilidad_acumulada))
    
    # Validar que el anticipo no exceda el total
    if quote_in.anticipo and quote_in.anticipo > db_quote.total:
        raise HTTPException(
            status_code=400, 
            detail=f"El anticipo (${quote_in.anticipo}) no puede ser mayor que el total (${db_quote.total})"
        )
    
    # Validar que el monto semanal esté en rango razonable si es financiamiento semanal
    if quote_in.tipo_pago == "Semanal" and quote_in.monto_semanal:
        min_weekly = 600
        max_weekly = 800
        if quote_in.monto_semanal < min_weekly or quote_in.monto_semanal > max_weekly:
            raise HTTPException(
                status_code=400,
                detail=f"El monto semanal (${quote_in.monto_semanal}) debe estar entre ${min_weekly} y ${max_weekly} para ser viable"
            )
    
    session.add(db_quote)
    session.commit()
    session.refresh(db_quote)

    return db_quote


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
        # Si es numero, buscar por ID, sino buscar por nombre de cliente
        if search.isdigit():
            query = query.where(Quote.id == int(search))
        else:
            # Join implicito o explicito para filtrar por cliente
            query = query.join(Customer).where(Customer.nombre.contains(search))

    quotes = session.exec(query.offset(offset).limit(limit)).all()
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

    # Si cambió a "Aceptada", actualizar stock de productos
    if old_estado != "Aceptada" and db_quote.estado == "Aceptada":
        # Cargar items de la cotización
        from sqlalchemy.orm import selectinload
        quote_with_items = session.exec(
            select(Quote).where(Quote.id == quote_id).options(selectinload(Quote.items))
        ).first()
        
        if quote_with_items:
            for item in quote_with_items.items:
                producto = session.get(Product, item.producto_id)
                if producto:
                    # Validar que haya suficiente stock antes de descontar
                    if producto.stock < item.cantidad:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Producto '{producto.nombre}' no tiene suficiente stock para aceptar la cotización. Disponible: {producto.stock}, Solicitado: {item.cantidad}"
                        )
                    # Descontar stock
                    producto.stock -= item.cantidad
                    session.add(producto)
                    
    # Si cambió de "Aceptada" a cualquier otro estado (Cancelada, Rechazada, Borrador), devolver stock
    elif old_estado == "Aceptada" and db_quote.estado != "Aceptada":
        from sqlalchemy.orm import selectinload
        quote_with_items = session.exec(
            select(Quote).where(Quote.id == quote_id).options(selectinload(Quote.items))
        ).first()
        
        if quote_with_items:
            for item in quote_with_items.items:
                producto = session.get(Product, item.producto_id)
                if producto:
                    # Devolver stock
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
        html_content = templates.get_template("pdf/quote.html").render(quote=quote)

        # Generar bytes PDF
        pdf_bytes = generate_pdf_bytes(html_content)

        # Nomenclatura: Cotizacion_FOLIO_CLI0001_nombre.pdf
        import unicodedata, re
        def _safe(t, n=20):
            s = unicodedata.normalize('NFKD', t or '').encode('ascii','ignore').decode()
            return re.sub(r'_+','_', re.sub(r'[^\w]','_', s)).strip('_')[:n]
        folio = quote.folio_cotizacion or f"COT{quote_id:04d}"
        nombre = _safe(quote.cliente.nombre) if quote.cliente else "cliente"
        pdf_name = f"Cotizacion_{folio}_CLI{quote.cliente_id:04d}_{nombre}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{pdf_name}"'},
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")

@router.get("/public/{quote_id}/pdf")
def generate_quote_pdf_public(
    *,
    session: Session = Depends(get_session),
    quote_id: int
):
    quote = session.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    try:
        # Renderizar HTML con datos reales
        html_content = templates.get_template("pdf/quote.html").render(quote=quote)

        # Generar bytes PDF
        pdf_bytes = generate_pdf_bytes(html_content)

        # Nomenclatura: Cotizacion_FOLIO_CLI0001_nombre.pdf
        import unicodedata, re
        def _safe(t, n=20):
            s = unicodedata.normalize('NFKD', t or '').encode('ascii','ignore').decode()
            return re.sub(r'_+','_', re.sub(r'[^\w]','_', s)).strip('_')[:n]
        folio = quote.folio_cotizacion or f"COT{quote_id:04d}"
        nombre = _safe(quote.cliente.nombre) if quote.cliente else "cliente"
        pdf_name = f"Cotizacion_{folio}_CLI{quote.cliente_id:04d}_{nombre}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{pdf_name}"'},
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")

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

    if quote.estado != "Enviada":
        raise HTTPException(status_code=400, detail="Solo puedes responder a cotizaciones enviadas")

    if payload.estado not in ["Aprobación Solicitada", "Rechazada"]:
        raise HTTPException(status_code=400, detail="Estado de respuesta no permitido")

    quote.estado = payload.estado
    if payload.notas:
        existing_notes = quote.notas or ""
        quote.notas = f"{existing_notes}\n[Comentario del Cliente {datetime.now().strftime('%d/%m/%Y')}]: {payload.notas}".strip()

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

Total: ${float(quote.total):,.2f}

Si tienes alguna duda, responde a este correo.

Saludos,
El equipo de Cotizador Pro""")

        msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename=pdf_name)

        with smtplib.SMTP_SSL(smtp_server, int(smtp_port)) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        # Si se quiere, actualizar el estado a "Enviada" si estaba en Borrador
        if quote.estado == "Borrador":
            quote.estado = "Enviada"
            session.add(quote)
            session.commit()

        return {"message": "Correo enviado con éxito"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error enviando correo: {str(e)}")

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

    reports_dir = os.path.join(BASE_DIR, "app", "static", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    # Reemplazar espacios y sanitizar un poco
    safe_filename = file.filename.replace(" ", "_")
    file_path = os.path.join(reports_dir, f"quote_{quote_id}_{safe_filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_quote.reporte_operativo_path = f"/static/reports/quote_{quote_id}_{safe_filename}"
    session.add(db_quote)
    session.commit()
    session.refresh(db_quote)
    return db_quote
