"""
Script: generar_cuentas_clientes.py
=====================================
Genera automáticamente cuentas de acceso para todos los clientes registrados
en la base de datos que aún no tengan un usuario vinculado.

Características:
- Genera usuario único basado en el email del cliente
- Genera contraseña aleatoria segura (12 caracteres)
- Exporta reporte CSV con las credenciales (para distribuirlas)
- No sobreescribe usuarios ya existentes
- Muestra resumen detallado al final

Uso:
    python scripts/generar_cuentas_clientes.py

    # Con opciones:
    python scripts/generar_cuentas_clientes.py --solo-reporte   # Solo muestra, no crea
    python scripts/generar_cuentas_clientes.py --contrasena-fija "MiPassword123"  # Contraseña uniforme
    python scripts/generar_cuentas_clientes.py --sin-csv        # No exporta CSV

Archivo de salida:
    scripts/cuentas_clientes_<FECHA>.csv
"""

import sys
import os
import csv
import secrets
import string
import argparse
from datetime import datetime

# Forzar UTF-8 en la consola de Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Agregar raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine
from app.models import User, Customer, RoleEnum
from app.core.security import get_password_hash


# ─────────────────────────────────────────────
# Generadores
# ─────────────────────────────────────────────

def generar_contrasena(longitud: int = 12) -> str:
    """Genera una contraseña segura aleatoria."""
    caracteres = string.ascii_letters + string.digits + "!@#$%"
    # Asegurar al menos 1 mayúscula, 1 minúscula, 1 dígito, 1 especial
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%"),
    ]
    # Rellenar hasta la longitud deseada
    password += [secrets.choice(caracteres) for _ in range(longitud - 4)]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def generar_username(email: str, nombre: str, session: Session) -> str:
    """Genera un nombre de usuario único a partir del email."""
    base = email.split("@")[0].lower() if email else nombre.lower().replace(" ", "")
    # Limpiar caracteres especiales
    base = "".join(c for c in base if c.isalnum() or c == ".")
    base = base[:30]  # Limitar longitud

    username = base
    counter = 1
    while session.exec(select(User).where(User.username == username)).first():
        username = f"{base}{counter}"
        counter += 1
    return username


# ─────────────────────────────────────────────
# Proceso principal
# ─────────────────────────────────────────────

def procesar_clientes(solo_reporte: bool, contrasena_fija: str | None, exportar_csv: bool):
    resultados = []
    creados = 0
    omitidos = 0
    errores = 0

    print("\n" + "=" * 60)
    print("  GENERADOR MASIVO DE CUENTAS DE CLIENTES")
    print("=" * 60)
    if solo_reporte:
        print("  ⚠️  MODO SOLO REPORTE — No se crearán usuarios")
    print()

    with Session(engine) as session:
        clientes = session.exec(select(Customer)).all()

        if not clientes:
            print("❌ No se encontraron clientes en la base de datos.")
            return

        print(f"📋 Clientes encontrados: {len(clientes)}\n")

        for cliente in clientes:
            if not cliente.email:
                print(f"  ⚠️  [{cliente.nombre}] Sin email — omitido")
                omitidos += 1
                continue

            try:
                # Verificar si ya existe cuenta vinculada al email
                usuario_existente = session.exec(
                    select(User).where(User.email == cliente.email)
                ).first()

                if usuario_existente:
                    # Si existe pero no está vinculado al cliente, vincularlo
                    if not usuario_existente.cliente_id:
                        if not solo_reporte:
                            usuario_existente.cliente_id = cliente.id
                            session.add(usuario_existente)
                        print(f"  🔗 [{cliente.nombre}] Usuario '{usuario_existente.username}' vinculado (ya existía)")
                    else:
                        print(f"  ✅ [{cliente.nombre}] Ya tiene cuenta: '{usuario_existente.username}'")
                    omitidos += 1
                    continue

                # Generar credenciales
                username = generar_username(cliente.email, cliente.nombre, session)
                password = contrasena_fija if contrasena_fija else generar_contrasena()

                if not solo_reporte:
                    nuevo_usuario = User(
                        username=username,
                        email=cliente.email,
                        role=RoleEnum.Cliente,
                        hashed_password=get_password_hash(password),
                        cliente_id=cliente.id,
                        is_active=True,
                    )
                    session.add(nuevo_usuario)

                resultados.append({
                    "nombre_cliente": cliente.nombre,
                    "email": cliente.email,
                    "username": username,
                    "password": password,
                })

                print(f"  ✨ [{cliente.nombre}]  usuario={username}  pass={password}")
                creados += 1

            except Exception as e:
                print(f"  ❌ [{cliente.nombre}] Error: {e}")
                errores += 1

        if not solo_reporte:
            session.commit()

    # ── Exportar CSV ──────────────────────────────
    if exportar_csv and resultados:
        fecha = datetime.now().strftime("%Y%m%d_%H%M")
        carpeta_scripts = os.path.dirname(os.path.abspath(__file__))
        ruta_csv = os.path.join(carpeta_scripts, f"cuentas_clientes_{fecha}.csv")

        with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as f:
            campos = ["nombre_cliente", "email", "username", "password"]
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(resultados)

        print(f"\n📄 Reporte exportado: {ruta_csv}")
    elif exportar_csv and not resultados:
        print("\n📄 No hay nuevas cuentas que exportar al CSV.")

    # ── Resumen final ─────────────────────────────
    print()
    print("=" * 60)
    print("  RESUMEN FINAL")
    print("=" * 60)
    print(f"  ✨ Cuentas {'simuladas' if solo_reporte else 'creadas'}:  {creados}")
    print(f"  ⏭️  Omitidos (ya tienen cuenta): {omitidos}")
    if errores:
        print(f"  ❌ Errores:                      {errores}")
    print("=" * 60)
    if not solo_reporte and creados > 0:
        print("\n  ⚠️  IMPORTANTE: Guarda y distribuye el archivo CSV")
        print("     de forma segura. Contiene contraseñas en texto claro.")
    print()


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Genera cuentas de acceso para clientes registrados en la base de datos."
    )
    parser.add_argument(
        "--solo-reporte",
        action="store_true",
        help="Solo muestra qué haría, sin crear usuarios reales.",
    )
    parser.add_argument(
        "--contrasena-fija",
        type=str,
        default=None,
        metavar="CONTRASEÑA",
        help="Usa la misma contraseña para todos (en lugar de generarlas automáticamente).",
    )
    parser.add_argument(
        "--sin-csv",
        action="store_true",
        help="No exportar el archivo CSV con las credenciales.",
    )

    args = parser.parse_args()
    procesar_clientes(
        solo_reporte=args.solo_reporte,
        contrasena_fija=args.contrasena_fija,
        exportar_csv=not args.sin_csv,
    )
