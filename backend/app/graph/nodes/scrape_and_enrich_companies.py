import asyncio
import logging
from pathlib import Path

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)

from app.core.clients import llm_client
from app.graph.state import CandidateLead, GraphState
from app.graph.nodes.schemas import EnrichedCompanyData

logger = logging.getLogger(__name__)


async def _scrape_company_website(
    lead: CandidateLead, enrichment_prompt: str
) -> dict | None:
    """
    Scrapes a company website to get its text content, then uses an LLM to extract
    structured information.
    """
    # 1. Configure crawler to only scrape content, not extract with an LLM yet.
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        word_count_threshold=50,
        exclude_external_links=True,
    )

    urls_to_try = [lead.source_url]
    # Try to find official website URL if the source URL is not a standard one
    if not any(
        domain in lead.source_url.lower() for domain in [".com", ".nl", ".be", ".org"]
    ):
        company_domain = lead.discovered_name.lower().replace(" ", "").replace("-", "")
        urls_to_try.extend(
            [
                f"https://www.{company_domain}.com",
                f"https://www.{company_domain}.nl",
                f"https://www.{company_domain}.be",
            ]
        )

    # 2. Scrape the website to get raw content
    scraped_content = None
    successful_url = None
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls_to_try:
            try:
                result = await crawler.arun(url=url, config=run_config)
                # Use the markdown content which is cleaner for LLMs
                if result.success and result.markdown and result.markdown.raw_markdown:
                    scraped_content = result.markdown.raw_markdown
                    successful_url = url
                    logger.info(f"    ✓ Successfully scraped content from {url}")
                    break  # Stop on first successful scrape
            except Exception as e:
                logger.error(f"    - Failed during scraping of {url}: {str(e)}")
                continue

    if not scraped_content:
        logger.warning(f"    - Could not scrape any content for {lead.discovered_name}")
        return None

    # 3. Use LLM to extract structured data from the scraped content
    logger.info(f"    > Extracting information for {lead.discovered_name} using LLM...")

    # Prepare the prompt for the LLM
    final_prompt = enrichment_prompt.replace("{company_name}", lead.discovered_name)
    final_prompt = final_prompt.replace("{industry}", lead.primary_industry)
    final_prompt = final_prompt.replace("{country}", lead.country)
    # Truncate content to avoid exceeding LLM context window limits
    final_prompt = final_prompt.replace("{website_content}", scraped_content[:15000])

    try:
        # Use a client configured for JSON mode to improve reliability
        json_llm_client = llm_client.with_structured_output(EnrichedCompanyData)
        response = await asyncio.to_thread(json_llm_client.invoke, final_prompt)

        # The response should already be a dictionary when using structured_output
        enriched_data = response.model_dump()

        if isinstance(enriched_data, dict):
            enriched_data["website_url"] = successful_url
            return enriched_data

        logger.warning(
            f"    - LLM did not return a valid dictionary for {lead.discovered_name}"
        )
        return None

    except Exception as e:
        logger.error(f"    - Failed LLM extraction for {lead.discovered_name}: {e}")
        return None


def scrape_and_enrich_companies(state: GraphState) -> dict:
    """Scrapes company websites and enriches data with LLM analysis in parallel."""
    logger.info(
        f"---NODE: Scraping and Enriching {len(state.candidate_leads)} Companies---"
    )

    # Load the enrichment prompt
    enrichment_prompt_path = (
        Path(__file__).parent.parent.parent.parent
        / "prompts"
        / "company_enrichment.txt"
    )
    try:
        enrichment_prompt = enrichment_prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("⚠️ company_enrichment.txt not found, skipping enrichment")
        return {
            "enriched_companies": [
                {"lead": lead, "enriched_data": None} for lead in state.candidate_leads
            ]
        }

    async def _run_enrichment():
        # Create a list of async tasks to run concurrently
        tasks = [
            _scrape_company_website(lead, enrichment_prompt)
            for lead in state.candidate_leads
        ]
        enriched_results = await asyncio.gather(*tasks)

        # Pair original leads with their new, enriched data
        final_enriched_companies = []
        for lead, data in zip(state.candidate_leads, enriched_results):
            final_enriched_companies.append({"lead": lead, "enriched_data": data})
            if data:
                logger.info(
                    f"    ✓ Successfully enriched data for {lead.discovered_name}"
                )
            else:
                logger.warning(
                    f"    - No enrichment data returned for {lead.discovered_name}"
                )
        return final_enriched_companies

    # Run the entire async enrichment process
    enriched_companies = asyncio.run(_run_enrichment())

    logger.info(
        f"  > Completed scraping. {len([c for c in enriched_companies if c['enriched_data']])} companies enriched."
    )
    return {"enriched_companies": enriched_companies}
