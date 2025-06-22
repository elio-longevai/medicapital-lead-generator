import logging

from app.db.models import Company
from app.db.session import SessionLocal
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
    db = SessionLocal()
    saved_count = 0
    icp_name = state.icp_name

    try:
        existing_names = {row[0] for row in db.query(Company.normalized_name).all()}

        for item in leads_to_save:
            lead = item["lead"]
            enriched_data = item.get("enriched_data")

            norm_name = normalize_name(lead.discovered_name)
            if not norm_name or norm_name in existing_names:
                logger.info(f"  > ⏭️  SKIPPING Duplicate: '{lead.discovered_name}'")
                continue

            # Create new company with enriched data
            new_company = Company(
                discovered_name=lead.discovered_name,
                normalized_name=norm_name,
                country=lead.country,
                source_url=lead.source_url,
                primary_industry=lead.primary_industry,
                initial_reasoning=lead.initial_reasoning,
                status="discovered",
                icp_name=icp_name,
            )

            # Add enriched data if available
            if enriched_data:
                new_company.website_url = enriched_data.get("website_url")
                new_company.contact_email = enriched_data.get("contact_email")
                new_company.contact_phone = enriched_data.get("contact_phone")
                new_company.location_details = enriched_data.get("location_details")
                new_company.employee_count = enriched_data.get("employee_count")
                new_company.equipment_needs = enriched_data.get("equipment_needs")
                new_company.recent_news = enriched_data.get("recent_news")
                new_company.enriched_data = (
                    enriched_data  # Store the entire enriched data dictionary
                )
                new_company.estimated_revenue = enriched_data.get("estimated_revenue")
                new_company.qualification_details = enriched_data.get(
                    "qualification_details"
                )

                # Calculate qualification score from details
                if enriched_data.get("qualification_details"):
                    qual_details = enriched_data["qualification_details"]
                    avg_score = sum(qual_details.values()) / len(qual_details)
                    new_company.qualification_score = int(avg_score)

            db.add(new_company)
            existing_names.add(norm_name)  # Add to set to handle intra-batch duplicates
            saved_count += 1
            logger.info(
                f"  > ✅ ADDING New Lead: '{lead.discovered_name}' {'(enriched)' if enriched_data else ''}"
            )

        db.commit()
        logger.info(f"  > Successfully saved {saved_count} new leads to database.")
    except Exception as e:
        db.rollback()
        logger.error(f"  > ❌ Database error: {e}", exc_info=True)
        return {"error_message": str(e)}
    finally:
        db.close()

    return {"newly_saved_leads_count": saved_count}
