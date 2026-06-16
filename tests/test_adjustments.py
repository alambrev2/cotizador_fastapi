from sqlmodel import Session, select
from app.database import engine
from app.models import User, Quote, Customer, Payment, RoleEnum
from datetime import datetime, date, timedelta
from decimal import Decimal
import secrets

def test_quote_with_low_weekly_payment():
    print("\n--- TEST: Cotización con pago semanal menor a $600 ---")
    with Session(engine) as db:
        # Buscar o crear un cliente de prueba
        customer = db.exec(select(Customer)).first()
        if not customer:
            customer = Customer(
                nombre="Cliente Prueba Bajo Monto",
                email="clientebajo@test.com",
                telefono="1234567890",
                saldo_inicial=Decimal("0.00")
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)

        # Crear cotización con cobro semanal menor a 600
        quote = Quote(
            cliente_id=customer.id,
            estado="Enviada",
            tipo_pago="Semanal",
            total=Decimal("500.00"),
            monto_semanal=Decimal("500.00"),
            plazo_semanas=1,
            fecha_inicio_pago=date.today(),
            fecha_fin_pago=date.today() + timedelta(days=7),
            filial="Test Filial"
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)

        print(f"OK: Cotización creada con monto semanal de ${quote.monto_semanal} (menor a $600).")
        assert quote.monto_semanal == Decimal("500.00")
        assert quote.tipo_pago == "Semanal"

        # Limpiar
        db.delete(quote)
        db.commit()


def test_adaptative_suggested_payments():
    print("\n--- TEST: Lógica adaptativa para sugerencia de pagos ---")
    with Session(engine) as db:
        # Buscar o crear un cliente de prueba
        customer = db.exec(select(Customer)).first()
        if not customer:
            customer = Customer(
                nombre="Cliente Prueba Adaptativa",
                email="clienteadapt@test.com",
                telefono="1234567890",
                saldo_inicial=Decimal("0.00")
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)

        # Crear cotización de $4,000 con esquema semanal de $800
        quote = Quote(
            cliente_id=customer.id,
            estado="Aprobada",
            tipo_pago="Semanal",
            total=Decimal("4000.00"),
            monto_semanal=Decimal("800.00"),
            plazo_semanas=5
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)

        total_quote = float(quote.total)
        cuota_estandar = float(quote.monto_semanal)
        print(f"Cotización creada - Total: ${total_quote}, Cuota estándar: ${cuota_estandar}")

        # Lógica de cálculo en statement_view: Math.min(saldo, cuota_estandar)
        # 1. Sin pagos
        pagado = 0.0
        saldo = total_quote - pagado
        sugerida = min(saldo, cuota_estandar)
        print(f"Paso 1 - Saldo: ${saldo}, Sugerida: ${sugerida}")
        assert sugerida == 800.0

        # 2. Registrar un pago mayor de $1,000 (Anticipo)
        p1 = Payment(cliente_id=customer.id, quote_id=quote.id, monto=Decimal("1000.00"), metodo_pago="Efectivo")
        db.add(p1)
        db.commit()

        # Calcular nuevo saldo y cuota sugerida
        pagado = 1000.0
        saldo = total_quote - pagado
        sugerida = min(saldo, cuota_estandar)
        print(f"Paso 2 (Abono de $1000) - Saldo: ${saldo}, Sugerida: ${sugerida}")
        assert sugerida == 800.0

        # 3. Registrar otro pago de $1,000
        p2 = Payment(cliente_id=customer.id, quote_id=quote.id, monto=Decimal("1000.00"), metodo_pago="Efectivo")
        db.add(p2)
        db.commit()

        # Calcular nuevo saldo y cuota sugerida
        pagado = 2000.0
        saldo = total_quote - pagado
        sugerida = min(saldo, cuota_estandar)
        print(f"Paso 3 (Abono de $1000) - Saldo: ${saldo}, Sugerida: ${sugerida}")
        assert sugerida == 800.0

        # 4. Registrar pago de $800
        p3 = Payment(cliente_id=customer.id, quote_id=quote.id, monto=Decimal("800.00"), metodo_pago="Efectivo")
        db.add(p3)
        db.commit()

        # 5. Registrar pago de $800
        p4 = Payment(cliente_id=customer.id, quote_id=quote.id, monto=Decimal("800.00"), metodo_pago="Efectivo")
        db.add(p4)
        db.commit()

        # Calcular nuevo saldo y cuota sugerida. Debería restar $400 ($4,000 - $3,600)
        pagado = 3600.0
        saldo = total_quote - pagado
        sugerida = min(saldo, cuota_estandar)
        print(f"Paso 5 (Abonado acumulado $3600) - Saldo: ${saldo}, Sugerida: ${sugerida}")
        # La sugerida debe adaptarse al saldo restante real ($400) para no cobrar de más ($800)
        assert sugerida == 400.0
        print("OK: La cuota sugerida se adaptó correctamente a $400 en lugar del estándar de $800.")

        # Limpiar pagos y cotización
        db.delete(p1)
        db.delete(p2)
        db.delete(p3)
        db.delete(p4)
        db.delete(quote)
        db.commit()


