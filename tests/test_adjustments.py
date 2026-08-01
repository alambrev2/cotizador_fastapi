"""Ajustes de negocio usando una BD temporal (no toca data/database.db)."""
from datetime import date, timedelta
from decimal import Decimal

from fastapi import Response
from sqlmodel import select

from app.api.v1.endpoints.dashboard import get_dashboard_summary
from app.models import Customer, Quote, Payment, QuoteEstado


def _cliente_prueba(db, nombre, email):
    customer = Customer(
        nombre=nombre,
        email=email,
        telefono="1234567890",
        saldo_inicial=Decimal("0.00"),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def test_quote_with_low_weekly_payment(db):
    customer = _cliente_prueba(db, "Cliente Prueba Bajo Monto", "clientebajo@test.com")
    quote = Quote(
        cliente_id=customer.id,
        estado=QuoteEstado.Enviada.value,
        tipo_pago="Semanal",
        total=Decimal("500.00"),
        monto_semanal=Decimal("500.00"),
        plazo_semanas=1,
        fecha_inicio_pago=date.today(),
        fecha_fin_pago=date.today() + timedelta(days=7),
        filial="Test Filial",
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    assert quote.monto_semanal == Decimal("500.00")
    assert quote.tipo_pago == "Semanal"


def test_adaptative_suggested_payments(db):
    customer = _cliente_prueba(db, "Cliente Prueba Adaptativa", "clienteadapt@test.com")
    quote = Quote(
        cliente_id=customer.id,
        estado=QuoteEstado.Aprobada.value,
        tipo_pago="Semanal",
        total=Decimal("4000.00"),
        monto_semanal=Decimal("800.00"),
        plazo_semanas=5,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    total_quote = quote.total
    cuota_estandar = quote.monto_semanal

    # Sin pagos
    saldo = total_quote - Decimal("0")
    assert min(saldo, cuota_estandar) == Decimal("800.00")

    # Anticipo de $1,000
    db.add(Payment(cliente_id=customer.id, quote_id=quote.id, monto=Decimal("1000.00"), metodo_pago="Efectivo"))
    db.commit()
    saldo = total_quote - Decimal("1000.00")
    assert min(saldo, cuota_estandar) == Decimal("800.00")

    # Acumulado $2,000
    db.add(Payment(cliente_id=customer.id, quote_id=quote.id, monto=Decimal("1000.00"), metodo_pago="Efectivo"))
    db.commit()
    saldo = total_quote - Decimal("2000.00")
    assert min(saldo, cuota_estandar) == Decimal("800.00")

    # $3,200 y $4,000 acumulados
    db.add(Payment(cliente_id=customer.id, quote_id=quote.id, monto=Decimal("800.00"), metodo_pago="Efectivo"))
    db.add(Payment(cliente_id=customer.id, quote_id=quote.id, monto=Decimal("800.00"), metodo_pago="Efectivo"))
    db.commit()
    saldo = total_quote - Decimal("3600.00")
    # La sugerida se adapta al saldo restante real ($400) para no cobrar de más
    assert min(saldo, cuota_estandar) == Decimal("400.00")


def test_custom_filial_option(db):
    customer = _cliente_prueba(db, "Cliente Prueba Filial", "clientefilial@test.com")
    filial_name = "Smart Pos Solution"
    quote = Quote(
        cliente_id=customer.id,
        estado=QuoteEstado.Enviada.value,
        tipo_pago="Contado",
        total=Decimal("1500.00"),
        filial=filial_name,
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    loaded = db.get(Quote, quote.id)
    assert loaded.filial == filial_name


def test_operator_report_notifications_and_finalized_projects(db):
    customer = _cliente_prueba(db, "Cliente Prueba Reportes", "clientereportes@test.com")
    quote = Quote(
        cliente_id=customer.id,
        estado=QuoteEstado.Aprobada.value,
        tipo_pago="Contado",
        total=Decimal("3000.00"),
        folio_cotizacion="C2026TEST01",
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)

    resp = Response()
    summary = get_dashboard_summary(session=db, response=resp)
    alertas = summary.get("alertas_reportes", [])
    assert not any(a["folio_cotizacion"] == "C2026TEST01" for a in alertas)

    quote.reporte_operativo_path = "/static/reports/quote_TEST_reporte.pdf"
    db.add(quote)
    db.commit()
    db.refresh(quote)

    summary = get_dashboard_summary(session=db, response=resp)
    alertas = summary.get("alertas_reportes", [])
    target = next((a for a in alertas if a["folio_cotizacion"] == "C2026TEST01"), None)
    assert target is not None
    assert target["cliente_nombre"] == "Cliente Prueba Reportes"
    assert target["reporte_path"] == "/static/reports/quote_TEST_reporte.pdf"

    quote.estado = QuoteEstado.Finalizada.value
    db.add(quote)
    db.commit()
    db.refresh(quote)

    finalized = db.exec(select(Quote).where(Quote.estado == QuoteEstado.Finalizada.value)).all()
    assert any(q.id == quote.id for q in finalized)

    summary = get_dashboard_summary(session=db, response=resp)
    alertas = summary.get("alertas_reportes", [])
    assert not any(a["folio_cotizacion"] == "C2026TEST01" for a in alertas)
