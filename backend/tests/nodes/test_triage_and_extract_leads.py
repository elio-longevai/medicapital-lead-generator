import asyncio
from unittest.mock import patch, AsyncMock
import pytest
from pydantic import ValidationError
from app.graph.nodes.triage_and_extract_leads import _triage_one_result


@pytest.mark.asyncio
@patch("app.graph.nodes.triage_and_extract_leads.llm_client")
async def test_triage_one_good_lead(mock_llm, mock_candidate_lead):
    """
    Tests that _triage_one_result correctly parses a good lead.
    """
    # Mock the chain used inside the function
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = mock_candidate_lead

    search_result = {
        "title": "Test Health Clinic",
        "url": "https://testclinic.com",
        "description": "A clinic",
    }

    # Execute
    result = await _triage_one_result(
        search_result, "NL", mock_chain, asyncio.Semaphore(1)
    )

    # Assert
    assert result is not None
    assert result.discovered_name == "Test Health Clinic"


@pytest.mark.asyncio
@patch("app.graph.nodes.triage_and_extract_leads.llm_client")
async def test_triage_one_bad_lead(mock_llm):
    """
    Tests that _triage_one_result rejects a bad lead (e.g., news article).
    The LLM chain is mocked to raise an exception, as it would for non-conforming output.
    """
    mock_chain = AsyncMock()
    mock_chain.ainvoke.side_effect = ValidationError.from_exception_data("Error", [])

    search_result = {
        "title": "News about clinics",
        "url": "https://news.com",
        "description": "A news story",
    }

    result = await _triage_one_result(
        search_result, "NL", mock_chain, asyncio.Semaphore(1)
    )

    assert result is None
