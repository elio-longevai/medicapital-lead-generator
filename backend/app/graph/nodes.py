from typing import TypedDict
from pathlib import Path
from langchain_core.output_parsers import (
    JsonOutputParser,
    PydanticOutputParser,
)
from langchain_core.prompts import PromptTemplate

from app.core.clients import (
    llm_client,
    brave_client,
    serper_client,
    tavily_client,
    firecrawl_client,
)
from app.core.settings import settings
from app.db.models import Company
from app.db.session import SessionLocal
from app.graph.state import GraphState, CandidateLead
from app.graph import prompts
from app.services.company_name_normalizer import normalize_name
from app.services.search_query_service import SearchQueryService
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
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NodeResult(TypedDict):
    """Defines the structure for node return values to update the state."""

    pass


def structure_icp(state: GraphState) -> dict:
    """Parses the raw ICP text into a structured dictionary. Caches result to a file."""
    logger.info("---NODE: Structuring ICP---")

    # Define cache path
    cache_path = Path(__file__).parent.parent.parent / "prompts" / "structured_icp.json"

    # Check if cached file exists
    if cache_path.exists():
        logger.info(f"  > Found cached structured ICP at {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            structured_icp = json.load(f)
        return {"structured_icp": structured_icp}

    # If not cached, generate it
    logger.info("  > No cache found. Generating structured ICP from raw text...")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.ICP_STRUCTURING_PROMPT,
        input_variables=["raw_icp_text"],
        partial_variables={"parser_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm_client | parser
    structured_icp = chain.invoke({"raw_icp_text": state.raw_icp_text})

    # Save to cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(structured_icp, f, indent=2, ensure_ascii=False)
    logger.info(f"  > Saved new structured ICP to {cache_path}")

    return {"structured_icp": structured_icp}


def get_used_queries(state: GraphState) -> dict:
    """Fetches all previously used search queries from the database."""
    logger.info("---NODE: Fetching Used Queries---")
    country = state.target_country
    with SearchQueryService() as query_service:
        used_queries = query_service.get_all_used_queries(country)
        logger.info(
            f"  > Found {len(used_queries)} used queries for country '{country}'."
        )
        return {"used_queries": used_queries}


def generate_search_queries(state: GraphState) -> dict:
    """Generates strategic search queries based on the structured ICP."""
    logger.info("---NODE: Generating Search Queries---")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.QUERY_GENERATION_PROMPT,
        input_variables=["structured_icp", "used_queries"],
    )
    chain = prompt | llm_client | parser

    # Format the list of used queries into a JSON string for the prompt
    used_queries_str = json.dumps(state.used_queries, indent=2)

    queries_result = chain.invoke(
        {"structured_icp": state.structured_icp, "used_queries": used_queries_str}
    )

    # The parser may return a dict {'queries': [...]} or a direct list [...]
    if hasattr(queries_result, "get"):
        return {"search_queries": queries_result.get("queries", [])}
    return {"search_queries": queries_result}


def _save_search_results(query: str, provider: str, results: list[dict]):
    """Save search results to a file for debugging purposes."""
    try:
        # Ensure directory exists
        results_dir = Path(__file__).parent.parent.parent / "search_results"
        results_dir.mkdir(exist_ok=True)

        # Create filename with timestamp and truncated query
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_query = "".join(c for c in query if c.isalnum() or c in " -_")[:50]
        clean_query = clean_query.replace(" ", "_")
        filename = f"{provider}_{timestamp}_{clean_query}.txt"

        filepath = results_dir / filename

        # Format results for saving
        content = f"Query: {query}\nProvider: {provider.upper()}\nTimestamp: {timestamp}\nResults: {len(results)}\n\n"

        for i, result in enumerate(results, 1):
            content += f"Result {i}:\n"
            content += f"Title: {result.get('title', 'N/A')}\n"
            content += f"URL: {result.get('url', 'N/A')}\n"
            content += f"Description: {result.get('description', 'N/A')[:200]}...\n"
            content += "-" * 80 + "\n"

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"💾 Saved {len(results)} results to {filename}")

    except Exception as e:
        logger.error(f"❌ Failed to save search results: {e}")


