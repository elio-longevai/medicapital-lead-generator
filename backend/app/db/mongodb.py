from typing import Optional
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.database import Database
from pymongo.collection import Collection
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""

    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None

    def connect(self):
        """Establish connection to MongoDB."""
        try:
            # Use MongoDB URI from environment
            uri = settings.MONGODB_URI

            # Create client with server API version and TLS settings for MongoDB Atlas
            self.client = MongoClient(
                uri,
                server_api=ServerApi("1"),
                tlsAllowInvalidCertificates=True,
                tlsAllowInvalidHostnames=True,
            )

            # Test the connection
            self.client.admin.command("ping")
            logger.info("✅ Successfully connected to MongoDB!")

            # Get database
            self.database = self.client[settings.MONGODB_DATABASE]

        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            logger.info("MongoDB connection closed")

    def get_collection(self, collection_name: str) -> Collection:
        """Get a collection from the database."""
        if self.database is None:
            self.connect()
        return self.database[collection_name]

    def get_database(self) -> Database:
        """Get the database instance."""
        if self.database is None:
            self.connect()
        return self.database


# Global MongoDB instance
mongodb = MongoDB()


def get_mongo_db() -> Database:
    """Get MongoDB database instance for dependency injection."""
    if mongodb.database is None:
        mongodb.connect()
    return mongodb.database


def get_mongo_collection(collection_name: str) -> Collection:
    """Get MongoDB collection for dependency injection."""
    if mongodb.database is None:
        mongodb.connect()
    return mongodb.database[collection_name]


def get_mongo_client() -> MongoClient:
    """Get MongoDB client instance for transactions."""
    if mongodb.client is None:
        mongodb.connect()
    return mongodb.client
