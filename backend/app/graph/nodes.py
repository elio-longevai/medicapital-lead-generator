from typing import TypedDict
from pathlib import Path
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.clients import llm_client, brave_client
from app.core.settings import settings
from app.db.models import Company
from app.db.session import SessionLocal
from app.graph.state import GraphState, CandidateLead
from app.graph import prompts
from app.services.company_name_normalizer import normalize_name
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMConfig,
)
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import json
import asyncio


class NodeResult(TypedDict):
    """Defines the structure for node return values to update the state."""

    pass


def structure_icp(state: GraphState) -> dict:
    """Parses the raw ICP text into a structured dictionary."""
    print("---NODE: Structuring ICP---")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.ICP_STRUCTURING_PROMPT,
        input_variables=["raw_icp_text"],
        partial_variables={"parser_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm_client | parser
    structured_icp = chain.invoke({"raw_icp_text": state.raw_icp_text})
    return {"structured_icp": structured_icp}


def generate_search_queries(state: GraphState) -> dict:
    """Generates strategic search queries based on the structured ICP."""
    print("---NODE: Generating Search Queries---")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.QUERY_GENERATION_PROMPT,
        input_variables=["structured_icp"],
        partial_variables={"parser_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm_client | parser
    queries = chain.invoke({"structured_icp": state.structured_icp})
    return {"search_queries": queries}


def execute_web_search(state: GraphState) -> dict:
    """Executes web searches with rate limiting (1 query per second)."""
    print(
        f"---NODE: Executing Web Search for {len(state.search_queries)} queries (Rate Limited: 1/sec)---"
    )

    all_results = []
    for i, query in enumerate(state.search_queries):
        print(f"  > [{i + 1}/{len(state.search_queries)}] Searching: '{query}'")

        # Execute search (synchronous)
        results = brave_client.search(query=query, country=state.target_country)
        all_results.extend(results)

        # Rate limiting: wait 1 second between requests (except for the last one)
        if i < len(state.search_queries) - 1:
            import time

            time.sleep(1.0)

    print(f"  > Found {len(all_results)} total results.")
    return {"search_results": all_results}


def triage_and_extract_leads(state: GraphState) -> dict:
    """Uses an LLM to triage search results."""
    print(f"---NODE: Triaging {len(state.search_results)} Search Results---")
    parser = PydanticOutputParser(pydantic_object=CandidateLead)
    prompt = PromptTemplate(
        template=prompts.LEAD_TRIAGE_PROMPT,
        input_variables=["title", "description", "source_url", "country"],
        partial_variables={"parser_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm_client | parser

    candidate_leads = []
    for i, result in enumerate(state.search_results):
        try:
            # Use synchronous invoke
            candidate = chain.invoke(
                {
                    "title": result["title"],
                    "description": result.get("description", ""),
                    "source_url": result["url"],
                    "country": state.target_country,
                }
            )
            print(
                f"  > [Result {i + 1}] PASS: Found potential lead '{candidate.discovered_name}'"
            )
            candidate_leads.append(candidate)
        except Exception:
            # Pydantic parser will raise an exception if the output is not valid JSON
            # or if the LLM outputs `null`, which we treat as a rejection.
            print(f"  > [Result {i + 1}] REJECTED: Not a B2B lead.")

    print(f"  > Completed triage. {len(candidate_leads)} potential leads identified.")
    return {"candidate_leads": candidate_leads}


def save_leads_to_db(state: GraphState) -> dict:
    """Saves unique, new leads to the database with enriched data."""
    leads_to_save = getattr(state, "enriched_companies", None) or [
        {"lead": lead, "enriched_data": None} for lead in state.candidate_leads
    ]

    print(
        f"---NODE: Saving {len(leads_to_save)} Candidate Leads to DB (with enrichment)---"
    )
    db = SessionLocal()
    saved_count = 0

    try:
        existing_names = {row[0] for row in db.query(Company.normalized_name).all()}

        for item in leads_to_save:
            lead = item["lead"]
            enriched_data = item.get("enriched_data")

            norm_name = normalize_name(lead.discovered_name)
            if not norm_name or norm_name in existing_names:
                print(f"  > SKIPPING Duplicate: '{lead.discovered_name}'")
                continue

            # Create new company with enriched data
            new_company = Company(
                discovered_name=lead.discovered_name,
                normalized_name=norm_name,
                country=lead.country,
                source_url=lead.source_url,
                primary_industry=lead.primary_industry,
                initial_reasoning=lead.initial_reasoning,
                status="discovered",
            )

            # Add enriched data if available
            if enriched_data:
                new_company.website_url = enriched_data.get("website_url")
                new_company.contact_email = enriched_data.get("contact_email")
                new_company.contact_phone = enriched_data.get("contact_phone")
                new_company.location_details = enriched_data.get("location_details")
                new_company.employee_count = enriched_data.get("employee_count")
                new_company.estimated_revenue = enriched_data.get("estimated_revenue")
                new_company.equipment_needs = enriched_data.get("equipment_needs")
                new_company.recent_news = enriched_data.get("recent_news")
                new_company.enriched_data = enriched_data.get("enriched_data")
                new_company.qualification_details = enriched_data.get(
                    "qualification_details"
                )

                # Calculate qualification score from details
                if enriched_data.get("qualification_details"):
                    qual_details = enriched_data["qualification_details"]
                    avg_score = sum(qual_details.values()) / len(qual_details)
                    new_company.qualification_score = int(avg_score)

            db.add(new_company)
            existing_names.add(norm_name)  # Add to set to handle intra-batch duplicates
            saved_count += 1
            print(
                f"  > ADDING New Lead: '{lead.discovered_name}' {'(enriched)' if enriched_data else ''}"
            )

        db.commit()
        print(f"  > Successfully saved {saved_count} new leads to database.")
    except Exception as e:
        db.rollback()
        print(f"  > Database error: {e}")
        return {"error_message": str(e)}
    finally:
        db.close()

    return {"newly_saved_leads_count": saved_count}


def scrape_and_enrich_companies(state: GraphState) -> dict:
    """Scrapes company websites using Crawl4AI and enriches data with LLM analysis."""
    print(f"---NODE: Scraping and Enriching {len(state.candidate_leads)} Companies---")

    # Load the enrichment prompt
    enrichment_prompt_path = (
        Path(__file__).parent.parent.parent / "prompts" / "company_enrichment.txt"
    )
    try:
        enrichment_prompt = enrichment_prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print("Warning: company_enrichment.txt not found, skipping enrichment")
        return {"enriched_companies": []}

    enriched_companies = []

    # Process each candidate lead
    for i, lead in enumerate(state.candidate_leads):
        print(
            f"  > [{i + 1}/{len(state.candidate_leads)}] Scraping: {lead.discovered_name}"
        )

        try:
            # Run the async scraping in a sync context
            enriched_data = asyncio.run(
                _scrape_company_website(lead, enrichment_prompt)
            )
            enriched_companies.append({"lead": lead, "enriched_data": enriched_data})
            print(f"    ✓ Successfully enriched data for {lead.discovered_name}")

        except Exception as e:
            print(f"    ✗ Failed to scrape {lead.discovered_name}: {str(e)}")
            # Add the lead without enrichment
            enriched_companies.append({"lead": lead, "enriched_data": None})

    print(
        f"  > Completed scraping. {len([c for c in enriched_companies if c['enriched_data']])} companies enriched."
    )
    return {"enriched_companies": enriched_companies}


async def _scrape_company_website(lead: CandidateLead, enrichment_prompt: str) -> dict:
    """Helper function to scrape a single company website using Crawl4AI."""

    # Configure browser for headless operation
    browser_config = BrowserConfig(headless=True, verbose=False)

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
            instruction=enrichment_prompt.format(
                website_content="{content}",  # This will be filled by Crawl4AI
                company_name=lead.discovered_name,
                industry=lead.primary_industry,
                country=lead.country,
            ),
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
                print(f"    Failed to scrape {url}: {str(e)}")
                continue

    # If all URLs failed, return None
    return None
