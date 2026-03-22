from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session
from pathlib import Path
from app.config import config


class Base(DeclarativeBase):
    pass


def get_engine(db_path: str | None = None):
    if db_path is None:
        data_dir = Path(config.storage.data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(data_dir / "knowledge.db")
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session(engine=None) -> Session:
    if engine is None:
        engine = get_engine()
    return Session(engine)


def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
