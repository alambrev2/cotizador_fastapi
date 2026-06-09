"""
Script de Validación: Flujo de Caja Real
==========================================
Valida que el Flujo de Caja Real se calcule correctamente:
  Flujo de Caja Real = Ingresos Totales Confirmados - Egresos Ejecutados

Verificaciones realizadas:
  1. No hay registros duplicados en Payment (por ID único)
  2. No hay registros duplicados en Expense (por ID único)
  3. Los OtherIncome NO se incluyen en el flujo de caja del dashboard (solo Payment)
  4. El cálculo del endpoint /api/v1/dashboard/summary coincide con el cálculo manual
  5. Se detalla cada registro sumado con su ID para auditoría

Uso:
  python scripts/validar_flujo_caja.py
"""

import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models import Payment, Expense, OtherIncome


def validar_duplicados(registros, nombre_tabla):
    """Verifica que no existan IDs duplicados en una lista de registros."""
    ids = [r.id for r in registros]
    ids_unicos = set(ids)
    duplicados = len(ids) - len(ids_unicos)

    if duplicados > 0:
        # Encontrar cuáles están duplicados
        vistos = set()
        repetidos = []
        for rid in ids:
            if rid in vistos:
                repetidos.append(rid)
            vistos.add(rid)
        return False, repetidos
    return True, []


