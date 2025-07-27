import json
from unittest.mock import patch

from langchain_core.messages import AIMessage

from app.graph.nodes.structure_icp import structure_icp


@patch("app.graph.nodes.structure_icp.llm_client")
def test_structure_icp_generates_json(mock_llm, mock_graph_state, tmp_path):
    """
    Tests that the node correctly calls the LLM and structures the ICP text
    when no cache is present.
    """
    mock_structured_icp = {"key": "value", "sectors": ["Test Sector"]}
    # The LLM is expected to return an AIMessage whose content is a JSON string.
    mock_llm.invoke.return_value = AIMessage(content=json.dumps(mock_structured_icp))

    # Patch the cache path to use a temporary directory
    with patch("app.graph.nodes.structure_icp.Path") as mock_path_class:
        # Make the mock path object behave like a real Path object for this test
        mock_cache_path_instance = tmp_path / "structured_test_icp.json"
        mock_path_class.return_value.parent.parent.parent.parent.__truediv__.return_value = mock_cache_path_instance

        # Mock the exists method on the instance
        with patch.object(mock_cache_path_instance, "exists", return_value=False):
            result = structure_icp(mock_graph_state)

            # Assertions
            assert "structured_icp" in result
            assert result["structured_icp"] == mock_structured_icp
            mock_llm.invoke.assert_called_once()

            # Assert that the result was cached
            assert mock_cache_path_instance.exists()
            with open(mock_cache_path_instance, "r") as f:
                assert json.load(f) == mock_structured_icp


def test_structure_icp_uses_cache(mock_graph_state, tmp_path):
    """
    Tests that the node correctly uses the cached file if it exists
    and does not call the LLM.
    """
    mock_structured_icp = {"cached_key": "cached_value"}

    # Create a mock cache file
    cache_dir = tmp_path / "prompts"
    cache_dir.mkdir()
    cache_file = cache_dir / "structured_test_icp.json"
    with open(cache_file, "w") as f:
        json.dump(mock_structured_icp, f)

    with patch("app.graph.nodes.structure_icp.llm_client") as mock_llm:
        # Patch the path to point to our temp cache file
        with patch("app.graph.nodes.structure_icp.Path") as mock_path:
            mock_path.return_value.parent.parent.parent.parent.__truediv__.return_value = cache_file

            # This call should not use the LLM, so we don't need to mock its return value
            result = structure_icp(mock_graph_state)

            # Assertions
            assert "structured_icp" in result
            assert result["structured_icp"] == mock_structured_icp
            mock_llm.invoke.assert_not_called()
