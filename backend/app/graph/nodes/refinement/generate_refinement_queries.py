import logging

from app.graph.state import GraphState

from .check_enrichment_completeness import ENRICHABLE_FIELDS

logger = logging.getLogger(__name__)

# Dutch translation map for field names to search terms
FIELD_NAME_TRANSLATIONS_NL = {
    "contact_email": "e-mailadres",
    "contact_phone": "telefoonnummer",
    "employee_count": "aantal medewerkers",
    "equipment_needs": "producten en diensten",
    "recent_news": "recent nieuws",
    "location_details": "adres locatie",
    "website_url": "website",
}

# Employee count search patterns organized by performance tiers
# Patterns are ordered by empirical testing results (100% → 50% success rates)
EMPLOYEE_SEARCH_PATTERNS = {
    "NL": {
        "tier_1": [  # High-performance patterns (50-100% success rates) - Try first
            '"{}" company size employees',  # 100% success rate - TOP PRIORITY
            '"{}" linkedin company size',  # 50% success rate - PROVEN EFFECTIVE
            "site:linkedin.com/company/{} employees",  # 50% success rate - PROVEN EFFECTIVE
            '"{}" aantal medewerkers',  # 50% success rate - DUTCH TRADITIONAL
        ],
        "tier_2": [  # Supplementary patterns - Only if tier_1 fails
            "site:linkedin.com/company/{} medewerkers",
            '"{}" linkedin bedrijfsgrootte',
            '"{}" personeelsbestand',
            '"{}" werknemersaantal',
            '"{}" employee count range',
            '"{}" workforce size',
        ],
    },
    "BE": {
        "tier_1": [  # High-performance patterns for Belgium
            '"{}" company size employees',  # 100% success rate - TOP PRIORITY
            '"{}" linkedin company size',  # 50% success rate - PROVEN EFFECTIVE
            "site:linkedin.com/company/{} employees",  # 50% success rate - PROVEN EFFECTIVE
            '"{}" aantal medewerkers',  # 50% success rate - DUTCH/FLEMISH TRADITIONAL
        ],
        "tier_2": [  # Supplementary patterns
            "site:linkedin.com/company/{} medewerkers",
            '"{}" linkedin bedrijfsgrootte',
            '"{}" personeelsbestand',
            '"{}" werknemersaantal',
            '"{}" employee count range',
            '"{}" workforce size',
        ],
    },
    "DEFAULT": {
        "tier_1": [  # High-performance patterns for international markets
            '"{}" company size employees',  # 100% success rate - TOP PRIORITY
            '"{}" linkedin company size',  # 50% success rate - PROVEN EFFECTIVE
            "site:linkedin.com/company/{} employees",  # 50% success rate - PROVEN EFFECTIVE
        ],
        "tier_2": [  # Supplementary international patterns
            '"{}" linkedin employee count',
            '"{}" staff size employees',
            '"{}" employee count range',
            '"{}" workforce size',
            '"{}" headcount employees',
        ],
    },
}


def get_search_term_for_field(field: str, country: str) -> str:
    """
    Translates a field name into a localized search term if applicable.
    Defaults to English if no translation is available.
    """
    if country.upper() == "NL" or country.upper() == "BE":
        return FIELD_NAME_TRANSLATIONS_NL.get(field, field.replace("_", " "))
    # Add other country logic here if needed in the future
    # elif country.upper() == 'BE':
    #     ...

    # Default to English
    return field.replace("_", " ")


def _clean_company_name_for_linkedin(company_name: str) -> str:
    """Clean company name for LinkedIn URL patterns (make URL-friendly)."""
    clean_name = company_name.lower().replace(" ", "-").replace("&", "and")
    return "".join(c for c in clean_name if c.isalnum() or c in "-")


def _apply_patterns_to_company(
    patterns: list[str], company_name: str, clean_company_name: str
) -> list[str]:
    """Apply search patterns to company names, handling LinkedIn URLs appropriately."""
    queries = []
    for pattern in patterns:
        if "site:linkedin.com/company/" in pattern:
            # For LinkedIn company URL patterns, use cleaned name
            query = pattern.format(clean_company_name)
        else:
            # For quoted company name patterns, use original name
            query = pattern.format(company_name)
        queries.append(query)
    return queries


def generate_employee_queries(
    company_name: str, country: str, tier: str = "all"
) -> dict[str, list[str]] | list[str]:
    """
    Generate employee count search queries with performance-based tiering.

    Args:
        company_name: Company name to search for
        country: Country code (NL, BE, or other)
        tier: "tier_1" (high-performance only), "tier_2" (supplementary only),
              "all" (both tiers as dict), or "flat" (all queries as flat list)

    Returns:
        - If tier="all": {"tier_1": [...], "tier_2": [...]}
        - If tier="tier_1" or "tier_2": list of queries for that tier
        - If tier="flat": flat list of all queries (tier_1 + tier_2)

    Performance notes:
        - tier_1: 50-100% success rates, cost-optimized, try first
        - tier_2: Lower success rates, only use if tier_1 fails
    """
    country_key = country.upper() if country.upper() in ["NL", "BE"] else "DEFAULT"
    patterns = EMPLOYEE_SEARCH_PATTERNS[country_key]

    clean_company_name = _clean_company_name_for_linkedin(company_name)

    # Generate queries for each tier
    tier_1_queries = _apply_patterns_to_company(
        patterns["tier_1"], company_name, clean_company_name
    )
    tier_2_queries = _apply_patterns_to_company(
        patterns["tier_2"], company_name, clean_company_name
    )

    # Return in requested format
    if tier == "tier_1":
        return tier_1_queries
    elif tier == "tier_2":
        return tier_2_queries
    elif tier == "flat":
        return tier_1_queries + tier_2_queries
    else:  # tier == "all"
        return {"tier_1": tier_1_queries, "tier_2": tier_2_queries}


def generate_refinement_queries(state: GraphState) -> dict:
    """Generates targeted search queries for missing information with cost optimization."""
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
                if field == "employee_count":
                    # Use smart tiered approach - start with only high-performance tier 1 queries
                    employee_queries = generate_employee_queries(
                        company_name, country, tier="tier_1"
                    )
                    queries.extend(employee_queries)
                    logger.info(
                        f"  > 💰 Using {len(employee_queries)} tier-1 employee queries for cost efficiency"
                    )
                else:
                    search_term = get_search_term_for_field(field, country)
                    query = f'"{company_name}" {search_term}'
                    queries.append(query)
            logger.info(
                f"  > 📝 Generated {len(queries)} queries for '{company_name}' (cost-optimized with tier-1 employee searches)."
            )
        else:
            # If partial data exists, generate queries only for missing fields.
            for field in ENRICHABLE_FIELDS:
                if not enriched_data.get(field):
                    if field == "employee_count":
                        # Use smart tiered approach - start with only high-performance tier 1 queries
                        employee_queries = generate_employee_queries(
                            company_name, country, tier="tier_1"
                        )
                        queries.extend(employee_queries)
                        logger.info(
                            f"  > 💰 Using {len(employee_queries)} tier-1 employee queries for cost efficiency"
                        )
                    else:
                        search_term = get_search_term_for_field(field, country)
                        query = f'"{company_name}" {search_term}'
                        queries.append(query)
            if queries:
                logger.info(
                    f"  > 📝 Generated {len(queries)} queries for '{company_name}' (cost-optimized tier-1 employee searches)."
                )

        if queries:
            refinement_queries[i] = queries

    return {
        "refinement_queries": refinement_queries,
        "refinement_attempts": current_attempt + 1,
    }
