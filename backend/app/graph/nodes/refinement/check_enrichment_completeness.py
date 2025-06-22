import logging

from app.graph.state import GraphState

logger = logging.getLogger(__name__)

# --- Refinement Loop Constants ---
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
