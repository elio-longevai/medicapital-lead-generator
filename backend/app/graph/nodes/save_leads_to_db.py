import logging

from app.db.repositories import CompanyRepository
from app.graph.state import GraphState
from app.services.company_name_normalizer import normalize_name

logger = logging.getLogger(__name__)


def save_leads_to_db(state: GraphState) -> dict:
    """Saves unique, new leads to the database with enriched data."""
    leads_to_save = state.enriched_companies or [
        {"lead": lead, "enriched_data": None} for lead in state.candidate_leads
    ]

    logger.info(
        f"---NODE: Saving {len(leads_to_save)} Candidate Leads to DB (with enrichment)---"
    )

    company_repo = CompanyRepository()
    saved_count = 0
    icp_name = state.icp_name

    try:
        # Get existing normalized names for deduplication
        existing_names = company_repo.get_all_normalized_names()

        for item in leads_to_save:
            lead = item["lead"]
            enriched_data = item.get("enriched_data")

            norm_name = normalize_name(lead.discovered_name)
            if not norm_name or norm_name in existing_names:
                logger.info(f"  > ⏭️  SKIPPING Duplicate: '{lead.discovered_name}'")
                continue

            # Create new company document with enriched data
            company_data = {
                "discovered_name": lead.discovered_name,
                "normalized_name": norm_name,
                "country": lead.country,
                "source_url": lead.source_url,
                "primary_industry": lead.primary_industry,
                "initial_reasoning": lead.initial_reasoning,
                "status": "discovered",
                "icp_name": icp_name,
            }

            # Add enriched data if available
            if enriched_data:
                # Extract first contact email and phone for backwards compatibility/simplicity if needed elsewhere
                contacts = enriched_data.get("contacts", [])
                primary_contact = contacts[0] if contacts else {}

                company_data.update(
                    {
                        "entity_type": enriched_data.get("entity_type"),
                        "sub_industry": enriched_data.get("sub_industry"),
                        "contacts": enriched_data.get("contacts"),
                        "contact_email": primary_contact.get("email"),
                        "contact_phone": None,  # Phone was removed from contacts, set to None
                        "website_url": enriched_data.get("website_url"),
                        "company_description": enriched_data.get("company_description"),
                        "location_details": enriched_data.get("location_details"),
                        "employee_count": enriched_data.get("employee_count"),
                        "equipment_needs": enriched_data.get("equipment_needs"),
                        "recent_news": enriched_data.get("recent_news"),
                        "enriched_data": enriched_data,  # Store the entire enriched data dictionary
                        "estimated_revenue": enriched_data.get("estimated_revenue"),
                        "qualification_details": enriched_data.get(
                            "qualification_details"
                        ),
                    }
                )

                # Calculate qualification score from details
                if enriched_data.get("qualification_details"):
                    qual_details = enriched_data["qualification_details"]
                    if qual_details:  # Ensure qual_details is not empty
                        avg_score = sum(qual_details.values()) / len(qual_details)
                        company_data["qualification_score"] = int(avg_score)
                    else:
                        company_data["qualification_score"] = (
                            75  # Default score if no details
                        )

            # Insert into MongoDB
            result_id = company_repo.create_company(company_data)
            if result_id:
                existing_names.add(
                    norm_name
                )  # Add to set to handle intra-batch duplicates
                saved_count += 1
                logger.info(
                    f"  > ✅ ADDING New Lead: '{lead.discovered_name}' {'(enriched)' if enriched_data else ''}"
                )
            else:
                logger.warning(f"  > ⚠️ Failed to save lead: '{lead.discovered_name}'")

        logger.info(f"  > Successfully saved {saved_count} new leads to database.")
    except Exception as e:
        logger.error(f"  > ❌ Database error: {e}", exc_info=True)
        return {"error_message": str(e)}

    return {"newly_saved_leads_count": saved_count}
