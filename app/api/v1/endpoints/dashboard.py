from fastapi import APIRouter, Depends, Response
from sqlmodel import Session, select
from app.database import get_session
from app.models import Payment, Quote, Expense
from datetime import datetime
import datetime as dt
from calendar import monthrange
from fastapi.templating import Jinja2Templates
from app.core.pdf import generate_pdf_bytes

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

@router.get("/export/ingresos")
def export_ingresos_pdf(mes: int, anio: int, session: Session = Depends(get_session)):
    first_day = dt.date(anio, mes, 1)
    last_day = dt.date(anio, mes, monthrange(anio, mes)[1])
    
    pagos = session.exec(select(Payment).where(Payment.fecha_pago >= first_day, Payment.fecha_pago <= last_day)).all()
    
    filas = []
    total = 0.0
    for p in pagos:
        desc = p.metodo_pago or "Pago"
        monto = float(p.monto)
        total += monto
        fecha = p.fecha_pago.strftime("%d/%m/%Y")
        origen = "Cobro Cliente" + (" (Abono)" if not p.quote_id else " (Cotización)")
        filas.append([fecha, origen, desc, f"${monto:,.2f}"])
        
    html_content = templates.get_template("pdf/financial_report.html").render(
        tipo_reporte="INGRESOS",
        mes=f"{mes:02d}",
        anio=anio,
        fecha_emision=datetime.now().strftime("%d/%m/%Y"),
        columnas=["Fecha", "Origen/Descripción", "Tipo", "Monto"],
        filas=filas,
        total=f"${total:,.2f}"
    )
    
    pdf_bytes = generate_pdf_bytes(html_content)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Ingresos_{mes}_{anio}.pdf"})

@router.get("/export/egresos")
def export_egresos_pdf(mes: int, anio: int, session: Session = Depends(get_session)):
    first_day = dt.date(anio, mes, 1)
    last_day = dt.date(anio, mes, monthrange(anio, mes)[1])
    
    egresos = session.exec(select(Expense).where(Expense.fecha >= first_day, Expense.fecha <= last_day)).all()
    
    filas = []
    total = 0.0
    for e in egresos:
        monto = float(e.monto)
        total += monto
        fecha = e.fecha.strftime("%d/%m/%Y")
        desc = e.descripcion[:30]
        cat = e.categoria or "General"
        filas.append([fecha, desc, cat, f"-${monto:,.2f}"])
        
    html_content = templates.get_template("pdf/financial_report.html").render(
        tipo_reporte="EGRESOS",
        mes=f"{mes:02d}",
        anio=anio,
        fecha_emision=datetime.now().strftime("%d/%m/%Y"),
        columnas=["Fecha", "Descripción del Servicio", "Categoría", "Monto"],
        filas=filas,
        total=f"-${total:,.2f}"
    )
    
    pdf_bytes = generate_pdf_bytes(html_content)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Egresos_{mes}_{anio}.pdf"})

