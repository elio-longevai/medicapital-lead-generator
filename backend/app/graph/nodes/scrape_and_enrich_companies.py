import asyncio
import json
import logging
from pathlib import Path

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    LLMConfig,
    CacheMode,
)
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from app.core.settings import settings
from app.graph.state import CandidateLead, GraphState

logger = logging.getLogger(__name__)


async def _scrape_company_website(lead: CandidateLead, enrichment_prompt: str) -> dict:
    """Helper function to scrape a single company website using Crawl4AI."""

    # Configure browser for headless operation
    browser_config = BrowserConfig(headless=True, verbose=False)

    # Prepare the instruction by replacing placeholders
    instruction = enrichment_prompt.replace("{company_name}", lead.discovered_name)
    instruction = instruction.replace("{industry}", lead.primary_industry)
    instruction = instruction.replace("{country}", lead.country)
    # Keep {website_content} for Crawl4AI to replace with actual content

    # Configure the crawler
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        word_count_threshold=50,  # Only process pages with substantial content
        exclude_external_links=True,
        extraction_strategy=LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="google/gemini-2.5-flash-preview-05-20",
                api_token=settings.GOOGLE_API_KEY,
            ),
            schema=None,  # We'll use the prompt directly
            extraction_type="block",
            instruction=instruction,
        ),
    )

    # Try to scrape the source URL first, then look for official website
    urls_to_try = [lead.source_url]

    # Try to find official website URL by looking for common patterns
    if not any(
        domain in lead.source_url.lower() for domain in [".com", ".nl", ".be", ".org"]
    ):
        # If source URL doesn't look like a company website, try to construct one
        company_domain = lead.discovered_name.lower().replace(" ", "").replace("-", "")
        urls_to_try.extend(
            [
                f"https://www.{company_domain}.com",
                f"https://www.{company_domain}.nl",
                f"https://www.{company_domain}.be",
            ]
        )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls_to_try:
            try:
                result = await crawler.arun(url=url, config=run_config)

                if result.success and result.extracted_content:
                    # Parse the JSON response from the LLM
                    try:
                        enriched_data = json.loads(result.extracted_content)
                        # Add the successful URL to the data
                        enriched_data["website_url"] = url
                        return enriched_data
                    except json.JSONDecodeError:
                        # If JSON parsing fails, create a basic structure
                        logger.warning(
                            f"    - Could not parse JSON from LLM for {url}, using raw output."
                        )
                        return {
                            "website_url": url,
                            "enriched_data": result.extracted_content[
                                :500
                            ],  # Truncate if too long
                            "contact_email": None,
                            "contact_phone": None,
                            "location_details": None,
                            "employee_count": None,
                            "estimated_revenue": None,
                            "equipment_needs": None,
                            "recent_news": None,
                            "qualification_details": {
                                "financial_stability": 75,
                                "equipment_need": 70,
                                "timing": 65,
                                "decision_authority": 70,
                            },
                        }

            except Exception as e:
                logger.error(f"    - Failed to scrape {url}: {str(e)}")
                continue

    # If all URLs failed, return None
    return None


def scrape_and_enrich_companies(state: GraphState) -> dict:
    """Scrapes company websites using Crawl4AI and enriches data with LLM analysis."""
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
        logger.warning(
            "⚠️ Warning: company_enrichment.txt not found, skipping enrichment"
        )
        # Still return a valid structure for the graph to continue
        return {
            "enriched_companies": [
                {"lead": lead, "enriched_data": None} for lead in state.candidate_leads
            ]
        }

    enriched_companies = []

    # Process each candidate lead
    for i, lead in enumerate(state.candidate_leads):
        logger.info(
            f"  > [{i + 1}/{len(state.candidate_leads)}] Scraping: {lead.discovered_name} ({lead.source_url})"
        )

        try:
            # Run the async scraping in a sync context
            enriched_data = asyncio.run(
                _scrape_company_website(lead, enrichment_prompt)
            )
            enriched_companies.append({"lead": lead, "enriched_data": enriched_data})
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
                f"    ✗ Failed to scrape {lead.discovered_name}: {str(e)}",
                exc_info=True,
            )
            # Add the lead without enrichment
            enriched_companies.append({"lead": lead, "enriched_data": None})

    logger.info(
        f"  > Completed scraping. {len([c for c in enriched_companies if c['enriched_data']])} companies enriched."
    )
    return {"enriched_companies": enriched_companies}
