from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import OtherIncome

router = APIRouter()


@router.post("/", response_model=OtherIncome)
def create_other_income(
    *, session: Session = Depends(get_session), income: OtherIncome
):
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
):
    query = select(OtherIncome).order_by(OtherIncome.fecha.desc())
    incomes = session.exec(query.offset(offset).limit(limit)).all()
    return incomes


@router.delete("/{income_id}")
def delete_other_income(*, session: Session = Depends(get_session), income_id: int):
    income = session.get(OtherIncome, income_id)
    if not income:
        raise HTTPException(status_code=404, detail="Other income not found")
    session.delete(income)
    session.commit()
    return {"ok": True}
