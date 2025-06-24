import sqlite3
from pathlib import Path
import logging


def update_database_schema():
    """
    Updates the database schema by adding missing columns
    to the 'companies' table if they don't already exist.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # The database is expected to be in the same directory as this script.
    db_path = Path(__file__).parent / "medicapital.db"

    if not db_path.exists():
        logging.error(f"❌ Database file not found at: {db_path}")
        return

    logging.info(f"💾 Using database: {db_path}")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get existing columns from the 'companies' table
        cursor.execute("PRAGMA table_info(companies)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        logging.info(
            f"🧐 Found {len(existing_columns)} existing columns in 'companies' table."
        )

        # Define all columns that should exist based on the Company model
        required_columns = {
            "icp_name": "TEXT",
            "company_description": "TEXT",
            "contact_email": "TEXT",
            "contact_phone": "TEXT",
            "employee_count": "TEXT",
            "equipment_needs": "TEXT",
            "recent_news": "TEXT",
            "qualification_details": "TEXT",
            "location_details": "TEXT",
            "estimated_revenue": "TEXT",
        }

        # Add missing columns
        for column_name, column_type in required_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(
                        f"ALTER TABLE companies ADD COLUMN {column_name} {column_type}"
                    )
                    logging.info(f"✅ Added column: {column_name}")
                except sqlite3.Error as e:
                    logging.error(f"❌ Error adding '{column_name}': {e}")
            else:
                logging.info(f"⏭️  Column '{column_name}' already exists.")

        conn.commit()
        logging.info("\n🎉 Schema update check completed!")

    except sqlite3.Error as e:
        logging.error(f"❌ Database connection error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    update_database_schema()
