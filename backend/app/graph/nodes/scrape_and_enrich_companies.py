import asyncio
import logging
from pathlib import Path
from itertools import islice

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
    # 1. Configure crawler to only scrape content, not extract with an LLM yet.
    # Consider disabling cache in production if URLs are always unique
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,  # Consider CacheMode.DISABLED in production
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
        response = await json_llm_client.ainvoke(final_prompt)
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


async def _scrape_with_semaphore(
    semaphore: asyncio.Semaphore,
    lead: CandidateLead,
    enrichment_prompt: str,
    json_llm_client,
):
    """Wrapper to control concurrency with a semaphore."""
    async with semaphore:
        return await _scrape_company_website(lead, enrichment_prompt, json_llm_client)


async def scrape_and_enrich_companies(state: GraphState) -> dict:
    """Scrapes company websites and enriches data with LLM analysis in parallel."""
    logger.info(
        f"---NODE: Scraping and Enriching {len(state.candidate_leads)} Companies---"
    )
    if not state.candidate_leads:
        return {"enriched_companies": []}

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

    # Limit concurrency to avoid resource exhaustion
    CONCURRENCY_LIMIT = 5
    BATCH_SIZE = 50  # Process 50 companies at a time
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    final_enriched_companies = []

    # Create the structured LLM client once to be reused.
    json_llm_client = llm_client.with_structured_output(EnrichedCompanyData)

    # Process leads in batches to control memory usage for task creation
    for lead_batch in _batch(state.candidate_leads, BATCH_SIZE):
        # Create a list of async tasks to run concurrently for the current batch
        task_to_lead = {
            asyncio.create_task(
                _scrape_with_semaphore(
                    semaphore, lead, enrichment_prompt, json_llm_client
                )
            ): lead
            for lead in lead_batch
        }

        # Process tasks as they complete to manage memory and log progressively
        for task in asyncio.as_completed(task_to_lead):
            lead = task_to_lead.pop(task)  # Pop the lead mapping to prevent leaks
            try:
                enriched_data = await task
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
                logger.error(
                    f"    - Task for {lead.discovered_name} failed with error: {e}"
                )
                # Append a failure record to maintain list integrity
                final_enriched_companies.append({"lead": lead, "enriched_data": None})

    logger.info(
        f"  > Completed scraping. {len([c for c in final_enriched_companies if c['enriched_data']])} companies enriched."
    )
    return {"enriched_companies": final_enriched_companies}
