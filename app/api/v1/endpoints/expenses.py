from typing import List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Expense, User
from app.api.deps import get_current_active_operativo_or_admin

router = APIRouter()


def _sanitize_dt(val):
    if val is None or val == "":
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        if val.endswith("Z"):
            val = val[:-1]
        try:
            return datetime.fromisoformat(val).replace(tzinfo=None)
        except ValueError:
            try:
                d = date.fromisoformat(val)
                return datetime(d.year, d.month, d.day)
            except ValueError:
                return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return datetime(val.year, val.month, val.day)
    return val


@router.post("/", response_model=Expense)
def create_expense(
    *,
    session: Session = Depends(get_session),
    expense: Expense,
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    expense.fecha_pago = _sanitize_dt(expense.fecha_pago)
    expense.fecha = _sanitize_dt(expense.fecha) or datetime.now()

    session.add(expense)
    session.commit()
    session.refresh(expense)
    return expense


@router.get("/", response_model=List[Expense])
def read_expenses(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    current_user: User = Depends(get_current_active_operativo_or_admin),
):
    query = select(Expense).order_by(Expense.fecha.desc())
    expenses = session.exec(query.offset(offset).limit(limit)).all()
    return expenses


@router.delete("/{expense_id}")
def delete_expense(
    *,
    session: Session = Depends(get_session),
    expense_id: int,
    current_user: User = Depends(get_current_active_operativo_or_admin)
):
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    session.delete(expense)
    session.commit()
    return {"ok": True}
