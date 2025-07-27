#!/usr/bin/env python3
"""
Contact Cleanup Script

This script removes contacts that don't have email OR phone information
from companies that have already been processed.
"""

import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.repositories import CompanyRepository


def main():
    """Clean up contacts without email or phone information."""
    repo = CompanyRepository()
    companies = repo.find_companies({"contact_enrichment_status": "completed"})

    updated_count = 0
    total_contacts_removed = 0

    print(f"Found {len(companies)} companies with completed contact enrichment")

    for company in companies:
        company_id = str(company["_id"])
        contact_persons = company.get("contact_persons", [])

        # Filter out contacts without email AND phone
        valid_contacts = [
            contact
            for contact in contact_persons
            if contact.get("email") or contact.get("phone")
        ]

        # If the number of contacts changed, update the company
        if len(valid_contacts) != len(contact_persons):
            contacts_removed = len(contact_persons) - len(valid_contacts)
            total_contacts_removed += contacts_removed

            print(
                f'Cleaning {company.get("discovered_name", "Unknown")}: {len(contact_persons)} -> {len(valid_contacts)} contacts'
            )

            update_data = {"contact_persons": valid_contacts}

            # Update status if no contacts remain
            if not valid_contacts:
                update_data["contact_enrichment_status"] = "partial"
                print('  -> Status changed to "partial" (no valid contacts)')

            repo.update_company(company_id, update_data)
            updated_count += 1

    print("\nCleanup completed:")
    print(f"- Updated {updated_count} companies")
    print(f"- Removed {total_contacts_removed} contacts without email/phone")


if __name__ == "__main__":
    main()
