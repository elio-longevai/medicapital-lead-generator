import asyncio
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.clients import llm_client
from app.graph import prompts
from app.graph.state import GraphState

from .check_enrichment_completeness import ENRICHABLE_FIELDS

logger = logging.getLogger(__name__)


async def extract_and_merge_missing_info(state: GraphState) -> dict:
    """Uses a targeted LLM call for each missing field and merges the data."""
    logger.info("---🔄 NODE: Extracting and Merging Refined Info---")
    updated_enriched_companies = state.enriched_companies
    refinement_results = state.refinement_results

    # This prompt is designed to extract a single value.
    prompt = PromptTemplate.from_template(prompts.REFINEMENT_PROMPT)
    # The output should be a simple string (or "null")
    chain = prompt | llm_client | StrOutputParser()

    all_company_tasks = []

    for index, search_results in refinement_results.items():
        company_data = updated_enriched_companies[index]
        company_name = company_data["lead"].discovered_name
        enriched_data = company_data.get("enriched_data", {})
        if not enriched_data:
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

        combined_snippets = "\n\n".join(
            [
                f"Source: {r.get('url', 'N/A')}\nTitle: {r.get('title', '')}\n{r.get('description', '')}"
                for r in search_results
            ]
        )

        # For each company, create a task to process all its missing fields
        async def process_company(
            local_enriched_data, local_company_name, local_missing_fields
        ):
            field_tasks = []
            for field in local_missing_fields:
                field_tasks.append(
                    chain.ainvoke(
                        {
                            "company_name": local_company_name,
                            "snippet": combined_snippets,
                            "field_name": field,
                        }
                    )
                )
            # Gather results for all fields of this company
            extracted_infos = await asyncio.gather(*field_tasks, return_exceptions=True)
            for field, info in zip(local_missing_fields, extracted_infos):
                if isinstance(info, Exception):
                    logger.error(
                        f"    - Error extracting '{field}' for '{local_company_name}': {info}"
                    )
                    continue
                if info and info.lower() != "null":
                    local_enriched_data[field] = info
                    logger.info(f"    + Merged new data for '{field}': {info[:100]}")

        all_company_tasks.append(
            process_company(enriched_data, company_name, missing_fields)
        )

    # Run all company processing tasks concurrently
    await asyncio.gather(*all_company_tasks)

    return {"enriched_companies": updated_enriched_companies}
