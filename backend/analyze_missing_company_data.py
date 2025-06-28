#!/usr/bin/env python3
"""
Company Data Analysis Script

This utility script analyzes existing companies in the database to identify
missing information and provide insights about what data needs enrichment.

Usage:
    python analyze_missing_company_data.py [--country NL] [--icp-name "Healthcare"]
"""

import argparse
import logging
from collections import defaultdict
from typing import Dict, List, Optional

from sqlalchemy import and_

from app.db.models import Company
from app.db.session import SessionLocal
from app.graph.nodes.refinement.check_enrichment_completeness import ENRICHABLE_FIELDS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class CompanyDataAnalyzer:
    """Analyzes missing data in company records."""

    def __init__(self):
        self.db = SessionLocal()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()

    def get_companies_for_analysis(
        self, country: Optional[str] = None, icp_name: Optional[str] = None
    ) -> List[Company]:
        """Get companies for analysis based on filters."""
        query = self.db.query(Company)

        conditions = []
        if country:
            conditions.append(Company.country == country)
        if icp_name:
            conditions.append(Company.icp_name == icp_name)

        if conditions:
            query = query.filter(and_(*conditions))

        return query.all()

    def analyze_missing_fields(self, companies: List[Company]) -> Dict:
        """Analyze missing fields across all companies."""
        total_companies = len(companies)
        field_stats = {}

        for field in ENRICHABLE_FIELDS:
            missing_count = 0
            populated_count = 0

            for company in companies:
                field_value = getattr(company, field, None)
                if field_value:
                    populated_count += 1
                else:
                    missing_count += 1

            field_stats[field] = {
                "missing": missing_count,
                "populated": populated_count,
                "missing_percentage": (missing_count / total_companies * 100)
                if total_companies > 0
                else 0,
                "populated_percentage": (populated_count / total_companies * 100)
                if total_companies > 0
                else 0,
            }

        return field_stats

    def analyze_by_country(self, companies: List[Company]) -> Dict:
        """Analyze missing data by country."""
        country_stats = defaultdict(lambda: defaultdict(int))
        country_totals = defaultdict(int)

        for company in companies:
            country = company.country or "Unknown"
            country_totals[country] += 1

            for field in ENRICHABLE_FIELDS:
                field_value = getattr(company, field, None)
                if not field_value:
                    country_stats[country][field] += 1

        # Convert to percentages
        country_analysis = {}
        for country, field_counts in country_stats.items():
            total = country_totals[country]
            country_analysis[country] = {"total_companies": total, "fields": {}}

            for field, missing_count in field_counts.items():
                country_analysis[country]["fields"][field] = {
                    "missing": missing_count,
                    "percentage": (missing_count / total * 100) if total > 0 else 0,
                }

        return country_analysis

    def analyze_by_icp(self, companies: List[Company]) -> Dict:
        """Analyze missing data by ICP name."""
        icp_stats = defaultdict(lambda: defaultdict(int))
        icp_totals = defaultdict(int)

        for company in companies:
            icp = company.icp_name or "Unknown"
            icp_totals[icp] += 1

            for field in ENRICHABLE_FIELDS:
                field_value = getattr(company, field, None)
                if not field_value:
                    icp_stats[icp][field] += 1

        # Convert to percentages
        icp_analysis = {}
        for icp, field_counts in icp_stats.items():
            total = icp_totals[icp]
            icp_analysis[icp] = {"total_companies": total, "fields": {}}

            for field, missing_count in field_counts.items():
                icp_analysis[icp]["fields"][field] = {
                    "missing": missing_count,
                    "percentage": (missing_count / total * 100) if total > 0 else 0,
                }

        return icp_analysis

    def find_companies_needing_most_enrichment(
        self, companies: List[Company], top_n: int = 10
    ) -> List[Dict]:
        """Find companies that need the most enrichment."""
        company_scores = []

        for company in companies:
            missing_fields = []
            for field in ENRICHABLE_FIELDS:
                field_value = getattr(company, field, None)
                if not field_value:
                    missing_fields.append(field)

            if missing_fields:  # Only include companies with missing fields
                company_scores.append(
                    {
                        "company": company,
                        "missing_fields": missing_fields,
                        "missing_count": len(missing_fields),
                        "completion_percentage": (
                            (len(ENRICHABLE_FIELDS) - len(missing_fields))
                            / len(ENRICHABLE_FIELDS)
                            * 100
                        ),
                    }
                )

        # Sort by missing count (descending) and then by company name
        company_scores.sort(
            key=lambda x: (-x["missing_count"], x["company"].discovered_name)
        )

        return company_scores[:top_n]

    def print_summary_report(
        self, country: Optional[str] = None, icp_name: Optional[str] = None
    ):
        """Print a comprehensive analysis report."""
        print("=" * 80)
        print("📊 COMPANY DATA ENRICHMENT ANALYSIS REPORT")
        print("=" * 80)

        # Get companies for analysis
        companies = self.get_companies_for_analysis(country, icp_name)
        total_companies = len(companies)

        if total_companies == 0:
            print("❌ No companies found matching the criteria.")
            return

        # Filters applied
        filters = []
        if country:
            filters.append(f"Country: {country}")
        if icp_name:
            filters.append(f"ICP: {icp_name}")

        if filters:
            print(f"🔍 Filters Applied: {', '.join(filters)}")

        print(f"📈 Total Companies Analyzed: {total_companies}")
        print()

        # Overall field analysis
        print("📋 MISSING FIELD ANALYSIS")
        print("-" * 50)
        field_stats = self.analyze_missing_fields(companies)

        print(f"{'Field':<20} {'Missing':<8} {'%':<6} {'Populated':<10} {'%':<6}")
        print("-" * 50)

        # Sort by missing percentage (descending)
        sorted_fields = sorted(
            field_stats.items(), key=lambda x: x[1]["missing_percentage"], reverse=True
        )

        for field, stats in sorted_fields:
            print(
                f"{field:<20} {stats['missing']:<8} {stats['missing_percentage']:<6.1f} {stats['populated']:<10} {stats['populated_percentage']:<6.1f}"
            )

        print()

        # Companies needing most enrichment
        print("🔥 TOP COMPANIES NEEDING ENRICHMENT")
        print("-" * 60)
        top_companies = self.find_companies_needing_most_enrichment(companies, 10)

        if not top_companies:
            print("✅ All companies have complete data!")
        else:
            print(
                f"{'Company Name':<30} {'Missing':<8} {'Complete %':<10} {'Missing Fields'}"
            )
            print("-" * 80)

            for item in top_companies:
                company = item["company"]
                missing_fields_str = ", ".join(
                    item["missing_fields"][:3]
                )  # Show first 3
                if len(item["missing_fields"]) > 3:
                    missing_fields_str += f" (+{len(item['missing_fields']) - 3} more)"

                print(
                    f"{company.discovered_name[:29]:<30} {item['missing_count']:<8} {item['completion_percentage']:<9.1f}% {missing_fields_str}"
                )

        print()

        # Country breakdown (if not filtered by country)
        if not country:
            print("🌍 ANALYSIS BY COUNTRY")
            print("-" * 40)
            country_analysis = self.analyze_by_country(companies)

            for country_code, data in sorted(country_analysis.items()):
                total_missing = sum(
                    field_data["missing"] for field_data in data["fields"].values()
                )
                avg_completeness = 100 - (
                    total_missing
                    / (data["total_companies"] * len(ENRICHABLE_FIELDS))
                    * 100
                )
                print(
                    f"{country_code}: {data['total_companies']} companies, {avg_completeness:.1f}% avg completeness"
                )

            print()

        # ICP breakdown (if not filtered by ICP)
        if not icp_name:
            print("🎯 ANALYSIS BY ICP")
            print("-" * 40)
            icp_analysis = self.analyze_by_icp(companies)

            for icp, data in sorted(icp_analysis.items()):
                if data["total_companies"] > 0:
                    total_missing = sum(
                        field_data["missing"] for field_data in data["fields"].values()
                    )
                    avg_completeness = 100 - (
                        total_missing
                        / (data["total_companies"] * len(ENRICHABLE_FIELDS))
                        * 100
                    )
                    print(
                        f"{icp}: {data['total_companies']} companies, {avg_completeness:.1f}% avg completeness"
                    )

            print()

        # Enrichment recommendations
        print("💡 ENRICHMENT RECOMMENDATIONS")
        print("-" * 50)

        # Find fields that need the most attention
        priority_fields = [
            field for field, stats in sorted_fields if stats["missing_percentage"] > 50
        ]

        if priority_fields:
            print(
                f"🔥 High Priority Fields (>50% missing): {', '.join(priority_fields)}"
            )

        companies_needing_enrichment = len(
            [
                c
                for c in companies
                if any(not getattr(c, field, None) for field in ENRICHABLE_FIELDS)
            ]
        )

        if companies_needing_enrichment > 0:
            print(
                f"📊 {companies_needing_enrichment} out of {total_companies} companies need enrichment ({companies_needing_enrichment / total_companies * 100:.1f}%)"
            )

            # Suggested command
            print()
            print("🚀 SUGGESTED ENRICHMENT COMMAND:")
            cmd_parts = ["python enrich_existing_companies.py"]

            if country:
                cmd_parts.append(f"--country {country}")
            if icp_name:
                cmd_parts.append(f'--icp-name "{icp_name}"')
            if priority_fields:
                cmd_parts.append(
                    f"--fields {' '.join(priority_fields[:3])}"
                )  # Top 3 priority fields

            # Suggest reasonable batch size
            if companies_needing_enrichment <= 50:
                cmd_parts.append("--batch-size 5")
            elif companies_needing_enrichment <= 200:
                cmd_parts.append("--batch-size 10")
            else:
                cmd_parts.append("--batch-size 20")

            print(" ".join(cmd_parts))
            print()
            print(
                "💡 Add --dry-run to see what would be changed without updating the database"
            )
        else:
            print("✅ All companies have complete enrichment data!")

        print("=" * 80)


def main():
    """Main entry point for the analysis script."""
    parser = argparse.ArgumentParser(
        description="Analyze missing company data for enrichment planning"
    )
    parser.add_argument(
        "--country",
        type=str,
        help="Filter companies by country code (e.g., 'NL', 'BE')",
    )
    parser.add_argument("--icp-name", type=str, help="Filter companies by ICP name")

    args = parser.parse_args()

    try:
        with CompanyDataAnalyzer() as analyzer:
            analyzer.print_summary_report(country=args.country, icp_name=args.icp_name)
    except Exception as e:
        logger.error(f"💥 Analysis failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
