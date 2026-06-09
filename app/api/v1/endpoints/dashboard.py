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
    alertas_proximas = [s for s in scheduled_expenses if hoy <= s.fecha_vencimiento <= limite_5_dias]

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
        "alertas_proximas": alertas_proximas
    }