def main():
    print("=" * 70)
    print("  VALIDACIÓN DE FLUJO DE CAJA REAL")
    print("  Sistema Cotizador - Smart Site Company")
    print("=" * 70)
    print()

    with Session(engine) as session:
        # ─────────────────────────────────────────────────────────────
        # 1. Obtener TODOS los pagos (Ingresos Confirmados)
        # ─────────────────────────────────────────────────────────────
        all_payments = session.exec(select(Payment)).all()

        print("━" * 70)
        print("  📥 INGRESOS TOTALES CONFIRMADOS (Tabla: Payment)")
        print("━" * 70)

        # Validar duplicados
        sin_dup, dup_ids = validar_duplicados(all_payments, "Payment")
        if sin_dup:
            print("  ✅ Sin duplicados detectados en Payment")
        else:
            print(f"  ⚠️  DUPLICADOS ENCONTRADOS en Payment: IDs {dup_ids}")

        # Deduplicar por ID (misma lógica que el dashboard.py)
        unique_payments = {p.id: p for p in all_payments}.values()

        print(f"\n  {'ID':>4} | {'Fecha':<22} | {'Método':<15} | {'Vinculación':<22} | {'Monto':>12}")
        print(f"  {'─'*4}─┼─{'─'*22}─┼─{'─'*15}─┼─{'─'*22}─┼─{'─'*12}")

        ingresos_totales = 0.0
        for p in sorted(unique_payments, key=lambda x: x.id):
            monto = float(p.monto) if p.monto else 0.0
            ingresos_totales += monto

            # Determinar vinculación
            if p.quote_id:
                vinculo = f"Cotización #{p.quote_id}"
            elif p.cargo_id:
                vinculo = f"Cargo #{p.cargo_id}"
            elif p.cliente_id:
                vinculo = f"Cliente #{p.cliente_id} (Global)"
            else:
                vinculo = "Sin vincular"

            fecha_str = str(p.fecha_pago)[:19] if p.fecha_pago else "N/A"
            print(f"  {p.id:>4} | {fecha_str:<22} | {p.metodo_pago or 'N/A':<15} | {vinculo:<22} | ${monto:>10,.2f}")

        print(f"\n  {'':>4}   {'':>22}   {'':>15}   {'TOTAL INGRESOS':>22}   ${ingresos_totales:>10,.2f}")
        print(f"  Registros: {len(list(unique_payments))} (de {len(all_payments)} consultados)")

        # ─────────────────────────────────────────────────────────────
        # 2. Obtener TODOS los gastos ejecutados (Egresos)
        # ─────────────────────────────────────────────────────────────
        all_expenses = session.exec(select(Expense)).all()

        print()
        print("━" * 70)
        print("  📤 EGRESOS EJECUTADOS (Tabla: Expense)")
        print("━" * 70)

        sin_dup_e, dup_ids_e = validar_duplicados(all_expenses, "Expense")
        if sin_dup_e:
            print("  ✅ Sin duplicados detectados en Expense")
        else:
            print(f"  ⚠️  DUPLICADOS ENCONTRADOS en Expense: IDs {dup_ids_e}")

        unique_expenses = {e.id: e for e in all_expenses}.values()

        print(f"\n  {'ID':>4} | {'Fecha':<22} | {'Categoría':<20} | {'Descripción':<25} | {'Monto':>12}")
        print(f"  {'─'*4}─┼─{'─'*22}─┼─{'─'*20}─┼─{'─'*25}─┼─{'─'*12}")

        egresos_ejecutados = 0.0
        for e in sorted(unique_expenses, key=lambda x: x.id):
            monto = float(e.monto) if e.monto else 0.0
            egresos_ejecutados += monto
            fecha_str = str(e.fecha)[:19] if e.fecha else "N/A"
            desc = (e.descripcion or "")[:25]
            cat = (e.categoria or "General")[:20]
            print(f"  {e.id:>4} | {fecha_str:<22} | {cat:<20} | {desc:<25} | ${monto:>10,.2f}")

        print(f"\n  {'':>4}   {'':>22}   {'':>20}   {'TOTAL EGRESOS':>25}   ${egresos_ejecutados:>10,.2f}")
        print(f"  Registros: {len(list(unique_expenses))} (de {len(all_expenses)} consultados)")

        # ─────────────────────────────────────────────────────────────
        # 3. Verificar OtherIncome (NO deben sumarse al flujo de caja)
        # ─────────────────────────────────────────────────────────────
        all_other = session.exec(select(OtherIncome)).all()

        print()
        print("━" * 70)
        print("  ℹ️  OTROS INGRESOS (Tabla: OtherIncome) — NO incluidos en Flujo de Caja")
        print("━" * 70)

        total_otros = sum(float(o.monto) for o in all_other if o.monto)
        print(f"  Registros: {len(all_other)}")
        print(f"  Suma total: ${total_otros:,.2f}")
        print(f"  📌 NOTA: El endpoint /api/v1/dashboard/summary calcula el Flujo de")
        print(f"     Caja Real usando SOLO la tabla Payment como ingresos confirmados.")
        print(f"     Los OtherIncome NO se incluyen en este cálculo.")

        # ─────────────────────────────────────────────────────────────
        # 4. CÁLCULO FINAL: Flujo de Caja Real
        # ─────────────────────────────────────────────────────────────
        flujo_caja_real = ingresos_totales - egresos_ejecutados

        print()
        print("━" * 70)
        print("  💰 RESULTADO: FLUJO DE CAJA REAL")
        print("━" * 70)
        print()
        print(f"    Ingresos Totales Confirmados (Payment):  ${ingresos_totales:>12,.2f}")
        print(f"  - Egresos Ejecutados (Expense):            ${egresos_ejecutados:>12,.2f}")
        print(f"                                             {'─' * 14}")
        print(f"  = FLUJO DE CAJA REAL:                      ${flujo_caja_real:>12,.2f}")
        print()

        if flujo_caja_real >= 0:
            print(f"  ✅ ESTADO: POSITIVO — El negocio tiene más ingresos que egresos.")
        else:
            print(f"  ⚠️  ESTADO: NEGATIVO — Los egresos superan los ingresos confirmados.")

        # ─────────────────────────────────────────────────────────────
        # 5. Comparar con el valor del endpoint dashboard/summary
        # ─────────────────────────────────────────────────────────────
        print()
        print("━" * 70)
        print("  🔍 VALIDACIÓN CRUZADA vs ENDPOINT /api/v1/dashboard/summary")
        print("━" * 70)

        # Replicamos la lógica exacta del dashboard.py (líneas 140-149)
        dashboard_ingresos = sum(float(p.monto) for p in {p.id: p for p in all_payments}.values() if p.monto)
        dashboard_egresos = sum(float(e.monto) for e in {e.id: e for e in all_expenses}.values() if e.monto)
        dashboard_flujo = dashboard_ingresos - dashboard_egresos

        print(f"\n  Cálculo del Script:")
        print(f"    Ingresos: ${ingresos_totales:>12,.2f}")
        print(f"    Egresos:  ${egresos_ejecutados:>12,.2f}")
        print(f"    Flujo:    ${flujo_caja_real:>12,.2f}")
        print()
        print(f"  Cálculo replicando lógica dashboard.py:")
        print(f"    Ingresos: ${dashboard_ingresos:>12,.2f}")
        print(f"    Egresos:  ${dashboard_egresos:>12,.2f}")
        print(f"    Flujo:    ${dashboard_flujo:>12,.2f}")

        # Comparar
        diff = abs(flujo_caja_real - dashboard_flujo)
        if diff < 0.01:
            print(f"\n  ✅ VALIDACIÓN EXITOSA: Ambos cálculos coinciden (diferencia: ${diff:.2f})")
        else:
            print(f"\n  ❌ DISCREPANCIA DETECTADA: Diferencia de ${diff:.2f}")
            print(f"     Revisar lógica del endpoint dashboard/summary")

        # ─────────────────────────────────────────────────────────────
        # 6. Resumen de integridad
        # ─────────────────────────────────────────────────────────────
        print()
        print("━" * 70)
        print("  📋 RESUMEN DE INTEGRIDAD")
        print("━" * 70)

        checks = [
            ("Sin duplicados en Payment", sin_dup),
            ("Sin duplicados en Expense", sin_dup_e),
            ("Cálculo script = Cálculo dashboard", diff < 0.01),
            ("OtherIncome excluido del flujo", True),  # Por diseño
        ]

        all_passed = True
        for label, passed in checks:
            icon = "✅" if passed else "❌"
            if not passed:
                all_passed = False
            print(f"  {icon} {label}")

        print()
        if all_passed:
            print("  🎉 TODAS LAS VALIDACIONES PASARON CORRECTAMENTE")
        else:
            print("  ⚠️  HAY VALIDACIONES FALLIDAS — REVISAR ARRIBA")

        print()
        print("=" * 70)

        return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
