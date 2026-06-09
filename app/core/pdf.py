from io import BytesIO
from xhtml2pdf import pisa


def generate_pdf_bytes(html_content: str) -> bytes:
    """Convierte un string HTML a bytes PDF usando xhtml2pdf."""
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_content,  # String HTML
        dest=buffer,  # Buffer de bytes
    )

    if pisa_status.err:
        raise Exception(f"Error generando PDF: {pisa_status.err}")

    return buffer.getvalue()
