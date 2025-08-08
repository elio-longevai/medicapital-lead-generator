from app.db.repositories import SearchQueryRepository
from app.graph.nodes.get_used_queries import get_used_queries


def test_get_used_queries_fetches_from_db(test_mongo_db, mock_graph_state):
    """
    Tests that the node correctly fetches used queries for a specific country.
    """
    # Setup: Add a query to the mock database
    query_text = "test query for NL"
    country = "NL"
    repo = SearchQueryRepository()
    repo.mark_query_as_used(query_text, country)

    # Execute the node
    result = get_used_queries(mock_graph_state)

    # Assertions
    assert "used_queries" in result
    assert len(result["used_queries"]) == 1
    assert result["used_queries"][0] == query_text