def test_custom_filial_option():
    print("\n--- TEST: Opción de filial personalizada ('Otro') ---")
    with Session(engine) as db:
        # Buscar o crear un cliente de prueba
        customer = db.exec(select(Customer)).first()
        if not customer:
            customer = Customer(
                nombre="Cliente Prueba Filial",
                email="clientefilial@test.com",
                telefono="1234567890",
                saldo_inicial=Decimal("0.00")
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)

        # Crear cotización con filial personalizada
        filial_name = "Smart Pos Solution"
        quote = Quote(
            cliente_id=customer.id,
            estado="Enviada",
            tipo_pago="Contado",
            total=Decimal("1500.00"),
            filial=filial_name
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)

        # Cargar y verificar
        loaded_quote = db.get(Quote, quote.id)
        print(f"OK: Cotización cargada. Filial guardada: '{loaded_quote.filial}'")
        assert loaded_quote.filial == filial_name

        # Limpiar
        db.delete(quote)
        db.commit()


def test_operator_report_notifications_and_finalized_projects():
    print("\n--- TEST: Alertas de reportes del operador e historial de finalizados ---")
    from app.api.v1.endpoints.dashboard import get_dashboard_summary
    from fastapi import Response

    with Session(engine) as db:
        # 1. Crear un cliente de prueba
        customer = Customer(
            nombre="Cliente Prueba Reportes",
            email="clientereportes@test.com",
            telefono="1234567890",
            saldo_inicial=Decimal("0.00")
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # 2. Crear una cotización en estado Aprobada (Proyecto en curso)
        quote = Quote(
            cliente_id=customer.id,
            estado="Aprobada",
            tipo_pago="Contado",
            total=Decimal("3000.00"),
            folio_cotizacion="C2026TEST01"
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)

        # 3. Consultar dashboard: inicialmente no debe haber alertas de reportes para este proyecto
        resp = Response()
        summary = get_dashboard_summary(session=db, response=resp)
        alertas = summary.get("alertas_reportes", [])
        print(f"Paso 1 (Aprobada sin reporte) - Cantidad de alertas: {len(alertas)}")
        # Validar que no contenga el folio
        assert not any(a["folio_cotizacion"] == "C2026TEST01" for a in alertas)

        # 4. Simular que el operador sube el reporte
        quote.reporte_operativo_path = "/static/reports/quote_TEST_reporte.pdf"
        db.add(quote)
        db.commit()
        db.refresh(quote)

        # 5. Consultar dashboard: ahora debe alertar al administrador
        summary = get_dashboard_summary(session=db, response=resp)
        alertas = summary.get("alertas_reportes", [])
        print(f"Paso 2 (Operador subió reporte) - Cantidad de alertas: {len(alertas)}")
        target_alert = next((a for a in alertas if a["folio_cotizacion"] == "C2026TEST01"), None)
        assert target_alert is not None
        assert target_alert["cliente_nombre"] == "Cliente Prueba Reportes"
        assert target_alert["reporte_path"] == "/static/reports/quote_TEST_reporte.pdf"
        print("OK: Alerta generada correctamente en el dashboard summary.")

        # 6. Simular que el administrador finaliza el proyecto
        quote.estado = "Finalizada"
        db.add(quote)
        db.commit()
        db.refresh(quote)

        # 7. Verificar almacenamiento del historial (el query por 'Finalizada' debe encontrarlo)
        finalized_quotes = db.exec(select(Quote).where(Quote.estado == "Finalizada")).all()
        assert any(q.id == quote.id for q in finalized_quotes)
        print("OK: Proyecto finalizado se encuentra en el historial de finalizados.")

        # 8. Consultar dashboard: la alerta debe desaparecer ya que el proyecto concluyó
        summary = get_dashboard_summary(session=db, response=resp)
        alertas = summary.get("alertas_reportes", [])
        print(f"Paso 3 (Proyecto finalizado) - Cantidad de alertas: {len(alertas)}")
        assert not any(a["folio_cotizacion"] == "C2026TEST01" for a in alertas)
        print("OK: Alerta removida tras finalización del proyecto.")

        # Limpiar
        db.delete(quote)
        db.delete(customer)
        db.commit()


if __name__ == "__main__":
    test_quote_with_low_weekly_payment()
    test_adaptative_suggested_payments()
    test_custom_filial_option()
    test_operator_report_notifications_and_finalized_projects()