@router.get("/summary")
def get_dashboard_summary(*, session: Session = Depends(get_session), response: Response):
    # Disable caching globally for this endpoint
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    now = datetime.now()
    first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_of_month = monthrange(now.year, now.month)[1]
    last_day = now.replace(day=last_day_of_month, hour=23, minute=59, second=59, microsecond=999999)

    # 1. Saldo por Cobrar
    # Usar la misma función de cálculo que ocupa la Finanzas "Cuentas Pendientes" globalmente para que cruce $1 a $1
    from app.api.v1.endpoints.payments import read_active_customers
    active_accounts = read_active_customers(session=session)
    
    saldo_por_cobrar = sum([float(a["saldo_global"]) for a in active_accounts])

    # 2. Cotizaciones en Borrador
    # Conteo de quotes cuyo estado sea 'Borrador'
    borradores_query = (
        select(Quote)
        .where(Quote.estado == "Borrador")
    )
    borradores_count = len(session.exec(borradores_query).all())

    # 3. Resumen Financiero (Mes actual)
    # Ingresos (Suma de pagos)
    pagos_query = select(Payment).where(Payment.fecha_pago >= first_day, Payment.fecha_pago <= last_day)
    pagos = session.exec(pagos_query).all()
    ingresos_mes = sum([float(p.monto) for p in pagos])

    # Egresos (Expense table used to register 'Pago de Renta, Luz', etc.)
    from app.models import Expense, ScheduledExpense
    egresos_query = select(Expense).where(
        Expense.fecha >= first_day, 
        Expense.fecha <= last_day
    )
    egresos = session.exec(egresos_query).all()
    egresos_mes = sum([float(g.monto) for g in egresos if g.monto])
    
    saldo_neto = ingresos_mes - egresos_mes

    # Egresos Programados Pendientes (Calendario)
    scheduled_query = select(ScheduledExpense).where(ScheduledExpense.estatus == 'Pendiente')
    scheduled_expenses = session.exec(scheduled_query).all()
    total_scheduled = sum([float(s.monto) for s in scheduled_expenses])
    
    # Flujo de Caja Real: Ingresos Totales Confirmados - Egresos Ejecutados
    all_payments = session.exec(select(Payment)).all()
    unique_payments = {p.id: p for p in all_payments}.values()
    ingresos_totales_confirmados = sum([float(p.monto) for p in unique_payments if p.monto])

    all_expenses = session.exec(select(Expense)).all()
    unique_expenses = {e.id: e for e in all_expenses}.values()
    egresos_ejecutados = sum([float(e.monto) for e in unique_expenses if e.monto])

    flujo_caja_real = ingresos_totales_confirmados - egresos_ejecutados

    import datetime as dt
    hoy = dt.date.today()
    limite_5_dias = hoy + dt.timedelta(days=5)
    alertas_proximas = [
        {
            "id": s.id,
            "descripcion": s.descripcion,
            "fecha_vencimiento": str(s.fecha_vencimiento),
            "monto": float(s.monto),
            "recibido_en": datetime.combine(s.fecha_vencimiento, datetime.min.time()).isoformat()
        }
        for s in scheduled_expenses if hoy <= s.fecha_vencimiento <= limite_5_dias
    ]

    from app.models import Customer
    # Alertas de Cotizaciones (Aprobación Solicitada o Rechazada)
    quotes_query = select(Quote).where(Quote.estado.in_(["Aprobación Solicitada", "Rechazada"]))
    quotes_alertas = session.exec(quotes_query).all()
    
    alertas_cotizaciones = []
    for q in quotes_alertas:
        cliente_nombre = "Cliente"
        if q.cliente_id:
            cliente_obj = session.get(Customer, q.cliente_id)
            if cliente_obj:
                cliente_nombre = cliente_obj.nombre
        alertas_cotizaciones.append({
            "id": q.id,
            "folio_cotizacion": q.folio_cotizacion or f"#{q.id}",
            "cliente_nombre": cliente_nombre,
            "estado": q.estado,
            "total": float(q.total),
            "notas": q.notas,
            "recibido_en": q.fecha_creacion.isoformat() if q.fecha_creacion else now.isoformat()
        })

    # Alertas de Reportes Operativos Subidos (Operador cargó PDF del proyecto en curso)
    reportes_query = select(Quote).where(
        Quote.estado == "Aprobada",
        Quote.reporte_operativo_path.isnot(None),
        Quote.reporte_operativo_path != ""
    )
    reportes_activos = session.exec(reportes_query).all()
    
    alertas_reportes = []
    for q in reportes_activos:
        cliente_nombre = "Cliente"
        if q.cliente_id:
            cliente_obj = session.get(Customer, q.cliente_id)
            if cliente_obj:
                cliente_nombre = cliente_obj.nombre
        alertas_reportes.append({
            "id": q.id,
            "folio_cotizacion": q.folio_cotizacion or f"#{q.id}",
            "cliente_nombre": cliente_nombre,
            "reporte_path": q.reporte_operativo_path,
            "recibido_en": now.isoformat()
        })

    return {
        "saldo_por_cobrar": round(saldo_por_cobrar, 2),
        "flujo_caja_real": round(flujo_caja_real, 2),
        "cotizaciones_borrador": borradores_count,
        "financiero": {
            "ingresos": round(ingresos_mes, 2),
            "egresos": round(egresos_mes, 2),
            "saldo_neto": round(saldo_neto, 2)
        },
        "scheduled_expenses": scheduled_expenses,
        "alertas_proximas": alertas_proximas,
        "alertas_cotizaciones": alertas_cotizaciones,
        "alertas_reportes": alertas_reportes
    }

