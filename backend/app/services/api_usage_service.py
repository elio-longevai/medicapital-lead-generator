import datetime
import logging
from sqlalchemy.orm import Session
from app.db.models import ApiUsage

# From search.todo: API Capabilities & Daily Free Limits
API_DAILY_LIMITS = {
    "serper": 83,
    "brave": 66,
    "tavily": 33,
    "firecrawl": 16,
}

logger = logging.getLogger(__name__)


class ApiUsageService:
    def __init__(self, db: Session):
        self.db = db

    def can_use_api(self, api_name: str) -> bool:
        """Checks if an API can be used based on its daily limit."""
        api_name = api_name.lower()
        limit = API_DAILY_LIMITS.get(api_name)
        if limit is None:
            # If the API is not in our rate-limited list, allow usage.
            return True

        today = datetime.date.today()
        usage_record = (
            self.db.query(ApiUsage).filter_by(api_name=api_name, date=today).first()
        )

        if not usage_record:
            return True  # No usage recorded for today

        return usage_record.count < limit

    def increment_usage(self, api_name: str):
        """Increments the usage count for a given API."""
        api_name = api_name.lower()
        if api_name not in API_DAILY_LIMITS:
            return  # Don't track APIs that aren't in our list

        today = datetime.date.today()
        usage_record = (
            self.db.query(ApiUsage).filter_by(api_name=api_name, date=today).first()
        )

        if usage_record:
            usage_record.count += 1
        else:
            usage_record = ApiUsage(api_name=api_name, date=today, count=1)
            self.db.add(usage_record)

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error incrementing API usage: {e}", exc_info=True)
