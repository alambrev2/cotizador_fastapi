"""Cálculos financieros centralizados.

Aquí vive la ÚNICA definición de cómo se calcula la deuda y el saldo de un
cliente, para que todos los endpoints muestren los mismos números.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Set

from app.models import QuoteEstado

# Estados que representan deuda activa (dinero que el cliente debe):
# - Aprobada: proyecto aprobado (el stock ya se comprometió)
# - Pendiente: en proceso de cobro
# - Cobranza Requerida: requiere cobranza
DEBT_ESTADOS: Set[str] = {
    QuoteEstado.Aprobada.value,
    QuoteEstado.Pendiente.value,
    QuoteEstado.Cobranza_Requerida.value,
}

# Tolerancia para considerar un saldo como "pagado" (evita ruido de centavos)
SALDO_TOLERANCIA = Decimal("0.01")


def es_estado_de_deuda(estado: Optional[str]) -> bool:
    return estado in DEBT_ESTADOS


def _decimal(valor) -> Decimal:
    return Decimal(str(valor or 0))


def money(valor) -> float:
    """Convierte un monto Decimal a float redondeado a 2 decimales (solo en la
    frontera de salida, para JSON). Todo cálculo interno se hace en Decimal."""
    return float(_decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def sum_decimal(iterable) -> Decimal:
    """Suma montos (Decimal o compatibles) sin pasar por float."""
    return sum((_decimal(v) for v in iterable), Decimal("0"))


def saldo_de_cotizacion(quote) -> Decimal:
    """Saldo pendiente de una cotización: total - pagos vinculados."""
    total = _decimal(quote.total)
    pagado = sum((_decimal(p.monto) for p in quote.pagos), Decimal("0"))
    return total - pagado


def calcular_saldo_cliente(customer) -> dict:
    """Calcula deuda total, total pagado y saldo de un cliente.

    ``customer`` debe traer cargadas las relaciones:
    ``cotizaciones`` (con ``pagos``), ``cargos`` (con ``pagos``) y ``pagos``.

    Reglas (definidas aquí, una sola vez):
    - Deuda = saldo_inicial + total de cotizaciones en deuda + total de cargos
    - Pagado = suma de TODOS los pagos del cliente (vinculados a cotizaciones,
      a cargos o directos), sin duplicar por id.
    - Saldo = deuda - pagado
    """
    saldo_inicial = _decimal(customer.saldo_inicial)

    comprado = sum(
        (_decimal(q.total) for q in customer.cotizaciones if es_estado_de_deuda(q.estado)),
        Decimal("0"),
    )
    total_cargos = sum((_decimal(c.monto) for c in customer.cargos), Decimal("0"))
    deuda_total = saldo_inicial + comprado + total_cargos

    # Recolectar todos los pagos sin duplicar (un pago puede aparecer en
    # customer.pagos y también en quote.pagos / cargo.pagos).
    pagos_ids: dict = {}
    for p in customer.pagos:
        pagos_ids[p.id] = _decimal(p.monto)
    for q in customer.cotizaciones:
        for p in q.pagos:
            pagos_ids[p.id] = _decimal(p.monto)
    for c in customer.cargos:
        for p in c.pagos:
            pagos_ids[p.id] = _decimal(p.monto)
    total_pagado = sum(pagos_ids.values(), Decimal("0"))

    saldo = deuda_total - total_pagado
    return {
        "saldo_inicial": saldo_inicial,
        "total_comprado": comprado,
        "total_cargos": total_cargos,
        "deuda_total": deuda_total,
        "total_pagado": total_pagado,
        "saldo": saldo,
    }
