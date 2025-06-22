from app.graph.nodes.refinement.generate_refinement_queries import (
    generate_refinement_queries,
    ENRICHABLE_FIELDS,
)


def test_generate_for_partially_enriched_company(mock_graph_state, mock_candidate_lead):
    """
    Tests generating queries only for the fields that are missing.
    """
    enriched_data = {
        "contact_phone": "12345",
        "employee_count": "10",
        # Missing contact_email, location_details, etc.
    }
    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": enriched_data}
    ]

    result = generate_refinement_queries(mock_graph_state)

    queries = result["refinement_queries"][0]
    expected_missing_count = len(ENRICHABLE_FIELDS) - 2
    assert len(queries) == expected_missing_count
    assert '"Test Health Clinic" e-mailadres' in queries
    assert '"Test Health Clinic" telefoonnummer' not in queries


def test_generate_for_unenriched_company(mock_graph_state, mock_candidate_lead):
    """
    Tests that queries are generated for all enrichable fields if no data exists.
    """
    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": None}
    ]

    result = generate_refinement_queries(mock_graph_state)

    queries = result["refinement_queries"][0]
    assert len(queries) == len(ENRICHABLE_FIELDS)
