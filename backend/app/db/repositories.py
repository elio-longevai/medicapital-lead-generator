import hashlib
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.db.mongo_models import COLLECTIONS
from app.db.mongodb import get_mongo_collection

logger = logging.getLogger(__name__)


class CompanyRepository:
    """Repository for Company document operations."""

    def __init__(self):
        self.collection: Collection = get_mongo_collection(COLLECTIONS["companies"])

    def get_all_normalized_names(self) -> set:
        """Get all normalized names from the database."""
        cursor = self.collection.find({}, {"normalized_name": 1})
        return {doc["normalized_name"] for doc in cursor}

    def find_by_normalized_name(self, normalized_name: str) -> Optional[Dict]:
        """Find company by normalized name."""
        return self.collection.find_one({"normalized_name": normalized_name})

    def create_company(self, company_data: Dict[str, Any]) -> Optional[ObjectId]:
        """Create a new company document."""
        try:
            # Add timestamps
            now = datetime.utcnow()
            company_data["created_at"] = now
            company_data["updated_at"] = now

            result = self.collection.insert_one(company_data)
            return result.inserted_id
        except DuplicateKeyError:
            logger.warning(
                f"Company with normalized_name '{company_data.get('normalized_name')}' already exists"
            )
            return None
        except Exception as e:
            logger.error(f"Error creating company: {e}")
            return None

    def update_company(
        self, company_id: Union[str, ObjectId], update_data: Dict[str, Any]
    ) -> bool:
        """Update a company document."""
        try:
            # Convert string ID to ObjectId if necessary
            if isinstance(company_id, str):
                company_id = ObjectId(company_id)

            update_data["updated_at"] = datetime.utcnow()
            result = self.collection.update_one(
                {"_id": company_id}, {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating company: {e}")
            return False

    def get_recent_companies(self, limit: int = 20) -> List[Dict]:
        """Get most recently created companies."""
        cursor = self.collection.find().sort("created_at", -1).limit(limit)
        return list(cursor)

    def count_companies(self) -> int:
        """Count total companies."""
        return self.collection.count_documents({})

    def find_by_icp_name(self, icp_name: str) -> List[Dict]:
        """Find companies by ICP name."""
        cursor = self.collection.find({"icp_name": icp_name})
        return list(cursor)

    def find_companies(self, filter_criteria: Dict[str, Any]) -> List[Dict]:
        """Find companies based on filter criteria."""
        cursor = self.collection.find(filter_criteria)
        return list(cursor)

    def find_with_filters(
        self,
        skip: int = 0,
        limit: int = 0,
        icp_name: Optional[Union[str, List[str]]] = None,
        status: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None,
        entity_type: Optional[str] = None,
        sub_industry: Optional[str] = None,
        sort_by: str = "score",
    ) -> Dict[str, Any]:
        """Find companies with filters and pagination."""

        # Build filter query
        filter_query = {}

        if icp_name and icp_name != "all":
            if isinstance(icp_name, list):
                filter_query["icp_name"] = {"$in": icp_name}
            else:
                filter_query["icp_name"] = icp_name

        if status and status != "all":
            filter_query["status"] = status
        elif not status or status == "all":
            # By default, do not show rejected leads
            filter_query["status"] = {"$ne": "rejected"}

        if country:
            filter_query["country"] = country

        if entity_type and entity_type != "all":
            filter_query["entity_type"] = entity_type

        if sub_industry:
            filter_query["sub_industry"] = {"$regex": sub_industry, "$options": "i"}

        if search:
            filter_query["$or"] = [
                {"discovered_name": {"$regex": search, "$options": "i"}},
                {"equipment_needs": {"$regex": search, "$options": "i"}},
            ]

        # Build sort query
        sort_query = []
        if sort_by == "score":
            sort_query.append(("qualification_score", -1))
        elif sort_by == "company":
            sort_query.append(("discovered_name", 1))
        elif sort_by == "activity":
            sort_query.append(("created_at", -1))

        # Get total count
        total = self.collection.count_documents(filter_query)

        # Get filtered results
        cursor = self.collection.find(filter_query)
        if sort_query:
            cursor = cursor.sort(sort_query)
        if skip > 0:
            cursor = cursor.skip(skip)
        if limit > 0:
            cursor = cursor.limit(limit)

        companies = list(cursor)

        return {"companies": companies, "total": total}

    def find_by_id(self, company_id: str) -> Optional[Dict]:
        """Find company by string ID (converts to ObjectId)."""
        try:
            object_id = ObjectId(company_id)
            return self.collection.find_one({"_id": object_id})
        except Exception as e:
            logger.error(f"Error finding company by ID {company_id}: {e}")
            return None

    def update_status(self, company_id: str, new_status: str) -> bool:
        """Update company status by ID."""
        try:
            object_id = ObjectId(company_id)
            result = self.collection.update_one(
                {"_id": object_id},
                {"$set": {"status": new_status, "updated_at": datetime.utcnow()}},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating company status: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        try:
            from datetime import datetime, timedelta

            # Total leads
            total_leads = self.collection.count_documents({})

            # Leads by status
            qualified_leads = self.collection.count_documents({"status": "qualified"})
            in_review_leads = self.collection.count_documents({"status": "in_review"})
            discovered_leads = self.collection.count_documents({"status": "discovered"})

            # Calculate time-based statistics
            now = datetime.utcnow()
            one_week_ago = now - timedelta(days=7)

            # Leads created this week
            leads_this_week = self.collection.count_documents(
                {"created_at": {"$gte": one_week_ago}}
            )

            # Average qualification score
            pipeline = [
                {"$match": {"qualification_score": {"$exists": True, "$ne": None}}},
                {
                    "$group": {
                        "_id": None,
                        "avg_score": {"$avg": "$qualification_score"},
                    }
                },
            ]
            avg_result = list(self.collection.aggregate(pipeline))
            avg_score = avg_result[0]["avg_score"] if avg_result else 75.0

            # Top ICPs
            pipeline = [
                {"$match": {"icp_name": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$icp_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 3},
            ]
            top_icps = list(self.collection.aggregate(pipeline))

            return {
                "total_leads": total_leads,
                "qualified_leads": qualified_leads,
                "in_review_leads": in_review_leads,
                "discovered_leads": discovered_leads,
                "leads_this_week": leads_this_week,
                "avg_score": float(avg_score),
                "top_icps": top_icps,
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "total_leads": 0,
                "qualified_leads": 0,
                "in_review_leads": 0,
                "discovered_leads": 0,
                "leads_this_week": 0,
                "avg_score": 75.0,
                "top_icps": [],
            }


class SearchQueryRepository:
    """Repository for SearchQuery document operations."""

    def __init__(self):
        self.collection: Collection = get_mongo_collection(
            COLLECTIONS["search_queries"]
        )

    def _generate_query_hash(self, query: str, country: str) -> str:
        """Generate a unique hash for the query+country combination."""
        combined = f"{query.lower().strip()}|{country.upper().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()

    def is_query_used(self, query: str, country: str) -> bool:
        """Check if a query has already been used."""
        query_hash = self._generate_query_hash(query, country)
        return self.collection.find_one({"query_hash": query_hash}) is not None

    def filter_unused_queries(self, queries: List[str], country: str) -> List[str]:
        """Filter out queries that have already been used."""
        unused_queries = []
        for query in queries:
            if not self.is_query_used(query, country):
                unused_queries.append(query)
            else:
                logger.info(f"🔄 Skipping already used query: {query[:50]}...")

        logger.info(
            f"📊 Filtered {len(queries)} queries → {len(unused_queries)} unused queries"
        )
        return unused_queries

    def mark_query_as_used(
        self,
        query: str,
        country: str,
        results_count: int = 0,
        providers_used: List[str] = None,
        success: bool = True,
    ) -> Optional[ObjectId]:
        """Mark a query as used in the database."""
        query_hash = self._generate_query_hash(query, country)

        search_query_doc = {
            "query_text": query,
            "country": country,
            "query_hash": query_hash,
            "used_at": datetime.utcnow(),
            "results_count": results_count,
            "providers_used": providers_used or [],
            "success": success,
        }

        try:
            result = self.collection.insert_one(search_query_doc)
            logger.info(f"✅ Marked query as used: {query[:50]}...")
            return result.inserted_id
        except DuplicateKeyError:
            # Query already exists (race condition)
            logger.warning(f"⚠️ Query already marked as used: {query[:50]}...")
            return None
        except Exception as e:
            logger.error(f"❌ Error marking query as used: {e}")
            return None

    def get_all_used_queries(self, country: str) -> List[str]:
        """Fetch all previously used query strings for a given country."""
        cursor = self.collection.find({"country": country}, {"query_text": 1})
        return [doc["query_text"] for doc in cursor]

    def mark_queries_as_used_batch(
        self,
        query_results: List[
            tuple
        ],  # [(query, country, results_count, providers_used, success), ...]
    ) -> int:
        """Mark multiple queries as used in a batch operation."""
        added_count = 0

        for query_data in query_results:
            query, country, results_count, providers_used, success = query_data
            if self.mark_query_as_used(
                query, country, results_count, providers_used, success
            ):
                added_count += 1

        logger.info(f"📝 Marked {added_count}/{len(query_results)} queries as used")
        return added_count

    def get_query_stats(self) -> Dict[str, int]:
        """Get statistics about search query usage."""
        total_queries = self.collection.count_documents({})
        successful_queries = self.collection.count_documents({"success": True})

        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": total_queries - successful_queries,
        }


class ApiUsageRepository:
    """Repository for API Usage tracking."""

    def __init__(self):
        self.collection: Collection = get_mongo_collection(COLLECTIONS["api_usage"])

    def increment_usage(self, api_name: str, usage_date: date = None) -> bool:
        """Increment usage count for an API on a specific date."""
        if usage_date is None:
            usage_date = date.today()

        # Convert date to ISO string for MongoDB compatibility
        date_str = (
            usage_date.isoformat() if isinstance(usage_date, date) else usage_date
        )

        try:
            # Try to increment existing record
            result = self.collection.update_one(
                {"api_name": api_name, "date": date_str},
                {"$inc": {"count": 1}},
                upsert=True,
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error incrementing API usage: {e}")
            return False

    def get_usage_stats(self, api_name: str) -> Dict[str, Any]:
        """Get usage statistics for an API."""
        pipeline = [
            {"$match": {"api_name": api_name}},
            {
                "$group": {
                    "_id": None,
                    "total_count": {"$sum": "$count"},
                    "days_used": {"$sum": 1},
                }
            },
        ]

        result = list(self.collection.aggregate(pipeline))
        if result:
            return {
                "api_name": api_name,
                "total_count": result[0]["total_count"],
                "days_used": result[0]["days_used"],
            }
        return {"api_name": api_name, "total_count": 0, "days_used": 0}


class LeadRepository:
    """Repository for Lead document operations."""

    def __init__(self):
        self.collection: Collection = get_mongo_collection(COLLECTIONS["leads"])

    def create_lead(self, lead_data: Dict[str, Any]) -> Optional[ObjectId]:
        """Create a new lead document."""
        try:
            result = self.collection.insert_one(lead_data)
            return result.inserted_id
        except DuplicateKeyError:
            logger.warning(
                f"Lead with source_url '{lead_data.get('source_url')}' already exists"
            )
            return None
        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            return None

    def find_by_source_url(self, source_url: str) -> Optional[Dict]:
        """Find lead by source URL."""
        return self.collection.find_one({"source_url": source_url})

    def get_leads_by_status(self, status: str) -> List[Dict]:
        """Get leads by status."""
        cursor = self.collection.find({"status": status})
        return list(cursor)


class BackgroundTaskRepository:
    """Repository for Background Task Status operations."""

    def __init__(self):
        self.collection: Collection = get_mongo_collection(
            COLLECTIONS["background_tasks"]
        )

    def get_task_status(self, task_name: str) -> str:
        """Get the current status of a background task."""
        task = self.collection.find_one({"task_name": task_name})
        return task["status"] if task else "idle"

    def set_task_running(self, task_name: str) -> bool:
        """Atomically set a task to 'running' status if it's currently 'idle'."""
        try:
            result = self.collection.find_one_and_update(
                {"task_name": task_name, "status": "idle"},
                {
                    "$set": {
                        "status": "running",
                        "started_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
                upsert=True,
                return_document=True,
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error setting task running: {e}")
            return False

    def set_task_idle(self, task_name: str) -> bool:
        """Set a task to 'idle' status."""
        try:
            result = self.collection.update_one(
                {"task_name": task_name},
                {
                    "$set": {
                        "status": "idle",
                        "updated_at": datetime.utcnow(),
                    },
                    "$unset": {"started_at": ""},
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error setting task idle: {e}")
            return False


class CircuitBreakerRepository:
    """Repository for Circuit Breaker state operations."""

    def __init__(self):
        self.collection: Collection = get_mongo_collection(
            COLLECTIONS["circuit_breaker_state"]
        )

    def get_provider_state(self, provider: str) -> Dict[str, Any]:
        """Get circuit breaker state for a provider."""
        state = self.collection.find_one({"provider": provider})
        if state:
            return {
                "failure_count": state.get("failure_count", 0),
                "disabled_until": state.get("disabled_until"),
            }
        return {"failure_count": 0, "disabled_until": None}

    def record_failure(self, provider: str, disabled_until: datetime = None) -> bool:
        """Record a failure for a provider and optionally disable it."""
        try:
            update_data = {
                "$inc": {"failure_count": 1},
                "$set": {"updated_at": datetime.utcnow()},
            }
            if disabled_until:
                update_data["$set"]["disabled_until"] = disabled_until

            result = self.collection.update_one(
                {"provider": provider},
                update_data,
                upsert=True,
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error recording failure for {provider}: {e}")
            return False

    def record_success(self, provider: str) -> bool:
        """Record a success for a provider and reset failure count."""
        try:
            result = self.collection.update_one(
                {"provider": provider},
                {
                    "$set": {
                        "failure_count": 0,
                        "updated_at": datetime.utcnow(),
                    },
                    "$unset": {"disabled_until": ""},
                },
                upsert=True,
            )
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error recording success for {provider}: {e}")
            return False
