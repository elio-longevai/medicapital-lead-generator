import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.graph.nodes.scrape_and_enrich_companies import scrape_and_enrich_companies


@patch("app.graph.nodes.scrape_and_enrich_companies.llm_client")
@patch("app.graph.nodes.scrape_and_enrich_companies.AsyncWebCrawler")
@patch("app.graph.nodes.scrape_and_enrich_companies.asyncio.run")
def test_scrape_and_enrich_one_company(
    mock_asyncio_run,
    mock_crawler_class,
    mock_llm_client,
    mock_graph_state,
    mock_candidate_lead,
):
    """
    Tests the successful scraping and enrichment of a single company.
    """
    # Setup Mocks
    mock_graph_state.candidate_leads = [mock_candidate_lead]
    mock_enriched_data = {
        "contact_email": "test@testclinic.com",
        "company_description": "A test company.",
    }

    # Mock the crawler to return successful content
    mock_crawler_instance = AsyncMock()
    mock_crawler_result = AsyncMock()
    mock_crawler_result.success = True
    mock_crawler_result.markdown.raw_markdown = "Website content with email."
    mock_crawler_instance.arun.return_value = mock_crawler_result
    mock_crawler_class.return_value.__aenter__.return_value = mock_crawler_instance

    # Mock the LLM to return structured data from a sync call
    mock_enriched_obj = MagicMock()
    mock_enriched_obj.model_dump.return_value = mock_enriched_data

    mock_json_llm = MagicMock()
    mock_json_llm.invoke.return_value = mock_enriched_obj
    mock_llm_client.with_structured_output.return_value = mock_json_llm

    # Mock asyncio.run
    mock_asyncio_run.side_effect = (
        lambda coro: asyncio.get_event_loop().run_until_complete(coro)
    )

    # Patch the prompt file reading
    with patch("builtins.open", unittest.mock.mock_open(read_data="Enrichment prompt")):
        # Execute
        result = scrape_and_enrich_companies(mock_graph_state)

    # Assertions
    assert "enriched_companies" in result
    enriched_company = result["enriched_companies"][0]
    assert enriched_company["lead"] == mock_candidate_lead
    assert enriched_company["enriched_data"]["contact_email"] == "test@testclinic.com"
    assert enriched_company["enriched_data"]["company_description"] == "A test company."
