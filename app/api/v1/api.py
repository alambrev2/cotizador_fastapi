from fastapi import APIRouter
from app.api.v1.endpoints import (
    customers,
    products,
    quotes,
    payments,
    expenses,
    incomes,
    dashboard,
    scheduled_expenses,
    auth,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(incomes.router, prefix="/incomes", tags=["incomes"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(scheduled_expenses.router, prefix="/scheduled-expenses", tags=["scheduled-expenses"])
