"""
Database Utilities

Shared utilities for database operations, transaction management,
and common query patterns.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List

from pymongo.errors import PyMongoError

from ..db.mongodb import get_mongo_client, get_mongo_collection

logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Shared utilities for database operations and transaction management."""

    @staticmethod
    async def execute_with_transaction(
        operations: List[Callable], session_options: Dict[str, Any] = None
    ) -> bool:
        """
        Execute multiple database operations within a transaction.

        Args:
            operations: List of callable operations to execute
            session_options: Optional session configuration

        Returns:
            True if all operations succeeded, False otherwise
        """
        client = get_mongo_client()
        session_options = session_options or {}

        try:
            with client.start_session(**session_options) as session:
                with session.start_transaction():
                    for operation in operations:
                        result = operation(session)
                        if not result:
                            raise Exception(f"Operation {operation.__name__} failed")

                    logger.info(
                        f"Transaction completed successfully with {len(operations)} operations"
                    )
                    return True

        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False

    @staticmethod
    def create_backup_collection(
        original_collection_name: str,
        documents: List[Dict[str, Any]],
        backup_metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Create a backup collection with timestamped name.

        Args:
            original_collection_name: Name of original collection
            documents: Documents to backup
            backup_metadata: Additional metadata to include

        Returns:
            Name of backup collection created
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_collection_name = f"{original_collection_name}_backup_{timestamp}"

        backup_collection = get_mongo_collection(backup_collection_name)

        backup_documents = []
        for doc in documents:
            backup_doc = {
                **doc,
                "backup_timestamp": datetime.utcnow(),
                "original_collection": original_collection_name,
                **(backup_metadata or {}),
            }
            backup_documents.append(backup_doc)

        if backup_documents:
            backup_collection.insert_many(backup_documents)
            logger.info(
                f"Created backup collection: {backup_collection_name} with {len(backup_documents)} documents"
            )

        return backup_collection_name

    @staticmethod
    def build_filter_query(**filters) -> Dict[str, Any]:
        """
        Build MongoDB filter query from keyword arguments.

        Args:
            **filters: Filter criteria as keyword arguments

        Returns:
            MongoDB filter query
        """
        query = {}

        for key, value in filters.items():
            if value is not None:
                if key.endswith("_status") and value == "all":
                    # Skip status filter if "all" is specified
                    continue
                elif key.endswith("_search") and value:
                    # Text search filter
                    query["$text"] = {"$search": value}
                elif key.endswith("_regex") and value:
                    # Regex filter
                    field_name = key.replace("_regex", "")
                    query[field_name] = {"$regex": value, "$options": "i"}
                elif key.endswith("_in") and isinstance(value, list):
                    # "In" filter for arrays
                    field_name = key.replace("_in", "")
                    query[field_name] = {"$in": value}
                elif key.endswith("_exists"):
                    # Existence filter
                    field_name = key.replace("_exists", "")
                    query[field_name] = {"$exists": value}
                else:
                    # Exact match filter
                    query[key] = value

        return query

    @staticmethod
    def build_sort_query(
        sort_by: str, default_sort: Dict[str, int] = None
    ) -> List[tuple]:
        """
        Build MongoDB sort query from sort string.

        Args:
            sort_by: Sort criteria (e.g., "created_at_desc", "score_asc")
            default_sort: Default sort if sort_by is invalid

        Returns:
            MongoDB sort query as list of tuples
        """
        default_sort = default_sort or [("created_at", -1)]

        if not sort_by:
            return default_sort

        sort_mapping = {
            "score_desc": [("qualification_score", -1)],
            "score_asc": [("qualification_score", 1)],
            "created_desc": [("created_at", -1)],
            "created_asc": [("created_at", 1)],
            "updated_desc": [("updated_at", -1)],
            "updated_asc": [("updated_at", 1)],
            "company_asc": [("discovered_name", 1)],
            "company_desc": [("discovered_name", -1)],
        }

        return sort_mapping.get(sort_by, default_sort)

    @staticmethod
    def safe_update_document(
        collection_name: str,
        document_id: str,
        update_data: Dict[str, Any],
        upsert: bool = False,
    ) -> bool:
        """
        Safely update a document with error handling.

        Args:
            collection_name: Name of collection
            document_id: Document ID to update
            update_data: Data to update
            upsert: Whether to insert if document doesn't exist

        Returns:
            True if update succeeded, False otherwise
        """
        try:
            collection = get_mongo_collection(collection_name)

            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()

            result = collection.update_one(
                {"_id": document_id}, {"$set": update_data}, upsert=upsert
            )

            if result.modified_count > 0 or result.upserted_id:
                logger.debug(
                    f"Successfully updated document {document_id} in {collection_name}"
                )
                return True
            else:
                logger.warning(
                    f"No document found to update: {document_id} in {collection_name}"
                )
                return False

        except PyMongoError as e:
            logger.error(
                f"Database error updating {document_id} in {collection_name}: {e}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error updating {document_id} in {collection_name}: {e}"
            )
            return False

    @staticmethod
    def bulk_update_documents(
        collection_name: str, updates: List[Dict[str, Any]], key_field: str = "_id"
    ) -> Dict[str, int]:
        """
        Perform bulk updates on documents.

        Args:
            collection_name: Name of collection
            updates: List of update operations with 'filter' and 'update' keys
            key_field: Field to use for matching documents

        Returns:
            Statistics about the bulk operation
        """
        try:
            collection = get_mongo_collection(collection_name)

            bulk_operations = []
            for update_op in updates:
                filter_query = {key_field: update_op["filter"]}
                update_data = {**update_op["update"], "updated_at": datetime.utcnow()}

                bulk_operations.append(
                    {
                        "update_one": {
                            "filter": filter_query,
                            "update": {"$set": update_data},
                        }
                    }
                )

            if bulk_operations:
                result = collection.bulk_write(bulk_operations)

                stats = {
                    "matched_count": result.matched_count,
                    "modified_count": result.modified_count,
                    "upserted_count": result.upserted_count,
                }

                logger.info(f"Bulk update completed on {collection_name}: {stats}")
                return stats

            return {"matched_count": 0, "modified_count": 0, "upserted_count": 0}

        except PyMongoError as e:
            logger.error(f"Database error in bulk update for {collection_name}: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in bulk update for {collection_name}: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_collection_statistics(collection_name: str) -> Dict[str, Any]:
        """
        Get basic statistics about a collection.

        Args:
            collection_name: Name of collection

        Returns:
            Collection statistics
        """
        try:
            collection = get_mongo_collection(collection_name)

            total_count = collection.count_documents({})

            # Get creation date range
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "min_created": {"$min": "$created_at"},
                        "max_created": {"$max": "$created_at"},
                        "avg_updated": {"$avg": "$updated_at"},
                    }
                }
            ]

            date_stats = list(collection.aggregate(pipeline))

            stats = {
                "total_documents": total_count,
                "collection_name": collection_name,
                "statistics_generated_at": datetime.utcnow(),
            }

            if date_stats:
                stats.update(
                    {
                        "earliest_created": date_stats[0].get("min_created"),
                        "latest_created": date_stats[0].get("max_created"),
                    }
                )

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics for {collection_name}: {e}")
            return {"error": str(e)}
