from decimal import Decimal
from sqlmodel import Session, SQLModel, create_engine
from app.models import Customer, Quote
from app.api.v1.endpoints.payments import (
    read_active_statements,
    read_active_customers,
    get_customer_statement,
)

# Set up test database in memory
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

def test_saldo_por_cobrar_estados():
    # Create tables
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Insert customer
        customer = Customer(
            nombre="Cliente Prueba",
            email="prueba@cliente.com",
            telefono="1234567890",
            direccion="Dirección Prueba",
            saldo_inicial=Decimal("0.0")
        )
        session.add(customer)
        session.commit()
        session.refresh(customer)

        # Insert quotes under different states
        quotes = [
            Quote(cliente_id=customer.id, total=Decimal("100.00"), estado="Borrador"),
            Quote(cliente_id=customer.id, total=Decimal("200.00"), estado="Enviada"),
            Quote(cliente_id=customer.id, total=Decimal("300.00"), estado="Aprobada"), # Excluded
            Quote(cliente_id=customer.id, total=Decimal("400.00"), estado="Rechazada"),
            Quote(cliente_id=customer.id, total=Decimal("500.00"), estado="Pendiente"), # Included!
            Quote(cliente_id=customer.id, total=Decimal("600.00"), estado="Cobranza Requerida"), # Included!
        ]
        for q in quotes:
            session.add(q)
        session.commit()

        # Test `read_active_statements` directly
        active_data = read_active_statements(session)
        # Should only include quotes in states 'Pendiente' or 'Cobranza Requerida'
        assert len(active_data) == 2, f"Expected 2 active quotes, got {len(active_data)}. Data: {active_data}"
        total_active_saldo = sum(item["saldo"] for item in active_data)
        assert total_active_saldo == 1100.00, f"Expected total active saldo of 1100.0, got {total_active_saldo}"

        # Test `read_active_customers` directly
        customers_data = read_active_customers(session)
        assert len(customers_data) == 1, f"Expected 1 active customer, got {len(customers_data)}"
        customer_record = customers_data[0]
        assert customer_record["cliente_id"] == customer.id
        assert customer_record["saldo_global"] == 1100.00, f"Expected saldo_global 1100.0, got {customer_record['saldo_global']}"
        assert customer_record["cotizaciones_activas"] == 2, f"Expected 2 active quotes for customer, got {customer_record['cotizaciones_activas']}"

        # Test `get_customer_statement` directly
        statement_data = get_customer_statement(session=session, customer_id=customer.id)
        assert len(statement_data["cotizaciones"]) == 2, f"Expected 2 quotes in statement, got {len(statement_data['cotizaciones'])}"
        assert statement_data["global"]["saldo_pendiente"] == 1100.00

    # Clean up tables
    SQLModel.metadata.drop_all(engine)
