import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    UniqueConstraint,
    JSON,
    Date,
    Boolean,
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    icp_name: Mapped[str] = mapped_column(String, nullable=True, index=True)
    normalized_name = Column(String, nullable=False, unique=True, index=True)
    discovered_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url = Column(String, nullable=False)
    country = Column(String(2), nullable=False)
    primary_industry = Column(String, nullable=True)
    initial_reasoning = Column(Text, nullable=False)
    status = Column(String, default="discovered", nullable=False, index=True)

    # For Sprint 2+
    website_url = Column(String, nullable=True)
    enriched_data: Mapped[dict] = mapped_column(
        JSON, nullable=True
    )  # For storing the raw enrichment JSON

    # For Sprint 3+
    qualification_score: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    qualification_reasoning = Column(Text, nullable=True)

    # New enhanced fields
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    employee_count = Column(String, nullable=True)  # e.g., "10-50", "100-250"
    estimated_revenue = Column(String, nullable=True)  # e.g., "€1M-5M"
    equipment_needs = Column(Text, nullable=True)  # Specific equipment requirements
    estimated_deal_value = Column(String, nullable=True)  # e.g., "€35,000-€125,000"
    recent_news = Column(Text, nullable=True)  # Latest company news/developments
    qualification_details = Column(
        JSON, nullable=True
    )  # Detailed qualification breakdown
    location_details = Column(String, nullable=True)  # Full location (city, country)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    __table_args__ = (UniqueConstraint("normalized_name", name="uq_normalized_name"),)

    def __repr__(self):
        return f"<Company(name='{self.discovered_name}', status='{self.status}')>"


class ApiUsage(Base):
    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String, nullable=False, index=True)
    date = Column(Date, default=datetime.date.today, nullable=False)
    count = Column(Integer, default=1, nullable=False)

    __table_args__ = (UniqueConstraint("api_name", "date", name="uq_api_date"),)

    def __repr__(self):
        return (
            f"<ApiUsage(api='{self.api_name}', date='{self.date}', count={self.count})>"
        )


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String, nullable=False, index=True)
    country = Column(String(2), nullable=False)
    query_hash = Column(
        String, nullable=False, unique=True, index=True
    )  # MD5 hash of query+country
    used_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    results_count = Column(Integer, default=0, nullable=False)
    providers_used = Column(
        JSON, nullable=True
    )  # List of providers that executed this query
    success = Column(Boolean, default=True, nullable=False)

    __table_args__ = (UniqueConstraint("query_hash", name="uq_query_hash"),)

    def __repr__(self):
        return f"<SearchQuery(query='{self.query_text[:50]}...', country='{self.country}', used_at='{self.used_at}')>"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    icp_name: Mapped[str] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="NEW", index=True)
    company_name: Mapped[str] = mapped_column(String, index=True)
    source_url: Mapped[str] = mapped_column(String, unique=True, index=True)
