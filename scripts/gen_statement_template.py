"""Regenera statement.html limpio con header/footer del formato base."""
import base64

brain_dir = r'C:/Users/HP/.gemini/antigravity/brain/88f27d62-ab23-4322-948f-be187c59f771'
out = r'app/templates/pdf/statement.html'

with open(brain_dir + '/header.png', 'rb') as f:
    H = base64.b64encode(f.read()).decode()
with open(brain_dir + '/footer.png', 'rb') as f:
    FO = base64.b64encode(f.read()).decode()

css = """
@page {
    size: letter;
    margin: 3.0cm 0cm 2.3cm 0cm;
    @frame header_frame {
        -pdf-frame-content: headerContent;
        top: 0cm;
        left: 0cm;
        right: 0cm;
        width: 21.59cm;
        height: 3.0cm;
    }
    @frame footer_frame {
        -pdf-frame-content: footerContent;
        bottom: 0cm;
        left: 0cm;
        right: 0cm;
        width: 21.59cm;
        height: 2.3cm;
    }
}
body {
    font-family: Helvetica, sans-serif;
    font-size: 9pt;
    color: #2d3748;
    margin-left: 1.5cm;
    margin-right: 1.5cm;
    margin-top: 0.3cm;
}
.info-table { width: 100%; margin-bottom: 8px; border-collapse: collapse; }
.info-table td { line-height: 1.5; font-size: 9pt; padding: 1px 0; }
.cli-badge { font-size: 16pt; font-weight: bold; color: #1b4f6a; }
.saldo-banner { width: 100%; border-collapse: collapse; margin-bottom: 10px; border: 2px solid #1b8a8f; }
.saldo-banner td { padding: 8px 14px; vertical-align: middle; }
.saldo-cell-main { border-right: 1px solid #9ecfcf; background-color: #f0fafa; }
.saldo-label { font-size: 7.5pt; color: #0e6b70; text-transform: uppercase; letter-spacing: 0.5px; font-weight: bold; }
.saldo-amount { font-size: 18pt; font-weight: bold; color: #0e6b70; }
.saldo-sub-label { font-size: 7.5pt; color: #15803d; text-transform: uppercase; letter-spacing: 0.5px; font-weight: bold; }
.saldo-sub-amount { font-size: 13pt; font-weight: bold; color: #15803d; }
.saldo-total-label { font-size: 7.5pt; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; font-weight: bold; }
.saldo-total-amount { font-size: 12pt; font-weight: bold; color: #334155; }
table.items-table { width: 100%; border-collapse: collapse; margin-bottom: 8px; }
table.items-table th { background-color: #1b4f6a; color: #fff; font-weight: bold; padding: 5px 7px; text-align: left; font-size: 8pt; }
table.items-table td { padding: 4px 7px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; }
table.items-table tr:nth-child(even) td { background-color: #f8fafc; }
.text-right { text-align: right; }
.text-center { text-align: center; }
.row-cargo { color: #c0392b; font-weight: bold; }
.row-abono { color: #1b8a8f; font-weight: bold; }
.section-title { font-size: 8.5pt; font-weight: bold; color: #1b4f6a; border-left: 3px solid #e8820c; padding-left: 7px; margin-bottom: 5px; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.nota-footer { color: #94a3b8; font-size: 7pt; border-top: 1px solid #e2e8f0; padding-top: 4px; margin-top: 6px; }
"""

