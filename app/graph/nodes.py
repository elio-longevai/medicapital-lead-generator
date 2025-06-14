import asyncio
import httpx
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
        partial_variables={"parser_instructions": parser.get_format_instructions()}
    )
    chain = prompt | llm_client | parser
    structured_icp = chain.invoke({"raw_icp_text": state["raw_icp_text"]})
    return {"structured_icp": structured_icp}

def generate_search_queries(state: GraphState) -> dict:
    """Generates strategic search queries based on the structured ICP."""
    print("---NODE: Generating Search Queries---")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.QUERY_GENERATION_PROMPT,
        input_variables=["structured_icp"],
        partial_variables={"parser_instructions": parser.get_format_instructions()}
    )
    chain = prompt | llm_client | parser
    queries = chain.invoke({"structured_icp": state["structured_icp"]})
    return {"search_queries": queries}

async def execute_web_search(state: GraphState) -> dict:
    """Executes web searches concurrently for better performance."""
    print(f"---NODE: Executing Web Search for {len(state['search_queries'])} queries (Concurrent)---")
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for query in state["search_queries"]:
            print(f"  > Queuing search: '{query}'")
            tasks.append(brave_client.search_async(query=query, country=state["target_country"], client=client))
        
        results_list = await asyncio.gather(*tasks)
    
    # Flatten the list of lists
    all_results = [item for sublist in results_list for item in sublist]
    print(f"  > Found {len(all_results)} total results.")
    return {"search_results": all_results}

async def triage_and_extract_leads(state: GraphState) -> dict:
    """Uses an LLM to triage search results concurrently."""
    print(f"---NODE: Triaging {len(state['search_results'])} Search Results (Concurrent)---")
    parser = PydanticOutputParser(pydantic_object=CandidateLead)
    prompt = PromptTemplate(
        template=prompts.LEAD_TRIAGE_PROMPT,
        input_variables=["title", "description", "source_url", "country"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm_client | parser

    async def process_result(result: dict, index: int):
        # The triage prompt is very sensitive to low-quality/irrelevant input
        if not result.get("title") or not result.get("description"):
            return None

        try:
            # Use ainvoke for async execution
            candidate = await chain.ainvoke({
                "title": result["title"],
                "description": result.get("description", ""),
                "source_url": result["url"],
                "country": state["target_country"],
            })
            print(f"  > [Result {index+1}] PASS: Found potential lead '{candidate.discovered_name}'")
            return candidate
        except Exception:
            # Pydantic parser will raise an exception if the output is not valid JSON
            # or if the LLM outputs `null`, which we treat as a rejection.
            print(f"  > [Result {index+1}] REJECTED: Not a B2B lead.")
            return None
            
    tasks = [process_result(result, i) for i, result in enumerate(state["search_results"])]
    results = await asyncio.gather(*tasks)
    
    # Filter out the None results from failed triages
    candidate_leads = [res for res in results if res is not None]
    print(f"  > Completed triage. {len(candidate_leads)} potential leads identified.")
    return {"candidate_leads": candidate_leads}

def save_leads_to_db(state: GraphState) -> dict:
    """Saves unique, new leads to the database."""
    print(f"---NODE: Saving {len(state['candidate_leads'])} Candidate Leads to DB---")
    db = SessionLocal()
    saved_count = 0
    
    try:
        existing_names = {row[0] for row in db.query(Company.normalized_name).all()}
        
        for lead in state["candidate_leads"]:
            norm_name = normalize_name(lead.discovered_name)
            if not norm_name or norm_name in existing_names:
                print(f"  > SKIPPING (Duplicate or empty): '{lead.discovered_name}'")
                continue

            new_company = Company(
                normalized_name=norm_name,
                discovered_name=lead.discovered_name,
                source_url=lead.source_url,
                country=lead.country,
                primary_industry=lead.primary_industry,
                initial_reasoning=lead.initial_reasoning,
                status="discovered",
            )
            db.add(new_company)
            existing_names.add(norm_name) # Add to set to handle intra-batch duplicates
            saved_count += 1
            print(f"  > ADDING New Lead: '{lead.discovered_name}'")

        db.commit()
        print(f"---SUCCESS: Saved {saved_count} new leads to the database.---")
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        db.rollback()
        return {"error_message": str(e)}
    finally:
        db.close()
        
    return {"newly_saved_leads_count": saved_count}
