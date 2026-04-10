"""SQLAlchemy engine + session com suporte a Row Level Security multi-tenant."""
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """Dependência FastAPI: sessão sem tenant setado (para auth)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def tenant_session(tenant_id: str) -> Iterator[Session]:
    """Sessão com app.current_tenant setado para ativar o RLS."""
    db = SessionLocal()
    try:
        db.execute(text("SET LOCAL app.current_tenant = :tid"), {"tid": str(tenant_id)})
        yield db
    finally:
        db.close()


def set_tenant(db: Session, tenant_id: str) -> None:
    """Ativa o contexto de tenant numa sessão existente."""
    db.execute(text("SET LOCAL app.current_tenant = :tid"), {"tid": str(tenant_id)})
