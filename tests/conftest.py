"""Fixtures de pytest con base de datos temporal.

La variable DATABASE_URL se fija ANTES de importar cualquier módulo de la app
para que ``app.database`` apunte a un SQLite temporal y los tests NUNCA toquen
``data/database.db`` (la BD de producción).
"""
import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="cotizador_tests_")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp_dir, 'test.db')}"

import pytest
from sqlmodel import Session, SQLModel
from fastapi.testclient import TestClient

from app.database import engine
from app.main import app


@pytest.fixture()
def db():
    """BD limpia por test: recrea todas las tablas."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def client(db):
    """Cliente HTTP contra la app real usando la BD temporal."""
    with TestClient(app) as c:
        yield c
