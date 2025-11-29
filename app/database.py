# app/database.py

from typing import Generator
from sqlmodel import SQLModel, Session, create_engine

from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}  # SQLite specific
)


def init_db() -> None:
    from . import models  # ensures model classes are imported
    SQLModel.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
