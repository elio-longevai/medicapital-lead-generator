#!/usr/bin/env python3
"""
Script to fix entity_type mapping for existing companies.
Converts 'hospital' to 'end_user' to match frontend expectations.

Usage:
    python scripts/fix_entity_type_mapping.py [--dry-run]
"""

import argparse
import os
import sys
from typing import Dict

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.repositories import CompanyRepository


def fix_entity_type_mapping(dry_run: bool = False) -> Dict[str, int]:
    """Fix entity_type mapping for all companies."""
    repo = CompanyRepository()

    # Count companies by entity_type before the fix
    print("Entity type counts before fix:")
    for entity_type in ["hospital", "end_user", "supplier", "other", None]:
        count = repo.collection.count_documents({"entity_type": entity_type})
        if count > 0:
            print(f"  {entity_type}: {count}")

    # Find all companies with entity_type = 'hospital'
    companies_to_fix = list(repo.collection.find({"entity_type": "hospital"}))

    print(
        f"\nFound {len(companies_to_fix)} companies with entity_type='hospital' to fix"
    )

    if not dry_run:
        # Update all companies with entity_type = 'hospital' to 'end_user'
        result = repo.collection.update_many(
            {"entity_type": "hospital"}, {"$set": {"entity_type": "end_user"}}
        )
        print(f"Updated {result.modified_count} companies")

        # Also ensure sub_industry and entity_type are consistent
        # Fix companies with sub_industry='Eindgebruiker' but wrong entity_type
        result2 = repo.collection.update_many(
            {"sub_industry": "Eindgebruiker", "entity_type": {"$ne": "end_user"}},
            {"$set": {"entity_type": "end_user"}},
        )
        print(
            f"Fixed {result2.modified_count} additional companies with sub_industry='Eindgebruiker'"
        )

        # Fix companies with sub_industry='Leverancier' but wrong entity_type
        result3 = repo.collection.update_many(
            {"sub_industry": "Leverancier", "entity_type": {"$ne": "supplier"}},
            {"$set": {"entity_type": "supplier"}},
        )
        print(
            f"Fixed {result3.modified_count} companies with sub_industry='Leverancier'"
        )

        # Fix companies with sub_industry='Overig' but wrong entity_type
        result4 = repo.collection.update_many(
            {"sub_industry": "Overig", "entity_type": {"$nin": ["other", None]}},
            {"$set": {"entity_type": "other"}},
        )
        print(f"Fixed {result4.modified_count} companies with sub_industry='Overig'")

        # Count companies by entity_type after the fix
        print("\nEntity type counts after fix:")
        for entity_type in ["hospital", "end_user", "supplier", "other", None]:
            count = repo.collection.count_documents({"entity_type": entity_type})
            if count > 0:
                print(f"  {entity_type}: {count}")
    else:
        print("\nDRY RUN - No changes made")

        # Show what would be fixed
        eindgebruiker_wrong = repo.collection.count_documents(
            {"sub_industry": "Eindgebruiker", "entity_type": {"$ne": "end_user"}}
        )
        leverancier_wrong = repo.collection.count_documents(
            {"sub_industry": "Leverancier", "entity_type": {"$ne": "supplier"}}
        )
        overig_wrong = repo.collection.count_documents(
            {"sub_industry": "Overig", "entity_type": {"$nin": ["other", None]}}
        )

        print("\nWould also fix:")
        print(
            f"  {eindgebruiker_wrong} companies with sub_industry='Eindgebruiker' but wrong entity_type"
        )
        print(
            f"  {leverancier_wrong} companies with sub_industry='Leverancier' but wrong entity_type"
        )
        print(
            f"  {overig_wrong} companies with sub_industry='Overig' but wrong entity_type"
        )

    return {
        "hospital_to_end_user": len(companies_to_fix),
        "total_processed": len(companies_to_fix),
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix entity_type mapping for existing companies"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    print(f"Fixing entity_type mapping {'(DRY RUN)' if args.dry_run else ''}")
    print("=" * 50)

    results = fix_entity_type_mapping(dry_run=args.dry_run)

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Companies with 'hospital' entity_type: {results['hospital_to_end_user']}")
    if not args.dry_run:
        print("All entity_type mappings have been fixed!")
    else:
        print("Run without --dry-run to apply the fixes")


if __name__ == "__main__":
    main()
