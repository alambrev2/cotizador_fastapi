import re
import unicodedata
from io import BytesIO
from xhtml2pdf import pisa


def clean_filename(text: str) -> str:
    """Normaliza texto para usarlo como nombre de archivo seguro."""
    if not text:
        return "sin_nombre"
    # Quitar acentos y caracteres especiales
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    # Reemplazar espacios por guiones bajos y remover caracteres no permitidos
    text = text.replace(" ", "_")
    text = re.sub(r'[^a-zA-Z0-9_-]', '', text)
    return text.lower()


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
