import datetime
import logging
from sqlalchemy.orm import Session
from app.db.models import ApiUsage


logger = logging.getLogger(__name__)


class ApiUsageService:
    def __init__(self, db: Session):
        self.db = db

    def increment_usage(self, api_name: str):
        """Increments the usage count for a given API."""
        api_name = api_name.lower()

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
