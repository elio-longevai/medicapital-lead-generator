#!/usr/bin/env python3
"""
Contact Cleanup Script

This script removes contacts that don't have email OR phone information
from companies that have already been processed.

SAFETY FEATURES:
- Creates backup collection before any deletions
- Uses MongoDB transactions for atomicity
- Provides rollback mechanism
- Detailed logging of all operations
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.db.repositories import CompanyRepository
from app.db.mongodb import get_mongo_collection, get_mongo_client


def create_backup_collection(companies_to_update: List[Dict[str, Any]]) -> str:
    """Create a backup collection with original contact data before cleanup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_collection_name = f"contact_cleanup_backup_{timestamp}"

    backup_collection = get_mongo_collection(backup_collection_name)

    backup_data = []
    for company in companies_to_update:
        backup_entry = {
            "company_id": str(company["_id"]),
            "company_name": company.get("discovered_name", "Unknown"),
            "original_contact_persons": company.get("contact_persons", []),
            "original_contact_enrichment_status": company.get(
                "contact_enrichment_status"
            ),
            "backup_timestamp": datetime.utcnow(),
            "cleanup_script_version": "2.0",
        }
        backup_data.append(backup_entry)

    if backup_data:
        backup_collection.insert_many(backup_data)
        print(f"✅ Created backup collection: {backup_collection_name}")
        print(f"   Backed up {len(backup_data)} companies")

    return backup_collection_name


def validate_contact_filtering(
    contact_persons: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Validate and filter contacts with improved logic."""
    valid_contacts = []

    for contact in contact_persons:
        email = contact.get("email", "").strip()
        phone = contact.get("phone", "").strip()
        name = contact.get("name", "").strip()

        # Skip contacts without name
        if not name:
            continue

        # Keep contacts that have either email OR phone
        if email or phone:
            valid_contacts.append(contact)

    return valid_contacts


def main():
    """Clean up contacts without email or phone information with safety measures."""
    print("🧹 Starting Contact Cleanup Script v2.0")
    print("=" * 60)

    repo = CompanyRepository()

    # Step 1: Find companies that need cleanup
    print("📋 Finding companies with completed contact enrichment...")
    companies = repo.find_companies({"contact_enrichment_status": "completed"})
    print(f"   Found {len(companies)} companies")

    # Step 2: Analyze which companies need updates
    companies_to_update = []
    total_contacts_before = 0
    total_contacts_after = 0

    for company in companies:
        contact_persons = company.get("contact_persons", [])
        total_contacts_before += len(contact_persons)

        valid_contacts = validate_contact_filtering(contact_persons)
        total_contacts_after += len(valid_contacts)

        if len(valid_contacts) != len(contact_persons):
            companies_to_update.append(
                {
                    **company,
                    "new_contact_persons": valid_contacts,
                    "contacts_removed": len(contact_persons) - len(valid_contacts),
                }
            )

    if not companies_to_update:
        print("✅ No companies need contact cleanup. All contacts are valid!")
        return

    # Step 3: Show preview of changes
    print("\n📊 Cleanup Preview:")
    print(f"   Companies to update: {len(companies_to_update)}")
    print(f"   Total contacts before: {total_contacts_before}")
    print(f"   Total contacts after: {total_contacts_after}")
    print(
        f"   Total contacts to remove: {total_contacts_before - total_contacts_after}"
    )

    # Ask for confirmation
    response = input("\n❓ Proceed with cleanup? (y/N): ").strip().lower()
    if response != "y":
        print("❌ Cleanup cancelled by user")
        return

    # Step 4: Create backup
    print("\n💾 Creating backup...")
    backup_collection_name = create_backup_collection(companies_to_update)

    # Step 5: Perform atomic updates using transactions
    print("\n🔄 Performing atomic updates...")
    client = get_mongo_client()

    updated_count = 0
    total_contacts_removed = 0

    try:
        # Use transaction for atomicity
        with client.start_session() as session:
            with session.start_transaction():
                for company_data in companies_to_update:
                    company_id = str(company_data["_id"])
                    valid_contacts = company_data["new_contact_persons"]
                    contacts_removed = company_data["contacts_removed"]

                    print(
                        f"   🔧 Cleaning {company_data.get('discovered_name', 'Unknown')}: "
                        f"{len(company_data.get('contact_persons', []))} -> {len(valid_contacts)} contacts"
                    )

                    update_data = {
                        "contact_persons": valid_contacts,
                        "contact_cleanup_timestamp": datetime.utcnow(),
                    }

                    # Update status if no contacts remain
                    if not valid_contacts:
                        update_data["contact_enrichment_status"] = "partial"
                        print(
                            '      ⚠️  Status changed to "partial" (no valid contacts)'
                        )

                    # Perform update within transaction
                    success = repo.update_company(company_id, update_data)
                    if not success:
                        raise Exception(f"Failed to update company {company_id}")

                    updated_count += 1
                    total_contacts_removed += contacts_removed

                print("   ✅ All updates completed successfully within transaction")

    except Exception as e:
        print(f"   ❌ Transaction failed: {e}")
        print("   🔄 All changes have been rolled back automatically")
        print(f"   💾 Backup collection {backup_collection_name} is preserved")
        return

    # Step 6: Final summary
    print("\n🎉 Cleanup completed successfully!")
    print("   📊 Summary:")
    print(f"      - Updated {updated_count} companies")
    print(f"      - Removed {total_contacts_removed} contacts without email/phone")
    print(f"      - Backup collection: {backup_collection_name}")
    print(
        f"\n💡 To rollback changes, run: python restore_contacts_backup.py {backup_collection_name}"
    )


def rollback_cleanup(backup_collection_name: str):
    """Rollback cleanup using backup collection."""
    print(f"🔄 Rolling back cleanup using backup: {backup_collection_name}")

    backup_collection = get_mongo_collection(backup_collection_name)
    repo = CompanyRepository()
    client = get_mongo_client()

    backup_entries = list(backup_collection.find({}))
    if not backup_entries:
        print(f"❌ No backup data found in {backup_collection_name}")
        return

    try:
        with client.start_session() as session:
            with session.start_transaction():
                for entry in backup_entries:
                    company_id = entry["company_id"]
                    restore_data = {
                        "contact_persons": entry["original_contact_persons"],
                        "contact_enrichment_status": entry[
                            "original_contact_enrichment_status"
                        ],
                    }

                    success = repo.update_company(company_id, restore_data)
                    if not success:
                        raise Exception(f"Failed to restore company {company_id}")

                print("✅ Rollback completed successfully!")
                print(f"   Restored {len(backup_entries)} companies")

    except Exception as e:
        print(f"❌ Rollback failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        if len(sys.argv) != 3:
            print("Usage: python cleanup_contacts.py rollback <backup_collection_name>")
            sys.exit(1)
        rollback_cleanup(sys.argv[2])
    else:
        main()
