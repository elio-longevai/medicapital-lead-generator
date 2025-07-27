#!/usr/bin/env python3
"""
Script to apply sub-industry classification to existing companies in the database
that don't have sub_industry field populated yet.

This script:
1. Finds companies without sub_industry classification
2. Re-enriches them using the existing enrichment pipeline
3. Updates their sub_industry and related fields

Usage:
    python scripts/apply_sub_industry_classification.py [--dry-run] [--limit N]
"""

import asyncio
import logging
import argparse
import sys
import os
from typing import List, Dict, Any

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.repositories import CompanyRepository
from app.core.clients import llm_client
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SubIndustryClassification(BaseModel):
    """Schema for sub-industry classification result."""

    sub_industry: str = Field(
        description="The sub-industry classification: 'Eindgebruiker', 'Leverancier', or 'Overig'"
    )
    reasoning: str = Field(description="Brief explanation for the classification")


class SubIndustryClassifier:
    """Handles applying sub-industry classification to existing companies."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.repo = CompanyRepository()
        self.classification_prompt = self._create_classification_prompt()

    def find_companies_without_sub_industry(
        self, limit: int = None
    ) -> List[Dict[str, Any]]:
        """Find companies that don't have sub_industry field populated or have 'Onbekend'."""
        query = {
            "$or": [
                {"sub_industry": {"$exists": False}},
                {"sub_industry": None},
                {"sub_industry": ""},
                {"sub_industry": "Onbekend"},
            ]
        }

        cursor = self.repo.collection.find(query)

        if limit:
            cursor = cursor.limit(limit)

        companies = list(cursor)
        logger.info(
            f"Found {len(companies)} companies without sub-industry classification or with 'Onbekend'"
        )
        return companies

    def find_companies_by_names(self, company_names: List[str]) -> List[Dict[str, Any]]:
        """Find specific companies by their discovered names."""
        query = {"discovered_name": {"$in": company_names}}
        cursor = self.repo.collection.find(query)
        companies = list(cursor)
        logger.info(
            f"Found {len(companies)} companies with specified names: {company_names}"
        )
        return companies

    def _create_classification_prompt(self) -> PromptTemplate:
        """Create the prompt template for sub-industry classification."""
        template = """You are an expert in classifying companies in the Netherlands and Belgium based on their equipment usage.

Classify the following company into one of these three sub-industries:

1. **Eindgebruiker**: Companies that USE equipment for their own operations/services
   - Examples: Hospitals, clinics, factories, energy companies, farms, recycling facilities, production companies
   - Key indicators: They provide services, manufacture products, need equipment for operations

2. **Leverancier**: Companies that SUPPLY, MANUFACTURE, or SERVICE equipment for others
   - Examples: Equipment manufacturers, distributors, installers, solar panel installers, battery suppliers
   - Key indicators: They sell, produce, install, maintain, or distribute equipment

3. **Overig**: Other companies
   - Examples: Consultancy firms, IT services, research institutes, government agencies
   - Key indicators: Service-based without significant equipment needs

Company Information:
- Name: {company_name}
- Industry: {primary_industry}
- Location: {location}
- Description: {description}
- Equipment Needs: {equipment_needs}
- Initial Analysis: {initial_analysis}

Based on this information, classify the company and provide a brief reasoning.

Return your response in JSON format:
{{
    "sub_industry": "<Eindgebruiker|Leverancier|Overig>",
    "reasoning": "<Brief explanation for the classification>"
}}"""

        return PromptTemplate(
            template=template,
            input_variables=[
                "company_name",
                "primary_industry",
                "location",
                "description",
                "equipment_needs",
                "initial_analysis",
            ],
        )

    async def classify_sub_industry(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a company's sub-industry using LLM."""
        try:
            # Prepare input data
            company_name = company.get("discovered_name", "Unknown")
            location = company.get("location_details", company.get("country", ""))
            description = company.get("company_description", "")
            equipment_needs = company.get("equipment_needs", "")
            initial_analysis = company.get("initial_reasoning", "")

            # Create parser and chain
            parser = JsonOutputParser(pydantic_object=SubIndustryClassification)
            chain = self.classification_prompt | llm_client | parser

            # Invoke the chain
            result = await chain.ainvoke(
                {
                    "company_name": company_name,
                    "primary_industry": company.get("primary_industry", "General"),
                    "location": location,
                    "description": description,
                    "equipment_needs": equipment_needs,
                    "initial_analysis": initial_analysis,
                }
            )

            logger.info(
                f"Classified {company_name} as {result['sub_industry']}: {result['reasoning']}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Error classifying {company.get('discovered_name', 'Unknown')}: {e}"
            )
            return None

    def update_company_sub_industry(
        self, company_id: str, classification_result: Dict[str, Any]
    ) -> bool:
        """Update company with new sub-industry classification."""
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would update company {company_id} with sub_industry: {classification_result.get('sub_industry')}"
            )
            return True

        try:
            update_data = {
                "sub_industry": classification_result.get("sub_industry"),
                "sub_industry_reasoning": classification_result.get("reasoning"),
            }

            # Map sub_industry to entity_type for backward compatibility
            sub_industry = classification_result.get("sub_industry")
            if sub_industry == "Eindgebruiker":
                update_data["entity_type"] = "end_user"
            elif sub_industry == "Leverancier":
                update_data["entity_type"] = "supplier"
            else:
                update_data["entity_type"] = "other"

            result = self.repo.collection.update_one(
                {"_id": company_id}, {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(
                    f"Updated company {company_id} with sub_industry: {classification_result.get('sub_industry')}"
                )
                return True
            else:
                logger.warning(f"No changes made to company {company_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating company {company_id}: {e}")
            return False

    async def process_companies(
        self, companies: List[Dict[str, Any]], force_reclassify: bool = False
    ) -> Dict[str, int]:
        """Process a list of companies to apply sub-industry classification."""
        stats = {"processed": 0, "successful": 0, "failed": 0, "skipped": 0}

        for company in companies:
            stats["processed"] += 1
            company_id = company["_id"]
            company_name = company.get("discovered_name", "Unknown")

            logger.info(
                f"Processing {stats['processed']}/{len(companies)}: {company_name}"
            )

            # Skip if company already has valid sub_industry (unless force_reclassify is True)
            # Note: "Onbekend" is not considered a valid classification and will be processed
            if (
                not force_reclassify
                and company.get("sub_industry")
                and company["sub_industry"].strip()
                and company["sub_industry"] != "Onbekend"
            ):
                logger.info(
                    f"Skipping {company_name} - already has sub_industry: {company['sub_industry']}"
                )
                stats["skipped"] += 1
                continue

            # Classify the company's sub-industry
            classification_result = await self.classify_sub_industry(company)

            if classification_result and classification_result.get("sub_industry"):
                # Update the company with new classification
                if self.update_company_sub_industry(company_id, classification_result):
                    stats["successful"] += 1
                else:
                    stats["failed"] += 1
            else:
                logger.warning(f"No sub_industry classification for {company_name}")
                stats["failed"] += 1

        return stats

    async def run(
        self,
        limit: int = None,
        company_names: List[str] = None,
        force_reclassify: bool = False,
    ):
        """Main execution method."""
        logger.info(
            f"Starting sub-industry classification {'(DRY RUN)' if self.dry_run else ''}"
        )

        if company_names:
            # Process specific companies
            companies = self.find_companies_by_names(company_names)
            if not companies:
                logger.info(f"No companies found with names: {company_names}")
                return
        else:
            # Find companies without sub_industry
            companies = self.find_companies_without_sub_industry(limit)
            if not companies:
                logger.info("No companies found without sub-industry classification")
                return

        # Process companies
        stats = await self.process_companies(
            companies, force_reclassify=force_reclassify
        )

        # Print summary
        logger.info("=" * 50)
        logger.info("SUMMARY:")
        logger.info(f"Total processed: {stats['processed']}")
        logger.info(f"Successful updates: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Skipped (already classified): {stats['skipped']}")
        logger.info("=" * 50)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Apply sub-industry classification to existing companies (including those with 'Onbekend' classification)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of companies to process (for testing)"
    )
    parser.add_argument(
        "--companies",
        nargs="+",
        help="Specific company names to process (will force reclassify if they already have sub_industry)",
    )
    parser.add_argument(
        "--force-reclassify",
        action="store_true",
        help="Force reclassification even if companies already have sub_industry (only works with --companies)",
    )

    args = parser.parse_args()

    classifier = SubIndustryClassifier(dry_run=args.dry_run)
    await classifier.run(
        limit=args.limit,
        company_names=args.companies,
        force_reclassify=args.force_reclassify or bool(args.companies),
    )


if __name__ == "__main__":
    asyncio.run(main())
