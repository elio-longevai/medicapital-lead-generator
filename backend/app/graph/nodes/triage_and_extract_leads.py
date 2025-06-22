import asyncio
import logging
from typing import Optional

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable

from app.core.clients import llm_client
from app.graph import prompts
from app.graph.state import CandidateLead, GraphState

logger = logging.getLogger(__name__)


async def _triage_one_result(
    result: dict, country: str, chain: Runnable, semaphore: asyncio.Semaphore
) -> Optional[CandidateLead]:
    """Tries to extract a lead from a single search result."""
    async with semaphore:
        try:
            candidate = await chain.ainvoke(
                {
                    "title": result["title"],
                    "description": result.get("description", ""),
                    "source_url": result["url"],
                    "country": country,
                }
            )
            logger.info(f"  > PASS: Found potential lead '{candidate.discovered_name}'")
            return candidate
        except Exception:
            logger.info("  > REJECTED: Not a B2B lead.")
            return None


def triage_and_extract_leads(state: GraphState) -> dict:
    """Uses an LLM to triage search results in parallel."""
    logger.info(f"---NODE: Triaging {len(state.search_results)} Search Results---")
    parser = PydanticOutputParser(pydantic_object=CandidateLead)
    prompt = PromptTemplate(
        template=prompts.LEAD_TRIAGE_PROMPT,
        input_variables=["title", "description", "source_url", "country"],
        partial_variables={"parser_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm_client | parser

    async def _run_triage():
        semaphore = asyncio.Semaphore(4)  # Limit to 4 concurrent tasks
        tasks = [
            _triage_one_result(result, state.target_country, chain, semaphore)
            for result in state.search_results
        ]

        # Gather results
        results = await asyncio.gather(*tasks)

        # Filter out None values (rejections)
        return [lead for lead in results if lead]

    # Run the async triage process
    candidate_leads = asyncio.run(_run_triage())

    logger.info(
        f"  > Completed triage. {len(candidate_leads)} potential leads identified."
    )
    return {"candidate_leads": candidate_leads}
