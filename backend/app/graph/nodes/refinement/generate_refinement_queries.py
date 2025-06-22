import logging

from app.graph.state import GraphState
from .check_enrichment_completeness import ENRICHABLE_FIELDS

logger = logging.getLogger(__name__)


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
