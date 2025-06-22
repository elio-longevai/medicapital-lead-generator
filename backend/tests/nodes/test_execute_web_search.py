import asyncio
from unittest.mock import patch, AsyncMock
import unittest
from app.graph.nodes.execute_web_search import execute_web_search


@patch("app.graph.nodes.execute_web_search.SearchQueryService")
@patch("app.graph.nodes.execute_web_search.create_multi_provider_search_client")
@patch("app.graph.nodes.execute_web_search.asyncio.run")
def test_execute_web_search_for_one_query(
    mock_asyncio_run, mock_search_client_factory, mock_query_service, mock_graph_state
):
    """
    Tests executing a single web search query.
    """
    # Setup
    mock_graph_state.search_queries = ["test query"]
    mock_results = [{"title": "Test Result", "url": "https://test.com"}]
    mock_provider = "brave"

    # Mock the search client instance
    mock_search_client = AsyncMock()
    mock_search_client.search_async = AsyncMock(
        return_value=(mock_results, mock_provider)
    )
    mock_search_client_factory.return_value = mock_search_client

    # Mock asyncio.run to just execute the coroutine in the current event loop
    mock_asyncio_run.side_effect = (
        lambda coro: asyncio.get_event_loop().run_until_complete(coro)
    )

    # Execute
    result = execute_web_search(mock_graph_state)

    # Assert
    assert "search_results" in result
    assert result["search_results"] == mock_results
    mock_search_client.search_async.assert_called_once_with(
        "test query", mock_graph_state.target_country, unittest.mock.ANY
    )
    # Check that query usage was marked
    mock_query_service.return_value.__enter__.return_value.mark_queries_as_used_batch.assert_called_once()
