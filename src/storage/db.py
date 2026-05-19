from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/lolka_bot"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


engine = create_engine(get_database_url(), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
