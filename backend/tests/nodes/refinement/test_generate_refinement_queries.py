from app.graph.nodes.refinement.generate_refinement_queries import (
    ENRICHABLE_FIELDS,
    generate_refinement_queries,
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
    # Cost-optimized approach with tier-1 employee queries only:
    # - 5 regular fields (excluding employee_count): 5 queries
    # - employee_count field gets tier-1 treatment only:
    #   * 4 tier-1 high-performance patterns for NL (50-100% success rates)
    #   * Total employee queries: 4
    # - Total: 5 + 4 = 9 queries (down from 19 for cost efficiency)
    assert len(queries) == 9

    # Verify the top-priority company size pattern is included
    company_size_queries = [q for q in queries if "company size employees" in q]
    assert len(company_size_queries) == 1
    assert '"Test Health Clinic" company size employees' in queries

    # Verify other tier-1 patterns are included
    assert '"Test Health Clinic" linkedin company size' in queries
    assert '"Test Health Clinic" aantal medewerkers' in queries
