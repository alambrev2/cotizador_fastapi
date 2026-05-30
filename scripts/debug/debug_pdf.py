import sys
import os
from datetime import datetime
from decimal import Decimal

# Obtener el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add current dir to path to find app module
sys.path.append(BASE_DIR)

from app.core.pdf import generate_pdf_bytes
from jinja2 import Environment, FileSystemLoader


# Mock objects to simulate SQLModel objects
class MockProduct:
    nombre = "Producto Prueba"
    categoria = "General"


class MockItem:
    cantidad = 2
    precio_unitario = Decimal("50.00")
    producto = MockProduct()


class MockCustomer:
    nombre = "Cliente Prueba"
    email = "cliente@test.com"
    telefono = "555-5555"
    direccion = "Calle Falsa 123"


class MockQuote:
    id = 999
    fecha_creacion = datetime.now()
    total = Decimal("100.00")
    cliente = MockCustomer()
    items = [MockItem(), MockItem()]


def test_pdf():
    print("Iniciando prueba de PDF...")
    try:
        # Load template
        env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, "app", "templates")))
        template = env.get_template("pdf/quote.html")

        # Render HTML
        quote = MockQuote()
        print("Renderizando template...")
        html_content = template.render(quote=quote)
        print("Template renderizado (len check):", len(html_content))

        # Generate PDF
        print("Generando bytes PDF con xhtml2pdf...")
        pdf_bytes = generate_pdf_bytes(html_content)
        print(f"Éxito! PDF generado: {len(pdf_bytes)} bytes")

        # Save to verify
        with open("debug_output.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("Guardado en debug_output.pdf")

    except Exception as e:
        print("ERROR CRÍTICO:", str(e))
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_pdf()
