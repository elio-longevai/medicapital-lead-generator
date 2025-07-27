import asyncio
from unittest.mock import AsyncMock, patch

from app.graph.nodes.refinement.execute_refinement_search import (
    execute_refinement_search,
)


@patch(
    "app.graph.nodes.refinement.execute_refinement_search.create_multi_provider_search_client"
)
@patch("app.graph.nodes.refinement.execute_refinement_search.asyncio.run")
def test_execute_refinement_search_for_one_company(
    mock_asyncio_run, mock_search_client_factory, mock_graph_state, mock_candidate_lead
):
    """
    Tests executing a refinement search for a single company.
    """
    # Setup
    queries = ['"Test Health Clinic" email', '"Test Health Clinic" phone']
    mock_graph_state.refinement_queries = {0: queries}
    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": {}}
    ]

    mock_results = [{"title": "Contact Us", "url": "https://test.com/contact"}]
    mock_provider = "tavily"

    # Mock the search client instance
    mock_search_client = AsyncMock()
    mock_search_client.search_async = AsyncMock(
        return_value=(mock_results, mock_provider)
    )
    mock_search_client_factory.return_value = mock_search_client

    mock_asyncio_run.side_effect = (
        lambda coro: asyncio.get_event_loop().run_until_complete(coro)
    )

    # Execute
    result = execute_refinement_search(mock_graph_state)

    # Assert
    assert "refinement_results" in result
    assert 0 in result["refinement_results"]
    # The helper function is called for each query, so we expect 2 results in the list
    assert len(result["refinement_results"][0]) == 2
    assert result["refinement_results"][0][0]["title"] == "Contact Us"
    assert mock_search_client.search_async.call_count == 2
