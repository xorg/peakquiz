import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.auth import get_current_user, get_optional_user
from app.db.database import Base, get_db
from app.db.models import Guess, Peak, Picture, User  # noqa: F401 — registers all models
from app.main import app


@pytest.fixture
def db():
    # StaticPool keeps a single connection so create_all and the session share the same DB.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def clear_quiz_sessions():
    """Reset in-memory session store between tests."""
    from app.api.routes import quiz as quiz_module
    quiz_module._sessions.clear()
    yield
    quiz_module._sessions.clear()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_user(db):
    user = User(id="test-user-1", username="Test User", best_score=0)
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def auth_client(client, auth_user):
    app.dependency_overrides[get_current_user] = lambda: auth_user
    app.dependency_overrides[get_optional_user] = lambda: auth_user
    yield client


@pytest.fixture
def peaks(db):
    """Seed 12 peaks with CDN images — enough for initial batch (10) plus extras."""
    result = []
    for i in range(12):
        peak = Peak(name=f"Test Peak {i}", elevation=3000 + i * 100, region="Switzerland")
        db.add(peak)
        db.flush()
        db.add(Picture(
            peak_id=peak.id,
            original_url=f"http://example.com/peak{i}.jpg",
            cdn_url=f"https://res.cloudinary.com/test/image/upload/f_auto,q_auto/{i}",
        ))
        result.append(peak)
    db.commit()
    return result
