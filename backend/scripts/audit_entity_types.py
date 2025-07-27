#!/usr/bin/env python3
"""
Script to audit existing entity_type values in the database.
Identifies all unique entity_type values and their counts to understand
what needs to be normalized to the three strict categories.
"""

import sys
import os
from collections import Counter

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.repositories import CompanyRepository


def audit_entity_types():
    """Audit existing entity_type values in the database."""
    print("🔍 Auditing entity_type values in database...")

    repo = CompanyRepository()

    # Get all companies and their entity_type values
    all_companies = repo.collection.find({}, {"entity_type": 1})

    entity_types = []
    none_count = 0

    for company in all_companies:
        entity_type = company.get("entity_type")
        if entity_type is None:
            none_count += 1
        else:
            entity_types.append(entity_type)

    # Count occurrences
    type_counts = Counter(entity_types)
    total_companies = len(entity_types) + none_count

    print(f"\n📊 Entity Type Analysis (Total: {total_companies} companies)")
    print("=" * 50)

    # Show standard categories first
    standard_categories = ["end_user", "supplier", "other"]

    print("✅ Standard Categories:")
    for category in standard_categories:
        count = type_counts.get(category, 0)
        percentage = (count / total_companies) * 100 if total_companies > 0 else 0
        print(f"   {category}: {count} ({percentage:.1f}%)")

    # Show non-standard values
    non_standard = {
        k: v for k, v in type_counts.items() if k not in standard_categories
    }

    if non_standard:
        print(f"\n❌ Non-Standard Values ({len(non_standard)} types):")
        for entity_type, count in sorted(
            non_standard.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total_companies) * 100
            print(f"   '{entity_type}': {count} ({percentage:.1f}%)")

    if none_count > 0:
        percentage = (none_count / total_companies) * 100
        print(f"\n🚫 NULL/Missing: {none_count} ({percentage:.1f}%)")

    # Summary
    standard_count = sum(type_counts.get(cat, 0) for cat in standard_categories)
    non_standard_count = sum(non_standard.values()) + none_count

    print("\n📈 Summary:")
    print(
        f"   ✅ Correctly classified: {standard_count} ({(standard_count/total_companies)*100:.1f}%)"
    )
    print(
        f"   ❌ Need normalization: {non_standard_count} ({(non_standard_count/total_companies)*100:.1f}%)"
    )

    return {
        "total": total_companies,
        "standard": standard_count,
        "non_standard": non_standard,
        "null_count": none_count,
        "type_counts": type_counts,
    }


if __name__ == "__main__":
    audit_entity_types()
