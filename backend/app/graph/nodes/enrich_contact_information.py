import asyncio
import logging
from datetime import datetime
from typing import List

from app.graph.nodes.schemas import ContactPerson
from app.graph.state import GraphState

logger = logging.getLogger(__name__)


async def enrich_contact_information(state: GraphState) -> dict:
    """
    Enriches contact information for companies that need contact details.

    This node processes enriched companies and adds detailed contact information
    through web search and AI extraction.
    """
    logger.info(
        f"---NODE: Enriching Contact Information for {len(state.enriched_companies or [])} Companies---"
    )

    if not state.enriched_companies:
        logger.warning("No enriched companies to process for contact enrichment")
        return {"contact_enriched_companies": []}

    # Import here to avoid circular imports
    from app.services.contact_enrichment import ContactEnrichmentService

    contact_service = ContactEnrichmentService()
    contact_enriched_companies = []

    # Process companies in smaller batches to manage API limits
    BATCH_SIZE = 3
    CONCURRENCY_LIMIT = 2
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def enrich_single_company(enriched_company_data: dict) -> dict:
        """Enrich contact information for a single company."""
        async with semaphore:
            lead = enriched_company_data["lead"]
            enriched_data = enriched_company_data["enriched_data"]

            company_name = lead.discovered_name
            website_url = enriched_data.get("website_url") if enriched_data else None
            existing_contacts = enriched_data.get("contacts") if enriched_data else None

            logger.info(f"    > Starting contact enrichment for {company_name}")

            try:
                # Convert existing contacts to ContactPerson objects if they exist
                existing_contact_objects = []
                if existing_contacts:
                    for contact_data in existing_contacts:
                        if isinstance(contact_data, dict):
                            contact_obj = ContactPerson(**contact_data)
                            existing_contact_objects.append(contact_obj)
                        elif isinstance(contact_data, ContactPerson):
                            existing_contact_objects.append(contact_data)

                # Perform contact enrichment
                enrichment_result = await contact_service.enrich_company_contacts(
                    company_name=company_name,
                    website_url=website_url,
                    existing_contacts=existing_contact_objects,
                )

                # Create enhanced enriched data
                enhanced_enriched_data = enriched_data.copy() if enriched_data else {}

                # Update contact information
                enhanced_enriched_data.update(
                    {
                        "contact_persons": [
                            contact.model_dump()
                            for contact in enrichment_result["contacts"]
                        ],
                        "contact_enrichment_status": enrichment_result[
                            "enrichment_status"
                        ],
                        "contact_enriched_at": datetime.utcnow().isoformat(),
                        "contact_search_summary": enrichment_result[
                            "search_results_summary"
                        ],
                    }
                )

                # Merge existing contacts with new contacts (avoid duplicates)
                all_contacts = existing_contact_objects + enrichment_result["contacts"]
                unique_contacts = _deduplicate_contacts(all_contacts)
                enhanced_enriched_data["contacts"] = [
                    contact.model_dump() for contact in unique_contacts
                ]

                logger.info(
                    f"    ✓ Contact enrichment completed for {company_name}. "
                    f"Found {len(enrichment_result['contacts'])} new contacts, "
                    f"total: {len(unique_contacts)} contacts"
                )

                return {"lead": lead, "enriched_data": enhanced_enriched_data}

            except Exception as e:
                logger.error(
                    f"    - Contact enrichment failed for {company_name}: {str(e)}"
                )

                # Return original data with error status
                enhanced_enriched_data = enriched_data.copy() if enriched_data else {}
                enhanced_enriched_data.update(
                    {
                        "contact_enrichment_status": "failed",
                        "contact_enrichment_error": str(e),
                        "contact_enriched_at": datetime.utcnow().isoformat(),
                    }
                )

                return {"lead": lead, "enriched_data": enhanced_enriched_data}

    # Process companies in batches
    for i in range(0, len(state.enriched_companies), BATCH_SIZE):
        batch = state.enriched_companies[i : i + BATCH_SIZE]
        logger.info(
            f"  > Processing contact enrichment batch {i // BATCH_SIZE + 1} with {len(batch)} companies"
        )

        # Create tasks for concurrent processing
        tasks = [
            asyncio.create_task(enrich_single_company(company_data))
            for company_data in batch
        ]

        # Wait for all tasks in batch to complete
        try:
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"    - Batch task failed: {str(result)}")
                else:
                    contact_enriched_companies.append(result)

        except Exception as e:
            logger.error(f"    - Batch processing failed: {str(e)}")

        # Add delay between batches to respect API rate limits
        if i + BATCH_SIZE < len(state.enriched_companies):
            logger.info("    > Waiting 3 seconds before next batch...")
            await asyncio.sleep(3)

    successful_enrichments = len(
        [
            c
            for c in contact_enriched_companies
            if c.get("enriched_data", {}).get("contact_enrichment_status")
            in ["completed", "partial"]
        ]
    )

    logger.info(
        f"  > Contact enrichment completed. {successful_enrichments}/{len(state.enriched_companies)} "
        f"companies successfully enriched with contact information."
    )

    return {"contact_enriched_companies": contact_enriched_companies}


def _deduplicate_contacts(contacts: List[ContactPerson]) -> List[ContactPerson]:
    """Remove duplicate contacts based on name and email."""
    unique_contacts = []
    seen = set()

    for contact in contacts:
        # Create a key based on name and email (case-insensitive)
        name_key = contact.name.lower().strip() if contact.name else ""
        email_key = contact.email.lower().strip() if contact.email else ""
        key = (name_key, email_key)

        # Skip if we've seen this combination before
        if key in seen or (not name_key and not email_key):
            continue

        seen.add(key)
        unique_contacts.append(contact)

    return unique_contacts
