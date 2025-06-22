import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.clients import llm_client
from app.graph import prompts
from app.graph.state import GraphState
from .check_enrichment_completeness import ENRICHABLE_FIELDS

logger = logging.getLogger(__name__)


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
