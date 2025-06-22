from unittest.mock import patch
from app.graph.nodes.get_used_queries import get_used_queries
from app.services.search_query_service import SearchQueryService


@patch("app.graph.nodes.get_used_queries.SearchQueryService")
def test_get_used_queries_fetches_from_db(
    mock_query_service_class, test_db, mock_graph_state
):
    """
    Tests that the node correctly fetches used queries for a specific country.
    """
    # Setup: Add a query to the test database
    query_text = "test query for NL"
    country = "NL"
    with SearchQueryService(test_db) as service:
        service.mark_query_as_used(query_text, country)

    # Mock the service instance used by the node to use our test_db
    mock_service_instance = SearchQueryService(test_db)
    mock_query_service_class.return_value.__enter__.return_value = mock_service_instance

    # Execute the node
    result = get_used_queries(mock_graph_state)

    # Assertions
    assert "used_queries" in result
    assert len(result["used_queries"]) == 1
    assert result["used_queries"][0] == query_text
