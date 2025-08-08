import mongomock
import pytest
from app.graph.state import CandidateLead, GraphState


@pytest.fixture(scope="function")
def test_mongo_db():
    """Fixture for an in-memory mock MongoDB database client."""
    client = mongomock.MongoClient()
    db = client.get_database("test_db")
    yield db
    client.close()


@pytest.fixture(autouse=True)
def mock_mongo_client(test_mongo_db, monkeypatch):
    """
    Mocks the MongoDB connection functions to return a mongomock instance
    for the duration of a test.
    """
    monkeypatch.setattr("app.db.mongodb.get_mongo_db", lambda: test_mongo_db)
    monkeypatch.setattr(
        "app.db.mongodb.get_mongo_collection",
        lambda name: test_mongo_db.get_collection(name),
    )
    monkeypatch.setattr("app.db.mongodb.get_mongo_client", lambda: test_mongo_db.client)


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
