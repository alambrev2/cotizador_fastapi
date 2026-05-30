from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from datetime import datetime
import datetime as dt
from dateutil.relativedelta import relativedelta

router = APIRouter()

from app.models import ScheduledExpense, ScheduledExpenseBase

class ScheduledExpenseCreate(ScheduledExpenseBase):
    pass

@router.post("/", response_model=ScheduledExpense)
def create_scheduled_expense(*, session: Session = Depends(get_session), expense: ScheduledExpenseCreate):
    base_obj = ScheduledExpense.from_orm(expense)
    session.add(base_obj)
    
    # Manejar recurrencia hasta 2 años a partir de la fecha de inicio
    if expense.frecuencia != 'Único':
        current_date = expense.fecha_vencimiento
        limit_date = current_date + relativedelta(years=2)
        
        step_months = 1
        if expense.frecuencia == 'Bimestral': step_months = 2
        elif expense.frecuencia == 'Semestral': step_months = 6
        elif expense.frecuencia == 'Anual': step_months = 12
            
        next_date = current_date + relativedelta(months=step_months)
        while next_date <= limit_date:
            cloned = ScheduledExpense(
                descripcion=expense.descripcion,
                monto=expense.monto,
                fecha_vencimiento=next_date,
                categoria=expense.categoria,
                clabe=expense.clabe,
                estatus='Pendiente',
                frecuencia=expense.frecuencia
            )
            session.add(cloned)
            next_date += relativedelta(months=step_months)
            
    session.commit()
    session.refresh(base_obj)
    return base_obj

@router.get("/", response_model=List[ScheduledExpense])
def read_scheduled_expenses(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    query = select(ScheduledExpense).order_by(ScheduledExpense.fecha_vencimiento.asc())
    return session.exec(query.offset(offset).limit(limit)).all()

@router.patch("/{expense_id}", response_model=ScheduledExpense)
def update_scheduled_expense(
    *,
    session: Session = Depends(get_session),
    expense_id: int,
    expense_update: ScheduledExpenseCreate
):
    db_obj = session.get(ScheduledExpense, expense_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    expense_data = expense_update.dict(exclude_unset=True)
    for key, value in expense_data.items():
        setattr(db_obj, key, value)
    
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

@router.delete("/{expense_id}")
def delete_scheduled_expense(*, session: Session = Depends(get_session), expense_id: int):
    expense = session.get(ScheduledExpense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    session.delete(expense)
    session.commit()
    return {"ok": True}
