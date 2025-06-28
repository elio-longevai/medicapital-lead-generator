#!/usr/bin/env python3
"""
Enrichment Script for Existing Companies

This script enriches existing companies in the database with missing information
by leveraging the existing refinement pipeline. It can be run standalone to
fill gaps in company data.

Usage:
    python enrich_existing_companies.py [--batch-size 10] [--country NL] [--icp-name "Healthcare"]
"""

import asyncio
import argparse
import logging
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.models import Company
from app.db.session import SessionLocal
from app.graph.state import GraphState, CandidateLead
from app.graph.nodes.refinement import (
    generate_refinement_queries,
    execute_refinement_search,
    extract_and_merge_missing_info,
)
from app.graph.nodes.refinement.check_enrichment_completeness import ENRICHABLE_FIELDS


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("enrichment.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@dataclass
class EnrichmentStats:
    """Track enrichment statistics."""

    total_companies: int = 0
    companies_processed: int = 0
    companies_enriched: int = 0
    fields_enriched: int = 0
    errors: int = 0
    skipped: int = 0


class ExistingCompanyEnricher:
    """Enriches existing companies with missing information."""

    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.stats = EnrichmentStats()

    def get_companies_needing_enrichment(
        self,
        db: Session,
        country: Optional[str] = None,
        icp_name: Optional[str] = None,
        specific_fields: Optional[List[str]] = None,
    ) -> List[Company]:
        """
        Query companies that have missing enrichable fields.

        Args:
            db: Database session
            country: Filter by country code (e.g., 'NL')
            icp_name: Filter by ICP name
            specific_fields: Only look for companies missing these specific fields

        Returns:
            List of companies needing enrichment
        """
        logger.info("🔍 Querying companies needing enrichment...")

        # Build base query
        query = db.query(Company)

        # Apply filters
        conditions = []

        if country:
            conditions.append(Company.country == country)

        if icp_name:
            conditions.append(Company.icp_name == icp_name)

        # Filter for companies with missing enrichable fields
        fields_to_check = specific_fields or ENRICHABLE_FIELDS

        missing_field_conditions = []
        for field in fields_to_check:
            field_attr = getattr(Company, field, None)
            if field_attr is not None:
                missing_field_conditions.append(
                    or_(field_attr.is_(None), field_attr == "")
                )

        if missing_field_conditions:
            conditions.append(or_(*missing_field_conditions))

        if conditions:
            query = query.filter(and_(*conditions))

        companies = query.all()

        logger.info(f"📊 Found {len(companies)} companies needing enrichment")

        # Log detailed breakdown
        field_counts = {}
        for company in companies:
            for field in fields_to_check:
                field_value = getattr(company, field, None)
                if not field_value:
                    field_counts[field] = field_counts.get(field, 0) + 1

        logger.info("📋 Missing field breakdown:")
        for field, count in sorted(field_counts.items()):
            logger.info(f"   • {field}: {count} companies")

        return companies

    def company_to_candidate_lead(self, company: Company) -> CandidateLead:
        """Convert a Company model to a CandidateLead for processing."""
        return CandidateLead(
            discovered_name=company.discovered_name,
            source_url=company.source_url,
            country=company.country,
            primary_industry=company.primary_industry,
            initial_reasoning=company.initial_reasoning,
        )

    def get_missing_fields_for_company(self, company: Company) -> List[str]:
        """Get list of missing enrichable fields for a company."""
        missing_fields = []
        for field in ENRICHABLE_FIELDS:
            field_value = getattr(company, field, None)
            if not field_value:
                missing_fields.append(field)
        return missing_fields

    def create_mock_state_for_company(self, company: Company) -> GraphState:
        """Create a GraphState for a single company to use with refinement nodes."""
        candidate_lead = self.company_to_candidate_lead(company)

        # Create enriched data from existing company fields
        enriched_data = {}
        for field in ENRICHABLE_FIELDS:
            field_value = getattr(company, field, None)
            if field_value:
                enriched_data[field] = field_value

        # Create the enriched company data structure
        enriched_company = {
            "lead": candidate_lead,
            "enriched_data": enriched_data if enriched_data else None,
        }

        return GraphState(
            icp_name=company.icp_name or "Unknown",
            raw_icp_text="Enrichment of existing company",
            target_country=company.country,
            enriched_companies=[enriched_company],
            refinement_attempts=0,
        )

    async def enrich_company_batch(self, companies: List[Company]) -> Dict[int, Dict]:
        """
        Enrich a batch of companies using the existing refinement pipeline.

        Args:
            companies: List of companies to enrich

        Returns:
            Dictionary mapping company IDs to enriched data
        """
        logger.info(f"🔄 Processing batch of {len(companies)} companies...")

        # Create states for each company
        states = []
        company_id_map = {}

        for i, company in enumerate(companies):
            state = self.create_mock_state_for_company(company)
            states.append(state)
            company_id_map[i] = company.id

        # Process each company's refinement
        enrichment_results = {}

        for i, state in enumerate(states):
            company = companies[i]
            missing_fields = self.get_missing_fields_for_company(company)

            if not missing_fields:
                logger.info(
                    f"⏭️  Company '{company.discovered_name}' has no missing fields"
                )
                self.stats.skipped += 1
                continue

            logger.info(
                f"🔍 Enriching '{company.discovered_name}' for fields: {', '.join(missing_fields)}"
            )

            try:
                # Step 1: Generate refinement queries
                query_result = generate_refinement_queries(state)
                state.refinement_queries = query_result.get("refinement_queries", {})

                if not state.refinement_queries:
                    logger.warning(
                        f"⚠️  No queries generated for '{company.discovered_name}'"
                    )
                    self.stats.skipped += 1
                    continue

                # Step 2: Execute refinement search
                search_result = await execute_refinement_search(state)
                state.refinement_results = search_result.get("refinement_results", {})

                if not state.refinement_results:
                    logger.warning(
                        f"⚠️  No search results for '{company.discovered_name}'"
                    )
                    self.stats.skipped += 1
                    continue

                # Step 3: Extract and merge missing info
                merge_result = await extract_and_merge_missing_info(state)
                updated_companies = merge_result.get("enriched_companies", [])

                if updated_companies:
                    enriched_data = updated_companies[0].get("enriched_data", {})
                    if enriched_data:
                        enrichment_results[company.id] = enriched_data

                        # Count enriched fields
                        new_fields = 0
                        for field in missing_fields:
                            if enriched_data.get(field):
                                new_fields += 1

                        self.stats.fields_enriched += new_fields
                        self.stats.companies_enriched += 1
                        logger.info(
                            f"✅ Enriched '{company.discovered_name}' with {new_fields} new fields"
                        )
                    else:
                        logger.warning(
                            f"⚠️  No enriched data extracted for '{company.discovered_name}'"
                        )
                        self.stats.skipped += 1
                else:
                    logger.warning(
                        f"⚠️  No updated companies returned for '{company.discovered_name}'"
                    )
                    self.stats.skipped += 1

                self.stats.companies_processed += 1

            except Exception as e:
                logger.error(
                    f"❌ Error enriching '{company.discovered_name}': {e}",
                    exc_info=True,
                )
                self.stats.errors += 1

        return enrichment_results

    def update_company_in_db(
        self, db: Session, company_id: int, enriched_data: Dict
    ) -> bool:
        """
        Update a company in the database with enriched data.

        Args:
            db: Database session
            company_id: ID of company to update
            enriched_data: Dictionary of enriched data

        Returns:
            True if update was successful, False otherwise
        """
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                logger.error(f"❌ Company with ID {company_id} not found")
                return False

            # Update individual fields
            updated_fields = []
            for field in ENRICHABLE_FIELDS:
                if enriched_data.get(field):
                    setattr(company, field, enriched_data[field])
                    updated_fields.append(field)

            # Update the enriched_data JSON field
            if company.enriched_data:
                company.enriched_data.update(enriched_data)
            else:
                company.enriched_data = enriched_data

            # Update timestamp
            company.updated_at = datetime.utcnow()

            db.commit()

            logger.info(
                f"💾 Updated '{company.discovered_name}' with fields: {', '.join(updated_fields)}"
            )
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"❌ Error updating company {company_id}: {e}", exc_info=True)
            return False

    async def enrich_companies(
        self,
        country: Optional[str] = None,
        icp_name: Optional[str] = None,
        specific_fields: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> EnrichmentStats:
        """
        Main method to enrich existing companies.

        Args:
            country: Filter by country code
            icp_name: Filter by ICP name
            specific_fields: Only enrich these specific fields
            dry_run: If True, don't actually update the database

        Returns:
            EnrichmentStats with processing results
        """
        logger.info("🚀 Starting enrichment of existing companies...")

        if dry_run:
            logger.info("🔍 DRY RUN MODE - No database updates will be made")

        db = SessionLocal()

        try:
            # Get companies needing enrichment
            companies = self.get_companies_needing_enrichment(
                db, country, icp_name, specific_fields
            )

            if not companies:
                logger.info("✅ No companies found needing enrichment")
                return self.stats

            self.stats.total_companies = len(companies)

            # Process companies in batches
            for i in range(0, len(companies), self.batch_size):
                batch = companies[i : i + self.batch_size]
                batch_num = i // self.batch_size + 1
                total_batches = (
                    len(companies) + self.batch_size - 1
                ) // self.batch_size

                logger.info(
                    f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} companies)"
                )

                # Enrich the batch
                enrichment_results = await self.enrich_company_batch(batch)

                # Update database if not dry run
                if not dry_run:
                    for company_id, enriched_data in enrichment_results.items():
                        self.update_company_in_db(db, company_id, enriched_data)
                else:
                    logger.info(
                        f"🔍 DRY RUN: Would update {len(enrichment_results)} companies"
                    )

                # Progress update
                progress = min(i + self.batch_size, len(companies))
                logger.info(
                    f"📊 Progress: {progress}/{len(companies)} companies processed"
                )

        finally:
            db.close()

        # Log final statistics
        logger.info("📊 Final Enrichment Statistics:")
        logger.info(f"   • Total companies found: {self.stats.total_companies}")
        logger.info(f"   • Companies processed: {self.stats.companies_processed}")
        logger.info(f"   • Companies enriched: {self.stats.companies_enriched}")
        logger.info(f"   • Fields enriched: {self.stats.fields_enriched}")
        logger.info(f"   • Companies skipped: {self.stats.skipped}")
        logger.info(f"   • Errors: {self.stats.errors}")

        return self.stats


