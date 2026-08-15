"""Test script para verificar la generación del PDF de estado de cuenta."""
from jinja2 import Environment, FileSystemLoader
from app.core.pdf import generate_pdf_bytes
import pdfplumber

env = Environment(loader=FileSystemLoader('app/templates'))
tmpl = env.get_template('pdf/statement.html')

html = tmpl.render(
    client_id=1,
    client_name='Juan Pérez García',
    client_email='juan@ejemplo.com',
    client_telefono='7221234567',
    fecha_generacion='15/08/2026',
    saldo_inicial=0,
    deuda_historica=25000.00,
    saldo_pendiente=8500.00,
    full_history=False,
    tipo_documento='Ultimos 9 Movimientos',
    movements=[
        {'fecha': '10/08/2026', 'origen': 'Cotización #12', 'descripcion': 'Proyecto Web', 'tipo': 'Cargo', 'cargo': 15000.0, 'abono': 0},
        {'fecha': '05/08/2026', 'origen': 'Pago a Cot. #12', 'descripcion': 'Método: Transferencia - Ref: TRF001', 'tipo': 'Abono', 'cargo': 0, 'abono': 5000.0},
        {'fecha': '01/07/2026', 'origen': 'Cotización #8', 'descripcion': 'Mantenimiento', 'tipo': 'Cargo', 'cargo': 3500.0, 'abono': 0},
        {'fecha': '25/06/2026', 'origen': 'Pago a Cot. #8', 'descripcion': 'Método: Efectivo', 'tipo': 'Abono', 'cargo': 0, 'abono': 5000.0},
    ]
)

pdf = generate_pdf_bytes(html, bg_pdf_path='FORMATO BASE PARA ESTADOS DE CUENTA (2) (2).pdf')
out_path = 'test_statement_nuevo.pdf'
with open(out_path, 'wb') as f:
    f.write(pdf)
print(f'PDF generado: {len(pdf):,} bytes -> {out_path}')

with pdfplumber.open(out_path) as p:
    print(f'Paginas: {len(p.pages)}')
    for i, page in enumerate(p.pages):
        img = page.to_image(resolution=150)
        img.save(f'test_statement_nuevo_p{i+1}.png')
print('Preview guardado')
