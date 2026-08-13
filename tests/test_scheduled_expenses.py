"""Recurrencia de egresos programados: semanal respeta el día de la semana."""
import datetime as dt

from sqlmodel import select

from app.core.security import get_password_hash
from app.models import User, RoleEnum, ScheduledExpense


def _admin(db):
    user = User(
        username="admin_recurrencia",
        email="admin_recurrencia@test.com",
        role=RoleEnum.Administrador,
        hashed_password=get_password_hash("admin123"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, username="admin_recurrencia"):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": "admin123"},
    )
    assert resp.status_code == 200, resp.text


def _scheduled(db, descripcion):
    return db.exec(
        select(ScheduledExpense).where(ScheduledExpense.descripcion == descripcion)
    ).all()


def test_recurrencia_semanal_respeta_dia_de_semana(client, db):
    _admin(db)
    _login(client)

    fecha = dt.date(2026, 8, 3)  # lunes
    resp = client.post(
        "/api/v1/scheduled-expenses/",
        json={
            "descripcion": "Pago semanal",
            "monto": 500,
            "fecha_vencimiento": str(fecha),
            "frecuencia": "Semanal",
        },
    )
    assert resp.status_code == 200, resp.text

    rows = sorted(_scheduled(db, "Pago semanal"), key=lambda r: r.fecha_vencimiento)
    # Original + clones semanales hasta 12 meses despues de la fecha base
    assert len(rows) >= 3, f"esperaba al menos 3 filas, hay {len(rows)}"
    assert rows[0].frecuencia == "Semanal"
    for r in rows:
        # Todas caen el mismo día de la semana (lunes = 0)
        assert r.fecha_vencimiento.weekday() == 0, f"{r.fecha_vencimiento} no es lunes"
    for a, b in zip(rows, rows[1:]):
        # Diferencia exacta de 7 días entre ocurrencias
        assert (b.fecha_vencimiento - a.fecha_vencimiento).days == 7


def test_recurrencia_semanal_funciona_despues_de_2026(client, db):
    _admin(db)
    _login(client)

    fecha = dt.date(2027, 8, 13)  # viernes, año futuro
    resp = client.post(
        "/api/v1/scheduled-expenses/",
        json={
            "descripcion": "Prueba semanal 2027",
            "monto": 100,
            "fecha_vencimiento": str(fecha),
            "frecuencia": "Semanal",
        },
    )
    assert resp.status_code == 200, resp.text

    rows = sorted(_scheduled(db, "Prueba semanal 2027"), key=lambda r: r.fecha_vencimiento)
    # El horizonte debe ser dinamico: la fecha base (2027) no puede quedarse sin clones
    assert len(rows) >= 3, f"esperaba al menos 3 filas, hay {len(rows)}"
    assert rows[0].fecha_vencimiento == fecha
    for r in rows:
        assert r.fecha_vencimiento.weekday() == fecha.weekday()
    for a, b in zip(rows, rows[1:]):
        assert (b.fecha_vencimiento - a.fecha_vencimiento).days == 7


def test_recurrencia_mensual_sigue_funcionando(client, db):
    _admin(db)
    _login(client)

    resp = client.post(
        "/api/v1/scheduled-expenses/",
        json={
            "descripcion": "Renta mensual",
            "monto": 2000,
            "fecha_vencimiento": "2026-08-15",
            "frecuencia": "Mensual",
        },
    )
    assert resp.status_code == 200, resp.text

    rows = sorted(_scheduled(db, "Renta mensual"), key=lambda r: r.fecha_vencimiento)
    assert len(rows) >= 2, f"esperaba al menos 2 filas, hay {len(rows)}"
    assert rows[0].frecuencia == "Mensual"
    for a, b in zip(rows, rows[1:]):
        assert b.fecha_vencimiento.month == (a.fecha_vencimiento.month % 12) + 1
        assert b.fecha_vencimiento.year == a.fecha_vencimiento.year + (1 if a.fecha_vencimiento.month == 12 else 0)
