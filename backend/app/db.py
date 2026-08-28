"""SQLAlchemy engine, session factory and declarative Base.

Single SQLite file at `backend/nigrani.db`. SQLite is a deliberate choice, not
a shortcut: 118,704 raw rows reduce to a corpus that fits comfortably in one
file, and Postgres would add a service, a container and a demo failure mode for
no benefit a judge can see (CLAUDE.md, "Stack").

The URL is read from `NIGRANI_DATABASE_URL` so that moving to Postgres later is
a configuration change and not a rewrite. Nothing else in the codebase names a
driver, a host or a file path.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .constants import BACKEND_DIR

# backend/app/db.py -> backend/nigrani.db
DB_PATH = BACKEND_DIR / "nigrani.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DB_PATH}"

DATABASE_URL = os.environ.get("NIGRANI_DATABASE_URL", DEFAULT_DATABASE_URL)

_IS_SQLITE = DATABASE_URL.startswith("sqlite")

# check_same_thread=False: FastAPI serves requests from a threadpool, and a
# SQLite connection is otherwise pinned to its creating thread. The argument is
# meaningless to any other driver, so it is only passed for SQLite.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _IS_SQLITE else {},
    future=True,
)


@event.listens_for(engine, "connect")
def _enforce_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """SQLite ignores foreign keys unless asked, per connection, every time.

    DOMAIN-MODEL.md (e) states that every foreign key is enforced. Without this
    listener a payment could reference a work that does not exist and nothing
    would complain until an officer opened an empty case.
    """
    if not _IS_SQLITE:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for every table in models.py."""


def get_db():
    """FastAPI dependency: one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
