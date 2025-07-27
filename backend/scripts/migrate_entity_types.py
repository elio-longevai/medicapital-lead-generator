#!/usr/bin/env python3
"""
Script to migrate and classify all companies into the three strict entity types:
- end_user: Companies that use equipment for their own services
- supplier: Companies that sell/produce/distribute equipment
- other: Non-commercial entities or those that don't fit other categories

This script analyzes existing company data (industry, description, equipment needs)
to intelligently classify each company.
"""

import sys
import os
from typing import Dict

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.repositories import CompanyRepository


class EntityTypeClassifier:
    """Classifies companies into entity types based on their business characteristics."""

    def __init__(self):
        # Keywords that indicate end-user businesses (service providers that use equipment)
        self.end_user_keywords = {
            # Healthcare providers
            "tandarts",
            "dentist",
            "kliniek",
            "clinic",
            "praktijk",
            "practice",
            "ziekenhuis",
            "hospital",
            "apotheek",
            "pharmacy",
            "fysiotherapie",
            "physiotherapy",
            "behandeling",
            "treatment",
            "patiënt",
            "patient",
            "zorg",
            "care",
            "medisch centrum",
            "medical center",
            "arts",
            "doctor",
            "specialist",
            "orthodontist",
            "kaakchirurg",
            "implantoloog",
            # Beauty & Wellness providers
            "salon",
            "spa",
            "beauty",
            "wellness",
            "massage",
            "cosmetisch",
            "cosmetic",
            "huidverzorging",
            "skincare",
            "schoonheid",
            "esthetiek",
            "nagelstudio",
            "nail salon",
            "kappers",
            "hairdresser",
            "barbier",
            # Other service providers
            "restaurant",
            "café",
            "hotel",
            "horeca",
            "catering",
            "bakkerij",
            "bakery",
            "slagerij",
            "butcher",
            "supermarkt",
            "winkel",
            "shop",
            "store",
            "garage",
            "werkplaats",
            "workshop",
            "school",
            "university",
            "universiteit",
            "onderwijs",
            "education",
            "sportschool",
            "gym",
            "fitness",
            "productie",
            "production",
            "fabriek",
            "factory",
            "laboratorium",
            "laboratory",
            "lab",
        }

        # Keywords that indicate supplier/manufacturer businesses
        self.supplier_keywords = {
            "verkoop",
            "verkopen",
            "sales",
            "sell",
            "selling",
            "distributie",
            "distribution",
            "groothandel",
            "wholesale",
            "leverancier",
            "supplier",
            "producent",
            "producer",
            "manufacturer",
            "fabrikant",
            "import",
            "export",
            "handel",
            "trade",
            "dealer",
            "reseller",
            "installateur",
            "installer",
            "montage",
            "installation",
            "service",
            "onderhoud",
            "maintenance",
            "reparatie",
            "repair",
            "techniek",
            "technical",
            "equipment",
            "apparatuur",
            "machinery",
            "machines",
            "systemen",
            "systems",
            "solutions",
            "oplossingen",
            "consulting",
            "consultancy",
            "advies",
            "advice",
            "engineering",
            "development",
            "ontwikkeling",
            "software",
            "technology",
            "technologie",
        }

        # Keywords that indicate "other" entities
        self.other_keywords = {
            "overheid",
            "government",
            "gemeente",
            "municipality",
            "ministerie",
            "ministry",
            "stichting",
            "foundation",
            "vereniging",
            "association",
            "organisatie",
            "organization",
            "instituut",
            "institute",
            "centrum",
            "center",
            "platform",
            "netwerk",
            "network",
            "branche",
            "industry",
            "nieuws",
            "news",
            "media",
            "pers",
            "press",
            "informatie",
            "information",
            "onderzoek",
            "research",
        }

        # Industry-based classifications
        self.industry_classifications = {
            # Healthcare industries - typically end users
            "gezondheidszorg": "end_user",
            "medisch": "end_user",
            "healthcare": "end_user",
            "medical": "end_user",
            "dental": "end_user",
            "tandheelkunde": "end_user",
            # Beauty & Wellness - typically end users
            "beauty": "end_user",
            "wellness": "end_user",
            "schoonheid": "end_user",
            # Manufacturing/Technology - typically suppliers
            "technologie": "supplier",
            "technology": "supplier",
            "manufacturing": "supplier",
            "productie": "supplier",
            "engineering": "supplier",
            "software": "supplier",
            # Trade/Sales - typically suppliers
            "handel": "supplier",
            "trade": "supplier",
            "distributie": "supplier",
            "distribution": "supplier",
        }

    def classify_company(self, company: Dict) -> str:
        """
        Classify a company based on its data.
        Returns: 'end_user', 'supplier', or 'other'
        """
        # Get relevant text fields
        company_name = (company.get("discovered_name") or "").lower()
        industry = (company.get("primary_industry") or "").lower()
        description = (company.get("company_description") or "").lower()
        equipment_needs = (company.get("equipment_needs") or "").lower()
        reasoning = (company.get("initial_reasoning") or "").lower()

        # Combine all text for analysis
        all_text = (
            f"{company_name} {industry} {description} {equipment_needs} {reasoning}"
        )

        # First, check industry-based classifications
        for industry_key, classification in self.industry_classifications.items():
            if industry_key in industry:
                return classification

        # Count keyword matches for each category
        end_user_score = sum(
            1 for keyword in self.end_user_keywords if keyword in all_text
        )
        supplier_score = sum(
            1 for keyword in self.supplier_keywords if keyword in all_text
        )
        other_score = sum(1 for keyword in self.other_keywords if keyword in all_text)

        # Special rules for specific patterns

        # Companies with "installateur", "service", "onderhoud" are usually suppliers
        if any(
            word in all_text
            for word in [
                "installateur",
                "installer",
                "service",
                "onderhoud",
                "maintenance",
            ]
        ):
            supplier_score += 3

        # Companies with practice/clinic in name are usually end users
        if any(
            word in company_name
            for word in ["praktijk", "practice", "kliniek", "clinic"]
        ):
            end_user_score += 3

        # Companies with "verkoop", "handel", "groothandel" are suppliers
        if any(
            word in all_text
            for word in ["verkoop", "handel", "groothandel", "distributie"]
        ):
            supplier_score += 3

        # Equipment needs that suggest end-user vs supplier
        if (
            "medische apparatuur" in equipment_needs
            or "tandheelkundige" in equipment_needs
        ):
            end_user_score += 2
        elif "software" in equipment_needs or "systemen" in equipment_needs:
            supplier_score += 1

        # Determine classification based on scores
        max_score = max(end_user_score, supplier_score, other_score)

        if max_score == 0:
            # No clear indicators, default to 'other'
            return "other"
        elif end_user_score == max_score:
            return "end_user"
        elif supplier_score == max_score:
            return "supplier"
        else:
            return "other"


