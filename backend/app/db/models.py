import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    normalized_name = Column(String, nullable=False, unique=True, index=True)
    discovered_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    country = Column(String(2), nullable=False)
    primary_industry = Column(String, nullable=True)
    initial_reasoning = Column(Text, nullable=False)
    status = Column(String, default="discovered", nullable=False, index=True)

    # For Sprint 2+
    website_url = Column(String, nullable=True)
    enriched_data = Column(Text, nullable=True)

    # For Sprint 3+
    qualification_score = Column(Integer, nullable=True)
    qualification_reasoning = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    __table_args__ = (UniqueConstraint("normalized_name", name="uq_normalized_name"),)

    def __repr__(self):
        return f"<Company(name='{self.discovered_name}', status='{self.status}')>"
