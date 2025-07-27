import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.graph.state import CandidateLead, GraphState

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Fixture for an in-memory database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_graph_state():
    """Provides a basic GraphState object for tests."""
    return GraphState(
        icp_name="test_icp",
        raw_icp_text="Some raw ICP text about test companies in the Healthcare industry.",
        target_country="NL",
        queries_per_icp=5,
    )


@pytest.fixture
def mock_candidate_lead():
    """Provides a single candidate lead for enrichment and saving tests."""
    return CandidateLead(
        discovered_name="Test Health Clinic",
        source_url="https://testclinic.com",
        country="NL",
        primary_industry="Healthcare",
        initial_reasoning="A clinic that likely needs medical equipment.",
    )
