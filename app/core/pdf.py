from io import BytesIO
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from xhtml2pdf import pisa


def generate_pdf_bytes(
    html_content: str,
    bg_pdf_path: str | Path | None = None,
    title: str | None = None
) -> bytes:
    """Convierte un string HTML a bytes PDF usando xhtml2pdf.
    
    Si se especifica bg_pdf_path, superpone cada página del PDF generado sobre
    la página de fondo correspondiente.
    Si se especifica title, agrega el título en los metadatos del PDF.
    """
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html_content,  # String HTML
        dest=buffer,  # Buffer de bytes
    )

    if pisa_status.err:
        raise Exception(f"Error generando PDF: {pisa_status.err}")

    buffer.seek(0)
    content_reader = PdfReader(buffer)

    writer = PdfWriter()

    if bg_pdf_path:
        with open(bg_pdf_path, "rb") as bg_file:
            bg_bytes = bg_file.read()

        for page in content_reader.pages:
            bg_reader = PdfReader(BytesIO(bg_bytes))
            bg_page = bg_reader.pages[0]
            bg_page.merge_page(page)
            writer.add_page(bg_page)
    else:
        for page in content_reader.pages:
            writer.add_page(page)

    if title:
        writer.add_metadata({"/Title": title})

    output_buffer = BytesIO()
    writer.write(output_buffer)
    return output_buffer.getvalue()

