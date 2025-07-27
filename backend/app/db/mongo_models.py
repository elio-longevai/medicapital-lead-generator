import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic compatibility."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema

        def validate_from_str(value: str) -> ObjectId:
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid ObjectId")
            return ObjectId(value)

        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(ObjectId),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return {"type": "string"}


# MongoDB Document Models


class CompanyDocument(BaseModel):
    """MongoDB document model for Company."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    icp_name: Optional[str] = None
    normalized_name: str = Field(
        ..., description="Normalized company name for deduplication"
    )
    discovered_name: str
    source_url: str
    country: str = Field(..., max_length=2)
    primary_industry: Optional[str] = None
    initial_reasoning: str
    status: str = Field(default="discovered")
    entity_type: Optional[str] = None
    sub_industry: Optional[str] = None
    contacts: Optional[List[Dict[str, Any]]] = None

    # For Sprint 2+
    website_url: Optional[str] = None
    enriched_data: Optional[Dict[str, Any]] = None

    # For Sprint 3+
    qualification_score: Optional[int] = None
    qualification_reasoning: Optional[str] = None

    # Enhanced fields
    company_description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    employee_count: Optional[str] = None
    equipment_needs: Optional[str] = None
    recent_news: Optional[str] = None
    qualification_details: Optional[Dict[str, Any]] = None
    location_details: Optional[str] = None
    estimated_revenue: Optional[str] = None

    # Contact enrichment fields
    contact_persons: Optional[List[Dict[str, Any]]] = None
    contact_enrichment_status: Optional[str] = None
    contact_enriched_at: Optional[datetime.datetime] = None

    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class ApiUsageDocument(BaseModel):
    """MongoDB document model for API Usage tracking."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime.date: str},
    )

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    api_name: str
    date: datetime.date = Field(default_factory=datetime.date.today)
    count: int = Field(default=1)


class SearchQueryDocument(BaseModel):
    """MongoDB document model for Search Query tracking."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    query_text: str
    country: str = Field(..., max_length=2)
    query_hash: str = Field(
        ..., description="Unique hash for query+country combination"
    )
    used_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    results_count: int = Field(default=0)
    providers_used: Optional[List[str]] = None
    success: bool = Field(default=True)


class LeadDocument(BaseModel):
    """MongoDB document model for Lead tracking."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    icp_name: Optional[str] = None
    status: str = Field(default="NEW")
    company_name: str
    source_url: str = Field(..., description="Unique source URL for the lead")


# Collection names
COLLECTIONS = {
    "companies": "companies",
    "api_usage": "api_usage",
    "search_queries": "search_queries",
    "leads": "leads",
}
