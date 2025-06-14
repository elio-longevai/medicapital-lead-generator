from typing import TypedDict
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.clients import llm_client, brave_client
from app.db.models import Company
from app.db.session import SessionLocal
from app.graph.state import GraphState, CandidateLead
from app.graph import prompts
from app.services.company_name_normalizer import normalize_name


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
        print(f"  > [{i+1}/{len(state.search_queries)}] Searching: '{query}'")

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
                f"  > [Result {i+1}] PASS: Found potential lead '{candidate.discovered_name}'"
            )
            candidate_leads.append(candidate)
        except Exception:
            # Pydantic parser will raise an exception if the output is not valid JSON
            # or if the LLM outputs `null`, which we treat as a rejection.
            print(f"  > [Result {i+1}] REJECTED: Not a B2B lead.")

    print(f"  > Completed triage. {len(candidate_leads)} potential leads identified.")
    return {"candidate_leads": candidate_leads}


def save_leads_to_db(state: GraphState) -> dict:
    """Saves unique, new leads to the database."""
    print(f"---NODE: Saving {len(state.candidate_leads)} Candidate Leads to DB---")
    db = SessionLocal()
    saved_count = 0

    try:
        existing_names = {row[0] for row in db.query(Company.normalized_name).all()}

        for lead in state.candidate_leads:
            norm_name = normalize_name(lead.discovered_name)
            if not norm_name or norm_name in existing_names:
                print(f"  > SKIPPING Duplicate: '{lead.discovered_name}'")
                continue

            new_company = Company(
                discovered_name=lead.discovered_name,
                normalized_name=norm_name,
                country=lead.country,
                source_url=lead.source_url,
                primary_industry=lead.primary_industry,
                initial_reasoning=lead.initial_reasoning,
                status="discovered",
            )
            db.add(new_company)
            existing_names.add(norm_name)  # Add to set to handle intra-batch duplicates
            saved_count += 1
            print(f"  > ADDING New Lead: '{lead.discovered_name}'")

        db.commit()
        print(f"  > Successfully saved {saved_count} new leads to database.")
    except Exception as e:
        db.rollback()
        print(f"  > Database error: {e}")
        return {"error_message": str(e)}
    finally:
        db.close()

    return {"newly_saved_leads_count": saved_count}
