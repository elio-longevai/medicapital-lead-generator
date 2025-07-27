#!/usr/bin/env python3
"""
Standalone Contact Enrichment Script

This script enriches contact information for companies that haven't been processed yet.
It can be run independently of the main pipeline to update existing companies with
detailed contact information.

Usage:
    python enrich_contacts.py [--icp ICP_NAME] [--country COUNTRY] [--batch-size SIZE] [--max-companies NUM]
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.repositories import CompanyRepository
from app.services.contact_enrichment import ContactEnrichmentService
from app.graph.nodes.schemas import ContactPerson


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f"contact_enrichment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class ContactEnrichmentRunner:
    """Manages the contact enrichment process for existing companies."""

    def __init__(self, batch_size: int = 5, max_companies: Optional[int] = None):
        self.batch_size = batch_size
        self.max_companies = max_companies
        self.company_repo = CompanyRepository()
        self.contact_service = ContactEnrichmentService()
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": datetime.now(),
        }

    def get_companies_needing_enrichment(
        self, icp_name: Optional[str] = None, country: Optional[str] = None
    ) -> List[Dict]:
        """
        Get companies that need contact enrichment.

        Args:
            icp_name: Filter by ICP name
            country: Filter by country code

        Returns:
            List of company documents needing contact enrichment
        """
        logger.info("Fetching companies that need contact enrichment...")

        # Build filter criteria
        filter_criteria = {
            "$or": [
                {"contact_enrichment_status": {"$exists": False}},
                {"contact_enrichment_status": None},
                {"contact_enrichment_status": "pending"},
                {"contact_enrichment_status": "failed"},
            ]
        }

        if icp_name:
            filter_criteria["icp_name"] = icp_name

        if country:
            filter_criteria["country"] = country

        companies = self.company_repo.find_companies(filter_criteria)

        # Apply max_companies limit
        if self.max_companies:
            companies = companies[: self.max_companies]

        logger.info(f"Found {len(companies)} companies needing contact enrichment")

        if icp_name:
            logger.info(f"  - Filtered by ICP: {icp_name}")
        if country:
            logger.info(f"  - Filtered by country: {country}")
        if self.max_companies:
            logger.info(f"  - Limited to: {self.max_companies} companies")

        return companies

    async def enrich_single_company(self, company: Dict) -> Dict:
        """Enrich contact information for a single company."""
        company_id = str(company["_id"])
        company_name = company.get("discovered_name", "Unknown")

        logger.info(f"  > Processing: {company_name} (ID: {company_id})")

        try:
            # Mark as pending
            self.company_repo.update_company(
                company_id,
                {
                    "contact_enrichment_status": "pending",
                    "contact_enriched_at": datetime.utcnow(),
                },
            )

            # Perform enrichment
            website_url = company.get("website_url")
            existing_contacts = company.get("contacts", [])

            # Convert existing contacts to ContactPerson objects
            existing_contact_objects = []
            if existing_contacts:
                for contact_data in existing_contacts:
                    if isinstance(contact_data, dict):
                        try:
                            contact_obj = ContactPerson(**contact_data)
                            existing_contact_objects.append(contact_obj)
                        except Exception as e:
                            logger.warning(
                                f"    - Invalid contact data for {company_name}: {e}"
                            )

            # Enrich contacts
            enrichment_result = await self.contact_service.enrich_company_contacts(
                company_name=company_name,
                website_url=website_url,
                existing_contacts=existing_contact_objects,
            )

            # Prepare update data
            update_data = {
                "contact_persons": [
                    contact.model_dump() for contact in enrichment_result["contacts"]
                ],
                "contact_enrichment_status": enrichment_result["enrichment_status"],
                "contact_enriched_at": datetime.utcnow(),
                "contact_search_summary": enrichment_result["search_results_summary"],
            }

            # Update contact_email and contact_phone from enriched data
            if enrichment_result["contacts"]:
                primary_contact = enrichment_result["contacts"][0]
                if primary_contact.email:
                    update_data["contact_email"] = primary_contact.email
                if primary_contact.phone:
                    update_data["contact_phone"] = primary_contact.phone

            # Update company record
            success = self.company_repo.update_company(company_id, update_data)

            if success:
                contact_count = len(enrichment_result["contacts"])
                logger.info(
                    f"    ✓ Successfully enriched {company_name} with {contact_count} contacts"
                )
                self.stats["successful"] += 1
                return {
                    "status": "success",
                    "company_name": company_name,
                    "contacts_found": contact_count,
                    "enrichment_status": enrichment_result["enrichment_status"],
                }
            else:
                logger.error(f"    - Failed to update database for {company_name}")
                self.stats["failed"] += 1
                return {
                    "status": "database_error",
                    "company_name": company_name,
                    "error": "Database update failed",
                }

        except Exception as e:
            logger.error(f"    - Enrichment failed for {company_name}: {str(e)}")

            # Mark as failed
            try:
                self.company_repo.update_company(
                    company_id,
                    {
                        "contact_enrichment_status": "failed",
                        "contact_enriched_at": datetime.utcnow(),
                        "contact_enrichment_error": str(e),
                    },
                )
            except Exception as db_error:
                logger.error(f"    - Failed to update error status: {db_error}")

            self.stats["failed"] += 1
            return {"status": "error", "company_name": company_name, "error": str(e)}

    async def run_enrichment(
        self, icp_name: Optional[str] = None, country: Optional[str] = None
    ) -> Dict:
        """
        Run the contact enrichment process.

        Args:
            icp_name: Filter by ICP name
            country: Filter by country code

        Returns:
            Summary of the enrichment process
        """
        logger.info("=" * 80)
        logger.info("STARTING CONTACT ENRICHMENT PROCESS")
        logger.info("=" * 80)

        # Get companies to process
        companies = self.get_companies_needing_enrichment(icp_name, country)

        if not companies:
            logger.info("No companies found that need contact enrichment.")
            return self.stats

        logger.info(
            f"Processing {len(companies)} companies in batches of {self.batch_size}"
        )

        # Process companies in batches
        for i in range(0, len(companies), self.batch_size):
            batch = companies[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(companies) + self.batch_size - 1) // self.batch_size

            logger.info(
                f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} companies)"
            )

            # Process batch concurrently with rate limiting
            semaphore = asyncio.Semaphore(2)  # Limit concurrent requests

            async def process_with_semaphore(company):
                async with semaphore:
                    return await self.enrich_single_company(company)

            # Execute batch
            tasks = [
                asyncio.create_task(process_with_semaphore(company))
                for company in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Update stats
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"    - Batch task failed: {result}")
                    self.stats["failed"] += 1
                else:
                    self.stats["total_processed"] += 1

            # Progress update
            completed = i + len(batch)
            progress = (completed / len(companies)) * 100
            elapsed = datetime.now() - self.stats["start_time"]

            logger.info(
                f"Progress: {completed}/{len(companies)} ({progress:.1f}%) - Elapsed: {elapsed}"
            )

            # Rate limiting pause between batches
            if i + self.batch_size < len(companies):
                logger.info("⏳ Waiting 5 seconds before next batch...")
                await asyncio.sleep(5)

        # Final statistics
        self.print_final_stats()

        return self.stats

    def print_final_stats(self):
        """Print final enrichment statistics."""
        elapsed = datetime.now() - self.stats["start_time"]

        logger.info("\n" + "=" * 80)
        logger.info("CONTACT ENRICHMENT COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Total Time: {elapsed}")
        logger.info(f"Companies Processed: {self.stats['total_processed']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")

        if self.stats["total_processed"] > 0:
            success_rate = (
                self.stats["successful"] / self.stats["total_processed"]
            ) * 100
            logger.info(f"Success Rate: {success_rate:.1f}%")

        logger.info("=" * 80)


def main():
    """Main function to run the contact enrichment script."""
    parser = argparse.ArgumentParser(
        description="Enrich contact information for companies"
    )

    parser.add_argument(
        "--icp", type=str, help="Filter by ICP name (e.g., 'Duurzaamheid')"
    )

    parser.add_argument(
        "--country", type=str, help="Filter by country code (e.g., 'NL')"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of companies to process concurrently (default: 5)",
    )

    parser.add_argument(
        "--max-companies",
        type=int,
        help="Maximum number of companies to process (for testing)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if args.batch_size < 1 or args.batch_size > 20:
        logger.error("Batch size must be between 1 and 20")
        sys.exit(1)

    # Create runner
    runner = ContactEnrichmentRunner(
        batch_size=args.batch_size, max_companies=args.max_companies
    )

    # Run enrichment
    try:
        asyncio.run(runner.run_enrichment(icp_name=args.icp, country=args.country))
    except KeyboardInterrupt:
        logger.info("\n🛑 Process interrupted by user")
        runner.print_final_stats()
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Enrichment process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
