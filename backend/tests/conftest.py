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


@pytest.fixture
def app_db(tmp_path):
    """Create a test DB and patch the app to use it."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.db.database import Base

    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    import app.api.project as proj_module
    original_get_session = proj_module._get_session

    def _test_session():
        return Session(engine)

    proj_module._get_session = _test_session
    yield engine
    proj_module._get_session = original_get_session
    engine.dispose()
