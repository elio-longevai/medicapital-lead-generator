import sqlite3
from pathlib import Path
import logging


def update_database_schema():
    """
    Updates the database schema by adding the 'icp_name' column
    to the 'leads' table if it doesn't already exist.
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

        # Add the 'icp_name' column if it's missing
        if "icp_name" not in existing_columns:
            try:
                cursor.execute("ALTER TABLE companies ADD COLUMN icp_name TEXT")
                logging.info("✅ Added column: icp_name")
            except sqlite3.Error as e:
                logging.error(f"❌ Error adding 'icp_name': {e}")
        else:
            logging.info("⏭️  Column 'icp_name' already exists.")

        conn.commit()
        logging.info("\n🎉 Schema update check completed!")

    except sqlite3.Error as e:
        logging.error(f"❌ Database connection error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    update_database_schema()
