"""Utilidades de fecha/hora del sistema.

Convención:
- Almacenamiento en base de datos: datetime NAIVE en UTC (sin zona horaria).
- "Ahora" / "hoy" del negocio: zona horaria configurada en ``settings.TIMEZONE``
  (por defecto America/Mexico_City), expuesta como datetime/date naive local.
- Los cortes mensuales (dashboard) se calculan en hora local del negocio y se
  convierten a UTC-naive antes de consultar la base de datos, para que los
  meses no se corran por la diferencia horaria.
"""
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings

BUSINESS_TZ = ZoneInfo(settings.TIMEZONE or "America/Mexico_City")


def utcnow() -> datetime:
    """Hora UTC actual como datetime naive (estándar de almacenamiento)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def now_local() -> datetime:
    """Hora actual en la zona del negocio como datetime naive."""
    return datetime.now(BUSINESS_TZ).replace(tzinfo=None)


def today_local() -> date:
    """Fecha actual en la zona del negocio."""
    return datetime.now(BUSINESS_TZ).date()


def to_utc(dt: datetime) -> datetime:
    """Convierte un datetime naive (interpretado como hora local del negocio)
    a datetime naive UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BUSINESS_TZ)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def month_bounds_utc(year: int, month: int):
    """Devuelve (primer_instante, último_instante) del mes en hora local del
    negocio, convertidos a UTC-naive para consultas a la BD."""
    import calendar

    last = calendar.monthrange(year, month)[1]
    first = datetime(year, month, 1)
    last_dt = datetime(year, month, last, 23, 59, 59, 999999)
    return to_utc(first), to_utc(last_dt)
