import logging

from app.graph.state import GraphState
from .check_enrichment_completeness import ENRICHABLE_FIELDS

logger = logging.getLogger(__name__)

# Dutch translation map for field names to search terms
FIELD_NAME_TRANSLATIONS_NL = {
    "contact_email": "e-mailadres",
    "contact_phone": "telefoonnummer",
    "employee_count": "aantal medewerkers",
    "estimated_revenue": "geschatte omzet",
    "equipment_needs": "producten en diensten",
    "recent_news": "recent nieuws",
    "location_details": "adres",
    "website_url": "website",
}


def get_search_term_for_field(field: str, country: str) -> str:
    """
    Translates a field name into a localized search term if applicable.
    Defaults to English if no translation is available.
    """
    if country.upper() == "NL":
        return FIELD_NAME_TRANSLATIONS_NL.get(field, field.replace("_", " "))
    # Add other country logic here if needed in the future
    # elif country.upper() == 'BE':
    #     ...

    # Default to English
    return field.replace("_", " ")


def generate_refinement_queries(state: GraphState) -> dict:
    """Generates targeted search queries for missing information."""
    logger.info("---🔍 NODE: Generating Refinement Queries---")
    current_attempt = state.refinement_attempts
    logger.info(f"  > Refinement loop iteration: {current_attempt + 1}")
    refinement_queries = {}
    for i, company_data in enumerate(state.enriched_companies):
        company_name = company_data["lead"].discovered_name
        # Get the company's country, defaulting to the target_country if not present
        country = (
            company_data["lead"].country
            if hasattr(company_data["lead"], "country")
            else state.target_country
        )
        queries = []
        enriched_data = company_data.get("enriched_data")

        if not enriched_data:
            # If no data exists, generate queries for all fields.
            for field in ENRICHABLE_FIELDS:
                search_term = get_search_term_for_field(field, country)
                query = f'"{company_name}" {search_term}'
                queries.append(query)
            logger.info(
                f"  > 📝 Generated {len(queries)} queries for '{company_name}' (no initial data)."
            )
        else:
            # If partial data exists, generate queries only for missing fields.
            for field in ENRICHABLE_FIELDS:
                if not enriched_data.get(field):
                    search_term = get_search_term_for_field(field, country)
                    query = f'"{company_name}" {search_term}'
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
