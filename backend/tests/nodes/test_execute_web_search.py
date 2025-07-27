import pytest
from unittest.mock import patch, AsyncMock
import unittest
from app.graph.nodes.execute_web_search import execute_web_search


@pytest.mark.asyncio
@patch("asyncio.to_thread")
@patch("app.core.clients.create_multi_provider_search_client")
async def test_execute_web_search_for_one_query(
    mock_search_client_factory, mock_to_thread, mock_graph_state
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

    # Mock the to_thread call for query tracking
    mock_to_thread.return_value = AsyncMock()

    # Execute
    result = await execute_web_search(mock_graph_state)

    # Assert
    assert "search_results" in result
    assert result["search_results"] == mock_results
    mock_search_client.search_async.assert_called_once_with(
        "test query", mock_graph_state.target_country, unittest.mock.ANY
    )
    # Check that query tracking was called
    mock_to_thread.assert_called_once()
