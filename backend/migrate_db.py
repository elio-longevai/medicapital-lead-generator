#!/usr/bin/env python3
"""
Database migration script to add new fields to the Company model.
Run this to update your existing database with the new fields.
"""

import sqlite3
from pathlib import Path
import logging


def migrate_database():
    """Add new columns to the companies table if they don't exist."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Find the database file - check both locations
    db_path = Path("medicapital.db")  # Project root from backend dir
    if not db_path.exists():
        db_path = Path("backend/medicapital.db")  # Current directory
        if not db_path.exists():
            logging.error("❌ Database file not found at expected locations.")
            return

    logging.info(f"💾 Using database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(companies)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    # New columns to add
    new_columns = [
        ("contact_email", "TEXT"),
        ("contact_phone", "TEXT"),
        ("employee_count", "TEXT"),
        ("estimated_revenue", "TEXT"),
        ("equipment_needs", "TEXT"),
        ("estimated_deal_value", "TEXT"),
        ("recent_news", "TEXT"),
        ("qualification_details", "TEXT"),  # JSON stored as TEXT in SQLite
        ("location_details", "TEXT"),
    ]

    logging.info(f"🧐 Found {len(existing_columns)} existing columns")

    # Add missing columns
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(
                    f"ALTER TABLE companies ADD COLUMN {column_name} {column_type}"
                )
                logging.info(f"✅ Added column: {column_name}")
            except sqlite3.Error as e:
                logging.error(f"❌ Error adding {column_name}: {e}")
        else:
            logging.info(f"⏭️  Column {column_name} already exists")

    conn.commit()
    conn.close()
    logging.info("\n🎉 Database migration completed!")


if __name__ == "__main__":
    migrate_database()
