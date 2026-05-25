from app.database import create_db_and_tables, engine
from app.models import SQLModel

# Importar TODOS los modelos para que SQLModel los reconozca al crear las tablas
# Aunque create_db_and_tables usa SQLModel.metadata, es buena práctica asegurarse que los modelos estén cargados
from app.models import (
    Customer, Product, Expense, Quote, QuoteItem, Payment,
    AccountCharge, OtherIncome, ScheduledExpense, ServicePayment
)

if __name__ == "__main__":
    print("Creando base de datos y tablas...")
    create_db_and_tables()
    print("¡Tablas creadas exitosamente!")
