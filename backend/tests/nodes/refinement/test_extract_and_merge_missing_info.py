from unittest.mock import patch
from langchain_core.messages import AIMessage
from app.graph.nodes.refinement.extract_and_merge_missing_info import (
    extract_and_merge_missing_info,
)


@patch("app.graph.nodes.refinement.extract_and_merge_missing_info.llm_client")
def test_extract_and_merge_one_field(mock_llm, mock_graph_state, mock_candidate_lead):
    """
    Tests that the node can extract a single missing piece of information and merge it.
    """
    # Setup: Company is missing an email
    mock_graph_state.enriched_companies = [
        {"lead": mock_candidate_lead, "enriched_data": {"contact_phone": "123"}}
    ]
    mock_graph_state.refinement_results = {
        0: [{"description": "Our email is contact@testclinic.com"}]
    }

    # Mock the LLM chain to return the email when asked
    # The chain is: prompt | llm | StrOutputParser()
    # The mock needs to return a message object for the parser to work correctly.
    async def mock_ainvoke(args):
        if args.get("field_name") == "contact_email":
            return AIMessage(content="contact@testclinic.com")
        return AIMessage(content="null")

    mock_llm.ainvoke.side_effect = mock_ainvoke

    # Execute
    result = extract_and_merge_missing_info(mock_graph_state)

    # Assert
    final_data = result["enriched_companies"][0]["enriched_data"]
    assert "contact_email" in final_data
    assert final_data["contact_email"] == "contact@testclinic.com"
    # Ensure existing data is kept
    assert final_data["contact_phone"] == "123"
