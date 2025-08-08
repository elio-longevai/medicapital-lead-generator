from app.graph.nodes.save_leads_to_db import save_leads_to_db
from app.services.company_name_normalizer import normalize_name
from app.db.repositories import CompanyRepository


def test_save_new_lead(test_mongo_db, mock_graph_state, mock_candidate_lead):
    """
    Tests saving a single new, enriched lead to the database.
    """
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

    repo = CompanyRepository()
    saved_company = repo.find_by_normalized_name(
        normalize_name(mock_candidate_lead.discovered_name)
    )
    assert saved_company is not None
    # Note: contact_email is no longer a top-level field, it's inside contact_persons
    assert saved_company.get("employee_count") == "10-50"
    assert saved_company["icp_name"] == mock_graph_state.icp_name


def test_skip_duplicate_lead(test_mongo_db, mock_graph_state, mock_candidate_lead):
    """
    Tests that a lead with a name that normalizes to an existing name is not saved.
    """
    repo = CompanyRepository()
    # Pre-populate the DB with a company
    existing_company = {
        "normalized_name": normalize_name("Test Health Clinic"),
        "discovered_name": "Test Health Clinic Inc.",
        "source_url": "https://existing.com",
        "country": "NL",
        "initial_reasoning": "Exists",
    }
    repo.collection.insert_one(existing_company)

    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": {}}
    ]

    # Execute
    result = save_leads_to_db(mock_graph_state)

    # Assert
    assert result["newly_saved_leads_count"] == 0
    company_count = repo.collection.count_documents({})
    assert company_count == 1
