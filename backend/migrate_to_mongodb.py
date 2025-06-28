#!/usr/bin/env python3
"""
Data migration script from SQLite to MongoDB.
This script migrates all data from the existing SQLite database to MongoDB.
"""

import logging

# SQLAlchemy imports for reading from SQLite
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Company, ApiUsage, SearchQuery, Lead

# MongoDB imports
from app.db.mongodb import get_mongo_db, mongodb
from app.db.mongo_models import COLLECTIONS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Handles migration from SQLite to MongoDB."""

    def __init__(self):
        # SQLite connection
        self.sqlite_engine = create_engine("sqlite:///./medicapital.db")
        self.SQLiteSession = sessionmaker(bind=self.sqlite_engine)

        # MongoDB connection
        self.mongo_db = None

    def setup_mongodb(self):
        """Initialize MongoDB connection."""
        try:
            self.mongo_db = get_mongo_db()
            logger.info("✅ Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def migrate_companies(self) -> int:
        """Migrate companies data."""
        logger.info("🏢 Starting companies migration...")

        sqlite_session = self.SQLiteSession()
        companies_collection = self.mongo_db[COLLECTIONS["companies"]]
        migrated_count = 0

        try:
            # Get all companies from SQLite
            companies = sqlite_session.query(Company).all()
            logger.info(f"Found {len(companies)} companies to migrate")

            for company in companies:
                try:
                    # Convert SQLAlchemy model to MongoDB document
                    company_doc = {
                        "icp_name": company.icp_name,
                        "normalized_name": company.normalized_name,
                        "discovered_name": company.discovered_name,
                        "source_url": company.source_url,
                        "country": company.country,
                        "primary_industry": company.primary_industry,
                        "initial_reasoning": company.initial_reasoning,
                        "status": company.status,
                        "website_url": company.website_url,
                        "enriched_data": company.enriched_data,
                        "qualification_score": company.qualification_score,
                        "qualification_reasoning": company.qualification_reasoning,
                        "company_description": company.company_description,
                        "contact_email": company.contact_email,
                        "contact_phone": company.contact_phone,
                        "employee_count": company.employee_count,
                        "equipment_needs": company.equipment_needs,
                        "recent_news": company.recent_news,
                        "qualification_details": company.qualification_details,
                        "location_details": company.location_details,
                        "estimated_revenue": company.estimated_revenue,
                        "created_at": company.created_at,
                        "updated_at": company.updated_at,
                    }

                    # Insert into MongoDB
                    result = companies_collection.insert_one(company_doc)
                    if result.inserted_id:
                        migrated_count += 1
                        logger.debug(f"Migrated company: {company.discovered_name}")

                except Exception as e:
                    logger.error(
                        f"Failed to migrate company {company.discovered_name}: {e}"
                    )
                    continue

            logger.info(f"✅ Successfully migrated {migrated_count} companies")
            return migrated_count

        except Exception as e:
            logger.error(f"❌ Error during companies migration: {e}")
            raise
        finally:
            sqlite_session.close()

    def migrate_api_usage(self) -> int:
        """Migrate API usage data."""
        logger.info("📊 Starting API usage migration...")

        sqlite_session = self.SQLiteSession()
        api_usage_collection = self.mongo_db[COLLECTIONS["api_usage"]]
        migrated_count = 0

        try:
            # Get all API usage records from SQLite
            api_usages = sqlite_session.query(ApiUsage).all()
            logger.info(f"Found {len(api_usages)} API usage records to migrate")

            for api_usage in api_usages:
                try:
                    api_usage_doc = {
                        "api_name": api_usage.api_name,
                        "date": api_usage.date.isoformat() if api_usage.date else None,
                        "count": api_usage.count,
                    }

                    result = api_usage_collection.insert_one(api_usage_doc)
                    if result.inserted_id:
                        migrated_count += 1
                        logger.debug(
                            f"Migrated API usage: {api_usage.api_name} - {api_usage.date}"
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to migrate API usage {api_usage.api_name}: {e}"
                    )
                    continue

            logger.info(f"✅ Successfully migrated {migrated_count} API usage records")
            return migrated_count

        except Exception as e:
            logger.error(f"❌ Error during API usage migration: {e}")
            raise
        finally:
            sqlite_session.close()

    def migrate_search_queries(self) -> int:
        """Migrate search queries data."""
        logger.info("🔍 Starting search queries migration...")

        sqlite_session = self.SQLiteSession()
        search_queries_collection = self.mongo_db[COLLECTIONS["search_queries"]]
        migrated_count = 0

        try:
            # Get all search queries from SQLite
            search_queries = sqlite_session.query(SearchQuery).all()
            logger.info(f"Found {len(search_queries)} search queries to migrate")

            for search_query in search_queries:
                try:
                    search_query_doc = {
                        "query_text": search_query.query_text,
                        "country": search_query.country,
                        "query_hash": search_query.query_hash,
                        "used_at": search_query.used_at,
                        "results_count": search_query.results_count,
                        "providers_used": search_query.providers_used,
                        "success": search_query.success,
                    }

                    result = search_queries_collection.insert_one(search_query_doc)
                    if result.inserted_id:
                        migrated_count += 1
                        logger.debug(
                            f"Migrated search query: {search_query.query_text[:50]}..."
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to migrate search query {search_query.query_hash}: {e}"
                    )
                    continue

            logger.info(f"✅ Successfully migrated {migrated_count} search queries")
            return migrated_count

        except Exception as e:
            logger.error(f"❌ Error during search queries migration: {e}")
            raise
        finally:
            sqlite_session.close()

    def migrate_leads(self) -> int:
        """Migrate leads data."""
        logger.info("🎯 Starting leads migration...")

        sqlite_session = self.SQLiteSession()
        leads_collection = self.mongo_db[COLLECTIONS["leads"]]
        migrated_count = 0

        try:
            # Get all leads from SQLite
            leads = sqlite_session.query(Lead).all()
            logger.info(f"Found {len(leads)} leads to migrate")

            for lead in leads:
                try:
                    lead_doc = {
                        "icp_name": lead.icp_name,
                        "status": lead.status,
                        "company_name": lead.company_name,
                        "source_url": lead.source_url,
                    }

                    result = leads_collection.insert_one(lead_doc)
                    if result.inserted_id:
                        migrated_count += 1
                        logger.debug(f"Migrated lead: {lead.company_name}")

                except Exception as e:
                    logger.error(f"Failed to migrate lead {lead.company_name}: {e}")
                    continue

            logger.info(f"✅ Successfully migrated {migrated_count} leads")
            return migrated_count

        except Exception as e:
            logger.error(f"❌ Error during leads migration: {e}")
            raise
        finally:
            sqlite_session.close()

    def create_indexes(self):
        """Create indexes in MongoDB for better performance."""
        logger.info("🔧 Creating MongoDB indexes...")

        try:
            # Companies collection indexes
            companies_collection = self.mongo_db[COLLECTIONS["companies"]]
            companies_collection.create_index("normalized_name", unique=True)
            companies_collection.create_index("icp_name")
            companies_collection.create_index("status")
            companies_collection.create_index("qualification_score")

            # Search queries collection indexes
            search_queries_collection = self.mongo_db[COLLECTIONS["search_queries"]]
            search_queries_collection.create_index("query_hash", unique=True)
            search_queries_collection.create_index("query_text")

            # API usage collection indexes
            api_usage_collection = self.mongo_db[COLLECTIONS["api_usage"]]
            api_usage_collection.create_index(
                [("api_name", 1), ("date", 1)], unique=True
            )

            # Leads collection indexes
            leads_collection = self.mongo_db[COLLECTIONS["leads"]]
            leads_collection.create_index("source_url", unique=True)
            leads_collection.create_index("icp_name")
            leads_collection.create_index("status")

            logger.info("✅ Successfully created MongoDB indexes")

        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
            raise

    def run_migration(self):
        """Run the complete migration process."""
        logger.info("🚀 Starting SQLite to MongoDB migration...")

        try:
            # Setup MongoDB connection
            self.setup_mongodb()

            # Run migrations
            companies_count = self.migrate_companies()
            api_usage_count = self.migrate_api_usage()
            search_queries_count = self.migrate_search_queries()
            leads_count = self.migrate_leads()

            # Create indexes
            self.create_indexes()

            # Summary
            total_migrated = (
                companies_count + api_usage_count + search_queries_count + leads_count
            )
            logger.info("=" * 60)
            logger.info("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("📊 Migration Summary:")
            logger.info(f"   • Companies: {companies_count}")
            logger.info(f"   • API Usage: {api_usage_count}")
            logger.info(f"   • Search Queries: {search_queries_count}")
            logger.info(f"   • Leads: {leads_count}")
            logger.info(f"   • Total: {total_migrated} records")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
        finally:
            # Close MongoDB connection
            if mongodb.client:
                mongodb.disconnect()


def main():
    """Main migration function."""
    migrator = DataMigrator()
    migrator.run_migration()


if __name__ == "__main__":
    main()
