import os
from typing import Any, List, Optional, Type

from dotenv import load_dotenv
from sqlmodel import SQLModel, select

from database.session import DBSession

load_dotenv()

DB_HOST = os.environ.get("POSTGRES_HOST")
DB_USER = os.environ.get("POSTGRES_USER")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
DB_NAME = os.environ.get("POSTGRES_DB")
DB_PORT = os.environ.get("POSTGRES_PORT", 5432)

db = DBSession(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)


def get_all(model: Type[SQLModel], tenant_schema: Optional[str] = None) -> List[Any]:
    """Fetch all rows for the given SqlModel `model`."""
    if tenant_schema:
        with db.tenant_session(tenant_schema) as session:
            statement = select(model)
            return session.exec(statement).all()

    with db.session() as session:
        return session.exec(select(model)).all()


def get_by_id(
    model: Type[SQLModel], id: Any, tenant_schema: Optional[str] = None
) -> Optional[Any]:
    """Fetch a single row by ID for the given SqlModel `model`."""
    if tenant_schema:
        with db.tenant_session(tenant_schema) as session:
            return session.get(model, id)

    with db.session() as session:
        return session.get(model, id)
