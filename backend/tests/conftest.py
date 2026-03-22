import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.db.database import Base
from app.config import config


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """Redirect data storage to a temp directory."""
    for sub in ["uploads", "projects", "examples"]:
        (tmp_path / sub).mkdir()
    monkeypatch.setattr(config.storage, "data_dir", str(tmp_path))
    return tmp_path


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
