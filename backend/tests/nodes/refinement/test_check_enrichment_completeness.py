from app.graph.nodes.refinement.check_enrichment_completeness import (
    check_enrichment_completeness,
    ENRICHABLE_FIELDS,
    MAX_REFINEMENT_LOOPS,
)


def test_check_completeness_all_complete_returns_save(
    mock_graph_state, mock_candidate_lead
):
    """
    Tests that the node returns 'save' when all company data is complete.
    """
    enriched_data = {field: "some value" for field in ENRICHABLE_FIELDS}
    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": enriched_data}
    ]

    result = check_enrichment_completeness(mock_graph_state)
    assert result == "save"


def test_check_completeness_missing_data_returns_refine(
    mock_graph_state, mock_candidate_lead
):
    """
    Tests that the node returns 'refine' when some data is missing.
    """
    enriched_data = {ENRICHABLE_FIELDS[0]: "some value"}  # Missing other fields
    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": enriched_data}
    ]

    result = check_enrichment_completeness(mock_graph_state)
    assert result == "refine"


def test_check_completeness_max_loops_returns_save(
    mock_graph_state, mock_candidate_lead
):
    """
    Tests that the node returns 'save' if the max refinement loops are exceeded,
    even if data is missing.
    """
    mock_graph_state.refinement_attempts = MAX_REFINEMENT_LOOPS + 1
    enriched_data = {}  # All data missing
    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": enriched_data}
    ]

    result = check_enrichment_completeness(mock_graph_state)
    assert result == "save"
