from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Expense, User
from app.api.deps import get_current_active_admin

router = APIRouter()


@router.post("/", response_model=Expense)
def create_expense(
    *,
    session: Session = Depends(get_session),
    expense: Expense,
    current_user: User = Depends(get_current_active_admin)
):
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
    current_user: User = Depends(get_current_active_admin),
):
    query = select(Expense).order_by(Expense.fecha.desc())
    expenses = session.exec(query.offset(offset).limit(limit)).all()
    return expenses


@router.delete("/{expense_id}")
def delete_expense(
    *,
    session: Session = Depends(get_session),
    expense_id: int,
    current_user: User = Depends(get_current_active_admin)
):
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    session.delete(expense)
    session.commit()
    return {"ok": True}
