import hashlib
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import SearchQuery
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class SearchQueryService:
    """Service for managing search query tracking and deduplication."""

    def __init__(self, db_session: Session = None):
        self.db_session = db_session or SessionLocal()
        self._should_close_session = db_session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_session:
            self.db_session.close()

    def _generate_query_hash(self, query: str, country: str) -> str:
        """Generate a unique hash for the query+country combination."""
        combined = f"{query.lower().strip()}|{country.upper().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()

    def is_query_used(self, query: str, country: str) -> bool:
        """Check if a query has already been used."""
        query_hash = self._generate_query_hash(query, country)
        existing_query = (
            self.db_session.query(SearchQuery)
            .filter(SearchQuery.query_hash == query_hash)
            .first()
        )
        return existing_query is not None

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
    ) -> Optional[SearchQuery]:
        """Mark a query as used in the database."""
        query_hash = self._generate_query_hash(query, country)

        search_query = SearchQuery(
            query_text=query,
            country=country,
            query_hash=query_hash,
            used_at=datetime.utcnow(),
            results_count=results_count,
            providers_used=providers_used or [],
            success=success,
        )

        try:
            self.db_session.add(search_query)
            self.db_session.commit()
            logger.info(f"✅ Marked query as used: {query[:50]}...")
            return search_query
        except IntegrityError:
            # Query already exists (race condition)
            self.db_session.rollback()
            logger.warning(f"⚠️ Query already marked as used: {query[:50]}...")
            return None
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"❌ Error marking query as used: {e}")
            return None

    def get_all_used_queries(self, country: str) -> List[str]:
        """Fetch all previously used query strings for a given country."""
        used_queries = (
            self.db_session.query(SearchQuery.query_text)
            .filter(SearchQuery.country == country)
            .all()
        )
        return [item[0] for item in used_queries]

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

    def get_query_stats(self) -> dict:
        """Get statistics about search query usage."""
        total_queries = self.db_session.query(SearchQuery).count()
        successful_queries = (
            self.db_session.query(SearchQuery).filter(SearchQuery.success).count()
        )

        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": total_queries - successful_queries,
        }
