import logging
from datetime import date
from typing import Any, Dict

from app.db.repositories import ApiUsageRepository

logger = logging.getLogger(__name__)


class ApiUsageService:
    """Service for tracking API usage statistics."""

    def __init__(self):
        self.repo = ApiUsageRepository()

    def increment_usage(self, api_name: str, usage_date: date = None) -> bool:
        """Increment usage count for an API on a specific date."""
        return self.repo.increment_usage(api_name, usage_date)

    def get_usage_stats(self, api_name: str) -> Dict[str, Any]:
        """Get usage statistics for an API."""
        return self.repo.get_usage_stats(api_name)

    def track_api_call(self, api_name: str) -> bool:
        """Track a single API call (convenience method)."""
        try:
            return self.increment_usage(api_name)
        except Exception as e:
            logger.error(f"Failed to track API call for {api_name}: {e}")
            return False