body = """\
<!-- DATOS DEL CLIENTE -->
<table class="info-table">
    <tr>
        <td width="60%" valign="top">
            <strong>No. de Cliente:</strong> {{ client_id }}<br/>
            <strong>Nombre:</strong> {{ client_name }}<br/>
            <strong>Tel&eacute;fono:</strong> {{ client_telefono or 'N/D' }}<br/>
            <strong>Correo:</strong> {{ client_email or 'N/D' }}
        </td>
        <td width="40%" valign="top" style="text-align:right;">
            <div class="cli-badge">CLI-{{ "%04d" % client_id }}</div>
            <div style="font-size:8pt; color:#64748b; margin-top:3px;">
                <strong>Tipo:</strong> {{ tipo_documento }}<br/>
                <strong>Fecha de emisi&oacute;n:</strong> {{ fecha_generacion }}
            </div>
        </td>
    </tr>
</table>

<!-- SALDOS BANNER -->
<table class="saldo-banner">
    <tr>
        <td width="40%" class="saldo-cell-main">
            <div class="saldo-label">Saldo Pendiente</div>
            <div class="saldo-amount">${{ "{:,.2f}".format(saldo_pendiente) }}</div>
        </td>
        <td width="30%" style="border-right: 1px solid #9ecfcf;">
            <div class="saldo-sub-label">Total Pagado</div>
            <div class="saldo-sub-amount">${{ "{:,.2f}".format(deuda_historica - saldo_pendiente) }}</div>
        </td>
        <td width="30%" style="text-align:right; padding-right:14px;">
            <div class="saldo-total-label">Deuda Total</div>
            <div class="saldo-total-amount">${{ "{:,.2f}".format(deuda_historica) }}</div>
        </td>
    </tr>
</table>

<!-- MOVIMIENTOS -->
<div class="section-title">
    Movimientos &mdash; {{ "(Historial Completo)" if full_history else "(Ultimos 9)" }}
</div>

<table class="items-table">
    <thead>
        <tr>
            <th width="11%">Fecha</th>
            <th width="22%">Origen</th>
            <th width="33%">Concepto</th>
            <th width="10%" class="text-center">Tipo</th>
            <th width="12%" class="text-right">Cargo</th>
            <th width="12%" class="text-right">Abono</th>
        </tr>
    </thead>
    <tbody>
        {% for mov in movements %}
        <tr>
            <td>{{ mov.fecha }}</td>
            <td><strong>{{ mov.origen }}</strong></td>
            <td>{{ mov.descripcion }}</td>
            <td class="text-center {% if mov.tipo == 'Cargo' %}row-cargo{% else %}row-abono{% endif %}">
                {{ mov.tipo }}
            </td>
            <td class="text-right">
                {% if mov.cargo > 0 %}<span class="row-cargo">${{ "{:,.2f}".format(mov.cargo) }}</span>{% else %}-{% endif %}
            </td>
            <td class="text-right">
                {% if mov.abono > 0 %}<span class="row-abono">${{ "{:,.2f}".format(mov.abono) }}</span>{% else %}-{% endif %}
            </td>
        </tr>
        {% else %}
        <tr>
            <td colspan="6" class="text-center" style="padding: 12px; color: #94a3b8;">No hay movimientos registrados.</td>
        </tr>
        {% endfor %}
        {% if saldo_inicial and saldo_inicial > 0 %}
        <tr style="background-color: #fff5f5;">
            <td>--/--/----</td>
            <td>Apertura</td>
            <td>Saldo Inicial de Cuenta</td>
            <td class="text-center"><span class="row-cargo">Cargo</span></td>
            <td class="text-right"><span class="row-cargo">${{ "{:,.2f}".format(saldo_inicial) }}</span></td>
            <td class="text-right">-</td>
        </tr>
        {% endif %}
    </tbody>
</table>

<p class="nota-footer">
    <em>Nota:</em> Este estado de cuenta refleja los saldos a la fecha de emisi&oacute;n.
    Los pagos pueden tardar hasta 24h en reflejarse. &nbsp;|&nbsp;
    Smart Site Company &middot; smartsitecompany.com &middot; 729 117 2795
</p>
"""

doc = (
    '<!DOCTYPE html>\n<html>\n<head>\n<style>\n'
    + css
    + '\n</style>\n</head>\n<body>\n\n'
    + '<div id="headerContent">\n'
    + '<img src="data:image/png;base64,' + H + '" style="width:21.59cm; display:block;" />\n'
    + '</div>\n\n'
    + '<div id="footerContent">\n'
    + '<img src="data:image/png;base64,' + FO + '" style="width:21.59cm; display:block;" />\n'
    + '</div>\n\n'
    + body
    + '\n</body>\n</html>\n'
)

with open(out, 'w', encoding='utf-8') as f:
    f.write(doc)

print('Template generado:', out, 'Size:', len(doc), 'chars')
