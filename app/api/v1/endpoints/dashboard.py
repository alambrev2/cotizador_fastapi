from fastapi import APIRouter, Depends, Response
from sqlmodel import Session, select
from app.database import get_session
from app.models import Payment, Quote, Expense
from datetime import datetime
import datetime as dt
from calendar import monthrange
from fpdf import FPDF

router = APIRouter()

@router.get("/export/ingresos")
def export_ingresos_pdf(mes: int, anio: int, session: Session = Depends(get_session)):
    first_day = dt.date(anio, mes, 1)
    last_day = dt.date(anio, mes, monthrange(anio, mes)[1])
    
    pagos = session.exec(select(Payment).where(Payment.fecha_pago >= first_day, Payment.fecha_pago <= last_day)).all()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=16, style='B')
    pdf.cell(0, 10, text=f"Historial de Ingresos - {mes}/{anio}", new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.cell(0, 10, text="", new_x='LMARGIN', new_y='NEXT')
    
    # Cabeceras
    pdf.set_font("helvetica", size=10, style='B')
    pdf.cell(40, 10, text="Fecha", border=1, align='C')
    pdf.cell(60, 10, text="Origen/Descripcion", border=1, align='C')
    pdf.cell(40, 10, text="Tipo", border=1, align='C')
    pdf.cell(40, 10, text="Monto ($)", border=1, new_x='LMARGIN', new_y='NEXT', align='C')
    
    pdf.set_font("helvetica", size=10)
    total = 0.0
    for p in pagos:
        desc = p.metodo_pago or "Pago"
        monto = float(p.monto)
        total += monto
        pdf.cell(40, 10, text=str(p.fecha_pago.date()), border=1)
        pdf.cell(60, 10, text="Cobro Cliente" + (f" (Abono)" if not p.quote_id else f" (Cotización)"), border=1)
        pdf.cell(40, 10, text=desc, border=1)
        pdf.cell(40, 10, text=f"${monto:,.2f}", border=1, new_x='LMARGIN', new_y='NEXT', align='R')
        
    pdf.set_font("helvetica", size=10, style='B')
    pdf.cell(140, 10, text="Total del Periodo:", border=1, align='R')
    pdf.cell(40, 10, text=f"${total:,.2f}", border=1, new_x='LMARGIN', new_y='NEXT', align='R')
    
    pdf_bytes = bytes(pdf.output())
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Ingresos_{mes}_{anio}.pdf"})

@router.get("/export/egresos")
def export_egresos_pdf(mes: int, anio: int, session: Session = Depends(get_session)):
    first_day = dt.date(anio, mes, 1)
    last_day = dt.date(anio, mes, monthrange(anio, mes)[1])
    
    egresos = session.exec(select(Expense).where(Expense.fecha >= first_day, Expense.fecha <= last_day)).all()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=16, style='B')
    pdf.cell(0, 10, text=f"Historial de Egresos - {mes}/{anio}", new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.cell(0, 10, text="", new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font("helvetica", size=10, style='B')
    pdf.cell(40, 10, text="Fecha", border=1, align='C')
    pdf.cell(60, 10, text="Descripción del Servicio", border=1, align='C')
    pdf.cell(40, 10, text="Categoría", border=1, align='C')
    pdf.cell(40, 10, text="Monto ($)", border=1, new_x='LMARGIN', new_y='NEXT', align='C')
    
    pdf.set_font("helvetica", size=10)
    total = 0.0
    for e in egresos:
        monto = float(e.monto)
        total += monto
        pdf.set_text_color(0, 0, 0) # Negro para info base
        pdf.cell(40, 10, text=str(e.fecha.date()), border=1)
        pdf.cell(60, 10, text=e.descripcion[:30], border=1)
        pdf.cell(40, 10, text=e.categoria or "General", border=1)
        
        pdf.set_text_color(220, 38, 38) # Rojo para monto
        pdf.cell(40, 10, text=f"-${monto:,.2f}", border=1, new_x='LMARGIN', new_y='NEXT', align='R')
        
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", size=10, style='B')
    pdf.cell(140, 10, text="Total del Periodo:", border=1, align='R')
    pdf.set_text_color(220, 38, 38)
    pdf.cell(40, 10, text=f"-${total:,.2f}", border=1, new_x='LMARGIN', new_y='NEXT', align='R')
    
    pdf_bytes = bytes(pdf.output())
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
    flujo_caja_real = saldo_por_cobrar - total_scheduled

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
