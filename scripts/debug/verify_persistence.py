import sys
import os
from sqlmodel import Session, select, create_engine

sys.path.append(os.getcwd())
from app.models import Product


def verify_persistence():
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"
    engine = create_engine(sqlite_url)

    print(f"Verificando base de datos en: {os.path.abspath(sqlite_file_name)}")

    with Session(engine) as session:
        # Check count before
        products = session.exec(select(Product)).all()
        count_before = len(products)
        print(f"Productos antes: {count_before}")
        for p in products:
            print(f" - {p.nombre} (ID: {p.id})")

        # Insert new
        new_p = Product(
            nombre=f"Producto Test Persistence {count_before + 1}",
            precio_menudeo=10.0,
            precio_mayoreo=5.0,
            stock=100,
        )
        session.add(new_p)
        session.commit()
        session.refresh(new_p)
        print(f"\nInsertado: {new_p.nombre} (ID: {new_p.id})")

    # Re-connect (simulate new session/restart)
    print("\nRe-conectando...")
    with Session(engine) as session:
        products_after = session.exec(select(Product)).all()
        count_after = len(products_after)
        print(f"Productos despues: {count_after}")

        if count_after > count_before:
            print("✅ ÉXITO: El producto persistió.")
        else:
            print("❌ FALLO: El producto NO persistió.")


if __name__ == "__main__":
    verify_persistence()
