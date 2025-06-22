from unittest.mock import patch
from app.graph.nodes.save_leads_to_db import save_leads_to_db
from app.db.models import Company
from app.services.company_name_normalizer import normalize_name


@patch("app.graph.nodes.save_leads_to_db.SessionLocal")
def test_save_new_lead(
    mock_session_local, test_db, mock_graph_state, mock_candidate_lead
):
    """
    Tests saving a single new, enriched lead to the database.
    """
    mock_session_local.return_value = test_db

    enriched_data = {
        "contact_email": "contact@testclinic.com",
        "employee_count": "10-50",
    }
    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": enriched_data}
    ]

    # Execute
    result = save_leads_to_db(mock_graph_state)

    # Assertions
    assert result["newly_saved_leads_count"] == 1

    saved_company = test_db.query(Company).first()
    assert saved_company is not None
    assert saved_company.discovered_name == mock_candidate_lead.discovered_name
    assert saved_company.contact_email == "contact@testclinic.com"
    assert saved_company.employee_count == "10-50"
    assert saved_company.icp_name == mock_graph_state.icp_name


@patch("app.graph.nodes.save_leads_to_db.SessionLocal")
def test_skip_duplicate_lead(
    mock_session_local, test_db, mock_graph_state, mock_candidate_lead
):
    """
    Tests that a lead with a name that normalizes to an existing name is not saved.
    """
    mock_session_local.return_value = test_db

    # Pre-populate the DB with a company
    existing_company = Company(
        normalized_name=normalize_name("Test Health Clinic"),
        discovered_name="Test Health Clinic Inc.",
        source_url="https://existing.com",
        country="NL",
        initial_reasoning="Exists",
    )
    test_db.add(existing_company)
    test_db.commit()

    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": {}}
    ]

    # Execute
    result = save_leads_to_db(mock_graph_state)

    # Assert
    assert result["newly_saved_leads_count"] == 0
    company_count = test_db.query(Company).count()
    assert company_count == 1