@router.get("/analytics")
def get_dashboard_analytics(*, session: Session = Depends(get_session), response: Response):
    # Disable caching
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    from app.models import Product, AccountCharge, Customer
    from sqlalchemy import func
    import datetime as dt
    
    # 1. Métricas de Conversión (Embudo de cotizaciones)
    quotes = session.exec(select(Quote.estado, func.count(Quote.id)).group_by(Quote.estado)).all()
    conversion_metrics = {estado: count for estado, count in quotes}
    
    # 2. Alertas de Inventario Bajo
    # Asegurarse de que el stock_minimo sea respetado
    low_stock_products = session.exec(select(Product).where(Product.stock <= Product.stock_minimo, Product.activo == True)).all()
    alertas_stock = [
        {"id": p.id, "nombre": p.nombre, "stock": p.stock, "stock_minimo": p.stock_minimo}
        for p in low_stock_products
    ]

    # 3. Alertas de Cobranza (>30 días)
    limite_cobranza = dt.datetime.utcnow() - dt.timedelta(days=30)
    cargos_atrasados = session.exec(
        select(AccountCharge)
        .where(AccountCharge.estatus == "Pendiente")
        .where(AccountCharge.fecha < limite_cobranza)
    ).all()

    alertas_cobranza = []
    for cargo in cargos_atrasados:
        dias_retraso = (dt.datetime.utcnow() - cargo.fecha).days
        cliente = session.get(Customer, cargo.cliente_id)
        if cliente:
            alertas_cobranza.append({
                "cliente": cliente.nombre,
                "detalle": cargo.detalle,
                "monto": float(cargo.monto),
                "dias_retraso": dias_retraso,
                "recibido_en": cargo.fecha.isoformat()
            })
    
    now_ts = dt.datetime.utcnow().isoformat()
    alertas_stock_ts = [
        {"id": p.id, "nombre": p.nombre, "stock": p.stock, "stock_minimo": p.stock_minimo, "recibido_en": now_ts}
        for p in low_stock_products
    ]
    
    return {
        "conversion_metrics": conversion_metrics,
        "alertas_stock": alertas_stock_ts,
        "alertas_cobranza": alertas_cobranza
    }

@router.get("/pnl")
def get_pnl(anio: int = None, session: Session = Depends(get_session)):
    if not anio:
        anio = datetime.now().year
    
    # We want to return data for each month (1 to 12)
    meses = []
    
    from app.models import OtherIncome
    
    for mes in range(1, 13):
        first_day = dt.date(anio, mes, 1)
        last_day = dt.date(anio, mes, monthrange(anio, mes)[1])
        
        # Ingresos: Suma de pagos + Incomes extras
        pagos = session.exec(select(Payment).where(Payment.fecha_pago >= first_day, Payment.fecha_pago <= last_day)).all()
        ingresos_pagos = sum([float(p.monto) for p in pagos])
        
        incomes = session.exec(select(OtherIncome).where(OtherIncome.fecha >= first_day, OtherIncome.fecha <= last_day)).all()
        ingresos_extras = sum([float(i.monto) for i in incomes])
        
        total_ingresos = ingresos_pagos + ingresos_extras
        
        # Egresos: 
        egresos = session.exec(select(Expense).where(Expense.fecha >= first_day, Expense.fecha <= last_day)).all()
        
        # Clasificar egresos
        cat_materiales = ["materiales", "insumos", "proveedores", "compras", "equipo"]
        
        costos_materiales = sum([float(e.monto) for e in egresos if e.categoria and e.categoria.lower() in cat_materiales])
        egresos_operativos = sum([float(e.monto) for e in egresos if not e.categoria or e.categoria.lower() not in cat_materiales])
        
        meses.append({
            "mes": mes,
            "ingresos": total_ingresos,
            "costos_materiales": costos_materiales,
            "egresos_operativos": egresos_operativos,
            "utilidad_bruta": total_ingresos - costos_materiales,
            "utilidad_neta": total_ingresos - costos_materiales - egresos_operativos
        })
        
    return {"anio": anio, "pnl": meses}