async def _execute_search_with_provider(
    query: str, country: str, provider: str, client: httpx.AsyncClient
) -> list[dict]:
    """Execute search with a specific provider and save results."""
    provider_clients = {
        "brave": brave_client,
        "serper": serper_client,
        "tavily": tavily_client,
        "firecrawl": firecrawl_client,
    }

    search_client = provider_clients.get(provider)
    if not search_client:
        logger.error(f"❌ Unknown provider: {provider}")
        return []

    try:
        # Add delay between requests for Brave to respect rate limits
        if provider == "brave":
            await asyncio.sleep(1)  # Ensure 1 second between Brave requests

        logger.info(f"🔍 Searching with {provider.upper()}: {query}")
        results = await search_client.search_async(query, country, client)

        # Save results to file for debugging
        _save_search_results(query, provider, results)

        logger.info(f"✅ {provider.upper()} returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"❌ Error with {provider}: {e}")
        return []


def execute_web_search(state: GraphState) -> dict:
    """Executes web searches concurrently using distributed providers."""
    queries_to_run = state.search_queries
    limit = state.search_query_limit

    if not queries_to_run:
        logger.warning("⚠️ No search queries were generated. Skipping web search.")
        return {"search_results": []}

    if limit and limit > 0:
        logger.info(f"---NODE: Executing Web Search (LIMITED to {limit} queries)---")
        queries_to_run = queries_to_run[:limit]
    else:
        logger.info(f"---NODE: Executing Web Search ({len(queries_to_run)} queries)---")

    async def _run_searches():
        """Internal async function to handle the concurrent searches."""
        all_results = []
        query_tracking_data = []  # Track queries for database storage
        providers = [
            "brave",
            "serper",
            "tavily",
            "firecrawl",
        ]  # Brave prioritized first

        async with httpx.AsyncClient() as client:
            tasks = []

            # Distribute queries across providers with Brave priority
            for i, query in enumerate(queries_to_run):
                provider = providers[i % len(providers)]
                task = _execute_search_with_provider(
                    query, state.target_country, provider, client
                )
                tasks.append((query, provider, task))

            search_results_list = await asyncio.gather(
                *[task for _, _, task in tasks], return_exceptions=True
            )

            for i, (query, provider, result) in enumerate(
                zip([t[0] for t in tasks], [t[1] for t in tasks], search_results_list)
            ):
                if isinstance(result, Exception):
                    logger.error(
                        f"❌ Search failed for query '{query[:50]}...' with provider {provider}: {result}"
                    )
                    query_tracking_data.append(
                        (query, state.target_country, 0, [provider], False)
                    )
                else:
                    all_results.extend(result)
                    query_tracking_data.append(
                        (query, state.target_country, len(result), [provider], True)
                    )
                    logger.info(
                        f"✅ Search completed for query '{query[:30]}...' via {provider}: {len(result)} results"
                    )

        # Save query usage to database
        with SearchQueryService() as query_service:
            query_service.mark_queries_as_used_batch(query_tracking_data)
            stats = query_service.get_query_stats()
            logger.info(
                f"📈 Query stats: {stats['total_queries']} total, {stats['successful_queries']} successful"
            )

        return all_results

    # Run the async searches
    search_results = asyncio.run(_run_searches())

    logger.info(f"🎯 Total search results collected: {len(search_results)}")
    return {"search_results": search_results}


def triage_and_extract_leads(state: GraphState) -> dict:
    """Uses an LLM to triage search results."""
    logger.info(f"---NODE: Triaging {len(state.search_results)} Search Results---")
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
            logger.info(
                f"  > [Result {i + 1}] PASS: Found potential lead '{candidate.discovered_name}'"
            )
            candidate_leads.append(candidate)
        except Exception:
            # Pydantic parser will raise an exception if the output is not valid JSON
            # or if the LLM outputs `null`, which we treat as a rejection.
            logger.info(f"  > [Result {i + 1}] REJECTED: Not a B2B lead.")

    logger.info(
        f"  > Completed triage. {len(candidate_leads)} potential leads identified."
    )
    return {"candidate_leads": candidate_leads}


def save_leads_to_db(state: GraphState) -> dict:
    """Saves unique, new leads to the database with enriched data."""
    leads_to_save = state.enriched_companies or [
        {"lead": lead, "enriched_data": None} for lead in state.candidate_leads
    ]

    logger.info(
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
                logger.info(f"  > ⏭️  SKIPPING Duplicate: '{lead.discovered_name}'")
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
            logger.info(
                f"  > ✅ ADDING New Lead: '{lead.discovered_name}' {'(enriched)' if enriched_data else ''}"
            )

        db.commit()
        logger.info(f"  > Successfully saved {saved_count} new leads to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"  > ❌ Database error: {e}", exc_info=True)
        return {"error_message": str(e)}
    finally:
        db.close()

    return {"newly_saved_leads_count": saved_count}


def scrape_and_enrich_companies(state: GraphState) -> dict:
    """Scrapes company websites using Crawl4AI and enriches data with LLM analysis."""
    logger.info(
        f"---NODE: Scraping and Enriching {len(state.candidate_leads)} Companies---"
    )

    # Load the enrichment prompt
    enrichment_prompt_path = (
        Path(__file__).parent.parent.parent / "prompts" / "company_enrichment.txt"
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


# --- Refinement Loop Nodes ---

ENRICHABLE_FIELDS = [
    "contact_email",
    "contact_phone",
    "location_details",
    "employee_count",
    "estimated_revenue",
    "equipment_needs",
    "recent_news",
]
MAX_REFINEMENT_LOOPS = 2


def check_enrichment_completeness(state: GraphState) -> str:
    """Checks if any enriched company has missing data and routes accordingly."""
    logger.info("---🕵️ NODE: Checking Enrichment Completeness---")
    logger.info(
        f"  > Loop attempt {state.refinement_attempts + 1} of {MAX_REFINEMENT_LOOPS + 1}"
    )

    if state.refinement_attempts > MAX_REFINEMENT_LOOPS:
        logger.warning(
            f"  > ⚠️  Max refinement loops ({MAX_REFINEMENT_LOOPS}) reached. Proceeding to save."
        )
        return "save"

    all_companies_complete = True
    for company_data in state.enriched_companies:
        enriched_data = company_data.get("enriched_data")
        if not enriched_data:
            logger.info(
                "  > ❗️ Found company with no enrichment data. Routing to refinement loop."
            )
            all_companies_complete = False
            break

        # This part handles partially successful enrichment.
        for field in ENRICHABLE_FIELDS:
            if not enriched_data.get(field):
                logger.info(
                    f"  > ❗️ Company '{company_data['lead'].discovered_name}' missing '{field}'. Routing to refinement loop."
                )
                all_companies_complete = False
                break
        if not all_companies_complete:
            break

    if all_companies_complete:
        logger.info("  > ✅ All companies have complete data. Routing to save.")
        return "save"
    else:
        return "refine"


def generate_refinement_queries(state: GraphState) -> dict:
    """Generates targeted search queries for missing information."""
    logger.info("---🔍 NODE: Generating Refinement Queries---")
    current_attempt = state.refinement_attempts
    logger.info(f"  > Refinement loop iteration: {current_attempt + 1}")
    refinement_queries = {}
    for i, company_data in enumerate(state.enriched_companies):
        company_name = company_data["lead"].discovered_name
        queries = []
        enriched_data = company_data.get("enriched_data")

        if not enriched_data:
            # If no data exists, generate queries for all fields.
            for field in ENRICHABLE_FIELDS:
                query = f'"{company_name}" {field.replace("_", " ")}'
                queries.append(query)
            logger.info(
                f"  > 📝 Generated {len(queries)} queries for '{company_name}' (no initial data)."
            )
        else:
            # If partial data exists, generate queries only for missing fields.
            for field in ENRICHABLE_FIELDS:
                if not enriched_data.get(field):
                    query = f'"{company_name}" {field.replace("_", " ")}'
                    queries.append(query)
            if queries:
                logger.info(
                    f"  > 📝 Generated {len(queries)} queries for '{company_name}'."
                )

        if queries:
            refinement_queries[i] = queries

    return {
        "refinement_queries": refinement_queries,
        "refinement_attempts": current_attempt + 1,
    }


async def _execute_single_refinement_search(
    queries: list[str], country: str
) -> list[dict]:
    """Helper to run searches for one company using distributed providers."""
    all_results = []
    providers = ["brave", "serper", "tavily", "firecrawl"]

    async with httpx.AsyncClient() as client:
        tasks = []

        # Distribute queries across providers with Brave priority
        for i, query in enumerate(queries):
            provider = providers[i % len(providers)]
            task = _execute_search_with_provider(query, country, provider, client)
            tasks.append((provider, task))  # Store provider name with task

        search_results_list = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        # Process results with provider information
        for (provider, _), result in zip(tasks, search_results_list):
            if isinstance(result, Exception):
                logger.error(f"  > ❌ Refinement search task failed: {result}")
                continue

            # Add provider info to each search result
            for res in result:
                res["_provider"] = provider
                all_results.append(res)

    return all_results


def execute_refinement_search(state: GraphState) -> dict:
    """Executes targeted web searches for missing data points."""
    logger.info("---🕸️ NODE: Executing Refinement Search---")
    refinement_results = {}
    country = state.target_country

    async def run_refinement_searches():
        tasks = []
        for index, queries in state.refinement_queries.items():
            company_name = state.enriched_companies[index]["lead"].discovered_name
            logger.info(f"  > Executing {len(queries)} searches for '{company_name}'")
            # Create a task for each company's search coroutine
            task = asyncio.create_task(
                _execute_single_refinement_search(queries, country)
            )
            tasks.append((index, task))

        # Wait for all tasks to complete
        results = await asyncio.gather(*[task for _, task in tasks])

        # Map results back to company index
        for (index, _), result_list in zip(tasks, results):
            if result_list:
                refinement_results[index] = result_list

    # Run the async orchestration
    asyncio.run(run_refinement_searches())

    logger.info(
        f"  > Refinement search complete. Found new data for {len(refinement_results)} companies."
    )
    return {"refinement_results": refinement_results}


def extract_and_merge_missing_info(state: GraphState) -> dict:
    """Uses an LLM to extract specific missing fields and merge them."""
    logger.info("---🔄 NODE: Extracting and Merging Refined Info---")
    updated_enriched_companies = state.enriched_companies
    refinement_results = state.refinement_results

    parser = JsonOutputParser()

    for index, results in refinement_results.items():
        company_data = updated_enriched_companies[index]
        company_name = company_data["lead"].discovered_name
        enriched_data = company_data.get("enriched_data", {})
        if not enriched_data:  # Ensure there's a dictionary to update
            enriched_data = {}
            company_data["enriched_data"] = enriched_data

        missing_fields = [
            field for field in ENRICHABLE_FIELDS if not enriched_data.get(field)
        ]
        if not missing_fields:
            continue

        logger.info(
            f"  > Refining '{company_name}' for fields: {', '.join(missing_fields)}"
        )

        prompt = PromptTemplate(
            template=prompts.REFINEMENT_PROMPT,
            input_variables=["company_name", "search_results", "missing_fields"],
            partial_variables={"parser_instructions": parser.get_format_instructions()},
        )

        chain = prompt | llm_client | parser
        combined_results = "\n".join(
            [
                f"Title: {r.get('title', '')}\n{r.get('description', '')}"
                for r in results
            ]
        )

        try:
            extracted_info = chain.invoke(
                {
                    "company_name": company_name,
                    "search_results": combined_results,
                    "missing_fields": ", ".join(missing_fields),
                }
            )

            # Merge the newly extracted info
            for field, value in extracted_info.items():
                if value and not enriched_data.get(field):
                    enriched_data[field] = value
                    logger.info(f"    + Merged new data for '{field}'")

            # Update qualification details if they were missing or incomplete
            if "qualification_details" in extracted_info:
                qual_details = enriched_data.get("qualification_details", {})
                qual_details.update(extracted_info["qualification_details"])
                enriched_data["qualification_details"] = qual_details

                # Recalculate score
                avg_score = sum(qual_details.values()) / len(qual_details)
                enriched_data["qualification_score"] = int(avg_score)
                logger.info(f"    + Updated qualification score to {int(avg_score)}")

        except Exception as e:
            logger.error(
                f"    - Error extracting refined info for '{company_name}': {e}"
            )

    return {"enriched_companies": updated_enriched_companies}
