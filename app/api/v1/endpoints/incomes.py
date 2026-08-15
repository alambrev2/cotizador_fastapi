from typing import List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import OtherIncome, User
from app.api.deps import get_current_active_operativo_or_admin

router = APIRouter()


def _sanitize_dt(val):
    if val is None:
        return None
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            try:
                d = date.fromisoformat(val)
                return datetime(d.year, d.month, d.day)
            except ValueError:
                return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime(val.year, val.month, val.day)
    return val


@router.post("/", response_model=OtherIncome)
def create_other_income(
    *,
    session: Session = Depends(get_session),
    income: OtherIncome,
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    if isinstance(income.fecha_pago, (str, date)):
        income.fecha_pago = _sanitize_dt(income.fecha_pago)
    if isinstance(income.fecha, (str, date)):
        income.fecha = _sanitize_dt(income.fecha)

    session.add(income)
    session.commit()
    session.refresh(income)
    return income


@router.get("/", response_model=List[OtherIncome])
def read_other_incomes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    current_user: User = Depends(get_current_active_operativo_or_admin),
):
    query = select(OtherIncome).order_by(OtherIncome.fecha.desc())
    incomes = session.exec(query.offset(offset).limit(limit)).all()
    return incomes


@router.delete("/{income_id}")
def delete_other_income(
    *,
    session: Session = Depends(get_session),
    income_id: int,
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    income = session.get(OtherIncome, income_id)
    if not income:
        raise HTTPException(status_code=404, detail="Other income not found")
    session.delete(income)
    session.commit()
    return {"ok": True}
