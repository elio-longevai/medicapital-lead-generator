import logging

from app.graph.state import GraphState

logger = logging.getLogger(__name__)

# --- Refinement Loop Constants ---
# Note: ENRICHABLE_FIELDS is still exported for compatibility with generate_refinement_queries.py
# but the actual completeness check now focuses on contact_persons
ENRICHABLE_FIELDS = [
    "contact_email",
    "contact_phone",
    "location_details",
    "employee_count",
    "equipment_needs",
    "recent_news",
]
MAX_REFINEMENT_LOOPS = 2
MIN_REQUIRED_CONTACTS = 2  # Minimum number of contact persons required


def check_enrichment_completeness(state: GraphState) -> str:
    """Checks if any enriched company has insufficient contacts and routes accordingly."""
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

        # Primary check: Does the company have enough contact persons?
        contact_persons = enriched_data.get("contact_persons", [])
        if len(contact_persons) < MIN_REQUIRED_CONTACTS:
            logger.info(
                f"  > ❗️ Company '{company_data['lead'].discovered_name}' has only {len(contact_persons)} contact(s), "
                f"needs at least {MIN_REQUIRED_CONTACTS}. Routing to refinement loop."
            )
            all_companies_complete = False
            break

    if all_companies_complete:
        logger.info(
            "  > ✅ All companies have sufficient contact data. Routing to save."
        )
        return "save"
    else:
        return "refine"
