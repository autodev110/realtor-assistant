import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.storage.models import Base, Client


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, future=True, autocommit=False, autoflush=False)
    with TestingSession() as session:
        yield session


@pytest.fixture
def client(session):
    client = Client(
        id=uuid.uuid4(),
        full_name="Test Client",
        email="client@example.com",
        prefs={"price_min": 300000, "price_max": 550000, "beds_min": 3},
        tone_profile={"formality": "conversational", "signoff": "Cheers"},
    )
    session.add(client)
    session.commit()
    return client