def main():
    """Main entry point for the enrichment script."""
    parser = argparse.ArgumentParser(
        description="Enrich existing companies with missing information"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of companies to process in each batch (default: 10)",
    )
    parser.add_argument(
        "--country",
        type=str,
        help="Filter companies by country code (e.g., 'NL', 'BE')",
    )
    parser.add_argument("--icp-name", type=str, help="Filter companies by ICP name")
    parser.add_argument(
        "--fields",
        type=str,
        nargs="+",
        help="Only enrich these specific fields",
        choices=ENRICHABLE_FIELDS,
    )
    parser.add_argument(
        "--limit", type=int, help="Maximum number of companies to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually update the database, just show what would be done",
    )

    args = parser.parse_args()

    # Create enricher
    enricher = ExistingCompanyEnricher(batch_size=args.batch_size)

    # Run enrichment
    try:
        stats = asyncio.run(
            enricher.enrich_companies(
                country=args.country,
                icp_name=args.icp_name,
                specific_fields=args.fields,
                dry_run=args.dry_run,
            )
        )

        # Return appropriate exit code
        if stats.errors > 0:
            logger.warning(f"⚠️  Completed with {stats.errors} errors")
            sys.exit(1)
        else:
            logger.info("✅ Enrichment completed successfully")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("🛑 Enrichment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Enrichment failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
