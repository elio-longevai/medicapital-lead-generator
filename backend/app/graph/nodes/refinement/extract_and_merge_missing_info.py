import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.clients import llm_client
from app.graph import prompts
from app.graph.state import GraphState
from .check_enrichment_completeness import ENRICHABLE_FIELDS

logger = logging.getLogger(__name__)


def extract_and_merge_missing_info(state: GraphState) -> dict:
    """Uses a targeted LLM call for each missing field and merges the data."""
    logger.info("---🔄 NODE: Extracting and Merging Refined Info---")
    updated_enriched_companies = state.enriched_companies
    refinement_results = state.refinement_results

    # This prompt is designed to extract a single value.
    prompt = PromptTemplate.from_template(prompts.REFINEMENT_PROMPT)
    # The output should be a simple string (or "null")
    chain = prompt | llm_client | StrOutputParser()

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

        # Combine all search result snippets into one block for this company
        combined_snippets = "\n\n".join(
            [
                f"Source: {r.get('url', 'N/A')}\nTitle: {r.get('title', '')}\n{r.get('description', '')}"
                for r in search_results
            ]
        )

        for field in missing_fields:
            try:
                # Invoke the chain for each missing field individually
                extracted_info = chain.invoke(
                    {
                        "company_name": company_name,
                        "snippet": combined_snippets,
                        "field_name": field,
                    }
                )

                # The LLM is instructed to return "null" if info is not found
                if extracted_info and extracted_info.lower() != "null":
                    enriched_data[field] = extracted_info
                    logger.info(
                        f"    + Merged new data for '{field}': {extracted_info[:100]}"
                    )

            except Exception as e:
                logger.error(
                    f"    - Error extracting '{field}' for '{company_name}': {e}"
                )

    return {"enriched_companies": updated_enriched_companies}
