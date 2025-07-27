import asyncio
import logging
from itertools import islice
from pathlib import Path

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
)

from app.core.clients import llm_client
from app.graph.nodes.schemas import EnrichedCompanyData
from app.graph.state import CandidateLead, GraphState

logger = logging.getLogger(__name__)


def _batch(iterable, size):
    """Yields successive n-sized chunks from an iterable."""
    it = iter(iterable)
    while True:
        chunk = tuple(islice(it, size))
        if not chunk:
            return
        yield chunk


async def _scrape_company_website(
    lead: CandidateLead, enrichment_prompt: str, json_llm_client
) -> dict | None:
    """
    Scrapes a company website to get its text content, then uses an LLM to extract
    structured information.
    """
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        word_count_threshold=50,
        exclude_external_links=True,
    )

    urls_to_try = [lead.source_url]
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

    scraped_content = None
    successful_url = None
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls_to_try:
            try:
                result = await crawler.arun(url=url, config=run_config)
                if result.success and result.markdown and result.markdown.raw_markdown:
                    scraped_content = result.markdown.raw_markdown
                    successful_url = url
                    logger.info(f"    ✓ Successfully scraped content from {url}")
                    break
            except Exception as e:
                logger.error(f"    - Failed during scraping of {url}: {str(e)}")
                continue

    if not scraped_content:
        logger.warning(f"    - Could not scrape any content for {lead.discovered_name}")
        return None

    logger.info(f"    > Extracting information for {lead.discovered_name} using LLM...")

    final_prompt = enrichment_prompt.replace("{company_name}", lead.discovered_name)
    final_prompt = final_prompt.replace("{industry}", lead.primary_industry)
    final_prompt = final_prompt.replace("{country}", lead.country)
    final_prompt = final_prompt.replace("{website_content}", scraped_content[:15000])

    try:
        response = await asyncio.wait_for(
            json_llm_client.ainvoke(final_prompt), timeout=60.0
        )
        enriched_data = response.model_dump()

        if isinstance(enriched_data, dict):
            enriched_data["website_url"] = successful_url
            return enriched_data

        logger.warning(
            f"    - LLM did not return a valid dictionary for {lead.discovered_name}"
        )
        return None
    except asyncio.TimeoutError:
        logger.error(
            f"    - Timeout occurred during LLM extraction for {lead.discovered_name}"
        )
        return None
    except Exception as e:
        logger.error(f"    - Failed LLM extraction for {lead.discovered_name}: {e}")
        return None


async def _scrape_with_semaphore(
    semaphore: asyncio.Semaphore,
    lead: CandidateLead,
    enrichment_prompt: str,
    json_llm_client,
):
    """
    Wrapper to control concurrency and ensure each task is self-contained.
    It returns the lead along with the scraping result.
    """
    async with semaphore:
        enriched_data = await _scrape_company_website(
            lead, enrichment_prompt, json_llm_client
        )
        return lead, enriched_data


async def scrape_and_enrich_companies(state: GraphState) -> dict:
    """Scrapes company websites and enriches data with LLM analysis in parallel."""
    logger.info(
        f"---NODE: Scraping and Enriching {len(state.candidate_leads)} Companies---"
    )
    if not state.candidate_leads:
        return {"enriched_companies": []}

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

    CONCURRENCY_LIMIT = 5
    BATCH_SIZE = 50
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    final_enriched_companies = []
    json_llm_client = llm_client.with_structured_output(EnrichedCompanyData)

    for lead_batch in _batch(state.candidate_leads, BATCH_SIZE):
        tasks = [
            asyncio.create_task(
                _scrape_with_semaphore(
                    semaphore, lead, enrichment_prompt, json_llm_client
                )
            )
            for lead in lead_batch
        ]

        for future in asyncio.as_completed(tasks):
            try:
                lead, enriched_data = await future
                final_enriched_companies.append(
                    {"lead": lead, "enriched_data": enriched_data}
                )
                if enriched_data:
                    logger.info(
                        f"    ✓ Successfully enriched data for {lead.discovered_name}"
                    )
                else:
                    logger.warning(
                        f"    - No enrichment data returned for {lead.discovered_name}"
                    )
            except Exception as e:
                # This exception is caught if the task itself fails unexpectedly.
                # Specific errors (like timeout) are handled within the task.
                logger.error(f"    - A scraping task failed or was cancelled: {e}")

    logger.info(
        f"  > Completed scraping. {len([c for c in final_enriched_companies if c['enriched_data']])} companies enriched."
    )
    return {"enriched_companies": final_enriched_companies}
