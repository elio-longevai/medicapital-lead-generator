import hashlib
import logging
from typing import List, Dict

from app.db.repositories import SearchQueryRepository

logger = logging.getLogger(__name__)


class SearchQueryService:
    """Service for managing search query tracking and deduplication."""

    def __init__(self):
        self.repo = SearchQueryRepository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # No need to close connections with MongoDB repositories
        pass

    def _generate_query_hash(self, query: str, country: str) -> str:
        """Generate a unique hash for the query+country combination."""
        combined = f"{query.lower().strip()}|{country.upper().strip()}"
        return hashlib.md5(combined.encode()).hexdigest()

    def is_query_used(self, query: str, country: str) -> bool:
        """Check if a query has already been used."""
        return self.repo.is_query_used(query, country)

    def filter_unused_queries(self, queries: List[str], country: str) -> List[str]:
        """Filter out queries that have already been used."""
        return self.repo.filter_unused_queries(queries, country)

    def mark_query_as_used(
        self,
        query: str,
        country: str,
        results_count: int = 0,
        providers_used: List[str] = None,
        success: bool = True,
    ) -> bool:
        """Mark a query as used in the database."""
        result_id = self.repo.mark_query_as_used(
            query, country, results_count, providers_used, success
        )
        return result_id is not None

    def get_all_used_queries(self, country: str) -> List[str]:
        """Fetch all previously used query strings for a given country."""
        return self.repo.get_all_used_queries(country)

    def mark_queries_as_used_batch(
        self,
        query_results: List[
            tuple
        ],  # [(query, country, results_count, providers_used, success), ...]
    ) -> int:
        """Mark multiple queries as used in a batch operation."""
        return self.repo.mark_queries_as_used_batch(query_results)

    def get_query_stats(self) -> Dict[str, int]:
        """Get statistics about search query usage."""
        return self.repo.get_query_stats()
