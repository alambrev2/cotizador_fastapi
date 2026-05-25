from sqlmodel import SQLModel, create_engine, Session

sqlite_file_name = "data/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        print(f"Error creando base de datos: {e}")
        raise


def get_session():
    with Session(engine) as session:
        yield session