def migrate_entity_types(dry_run: bool = True):
    """
    Migrate all companies to have proper entity_type classifications.

    Args:
        dry_run: If True, only shows what would be changed without updating
    """
    print("🚀 Starting Entity Type Migration...")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")

    repo = CompanyRepository()
    classifier = EntityTypeClassifier()

    # Get all companies
    companies = list(repo.collection.find({}))
    total_companies = len(companies)

    print(f"\n📊 Found {total_companies} companies to process")

    # Track classifications
    classifications = {"end_user": 0, "supplier": 0, "other": 0}
    updates = []

    print("\n🔍 Analyzing companies...")

    for i, company in enumerate(companies, 1):
        company_name = company.get("discovered_name", "Unknown")

        # Classify the company
        entity_type = classifier.classify_company(company)
        classifications[entity_type] += 1

        # Prepare update
        update_data = {
            "entity_type": entity_type,
            "updated_at": company.get("updated_at"),  # Keep existing timestamp
        }

        updates.append(
            {
                "company_id": company["_id"],
                "name": company_name,
                "entity_type": entity_type,
                "update_data": update_data,
            }
        )

        # Show progress every 50 companies
        if i % 50 == 0 or i == total_companies:
            print(f"   Processed {i}/{total_companies} companies...")

    # Show classification summary
    print("\n📈 Classification Results:")
    for entity_type, count in classifications.items():
        percentage = (count / total_companies) * 100
        display_name = {
            "end_user": "Eindgebruiker",
            "supplier": "Leverancier",
            "other": "Overig",
        }[entity_type]
        print(f"   {display_name}: {count} ({percentage:.1f}%)")

    if dry_run:
        print("\n🔍 DRY RUN - Sample Classifications:")
        # Show first 10 classifications as examples
        for update in updates[:10]:
            print(f"   '{update['name']}' → {update['entity_type']}")

        print(f"\n✅ Dry run completed. {total_companies} companies would be updated.")
        print("   Run with dry_run=False to apply changes.")
        return classifications

    # Apply updates
    print("\n💾 Applying updates to database...")
    success_count = 0

    for update in updates:
        try:
            result = repo.collection.update_one(
                {"_id": update["company_id"]}, {"$set": update["update_data"]}
            )
            if result.modified_count == 1:
                success_count += 1
        except Exception as e:
            print(f"   ❌ Failed to update {update['name']}: {e}")

    print("\n✅ Migration completed!")
    print(f"   Successfully updated: {success_count}/{total_companies} companies")

    return classifications


if __name__ == "__main__":
    # First run a dry run
    print("=" * 60)
    print("ENTITY TYPE MIGRATION - DRY RUN")
    print("=" * 60)

    dry_run_results = migrate_entity_types(dry_run=True)

    # Proceed with live migration automatically
    print("\n" + "=" * 60)
    print("ENTITY TYPE MIGRATION - LIVE UPDATE")
    print("=" * 60)

    live_results = migrate_entity_types(dry_run=False)
