import json
from unittest.mock import patch

from langchain_core.messages import AIMessage

from app.graph.nodes.generate_search_queries import generate_search_queries


@patch("app.graph.nodes.generate_search_queries.llm_client")
def test_generate_search_queries_with_mock_llm(mock_llm, mock_graph_state):
    """
    Tests that the node generates search queries via an LLM call.
    """
    mock_queries = ["query 1", "query 2"]
    mock_llm.invoke.return_value = AIMessage(content=json.dumps(mock_queries))
    mock_graph_state.structured_icp = {"some": "data"}
    mock_graph_state.used_queries = ["old query"]

    # Execute
    result = generate_search_queries(mock_graph_state)

    # Assert
    assert "search_queries" in result
    assert result["search_queries"] == mock_queries
    mock_llm.invoke.assert_called_once()

    # Check that used_queries were passed to the LLM
    invoke_args = mock_llm.invoke.call_args[0][0]
    assert (
        json.dumps(mock_graph_state.used_queries, indent=2)
        in invoke_args["used_queries"]
    )
