from pydantic import BaseModel, Field


class CandidateLead(BaseModel):
    """A pre-vetted lead, extracted from search results."""

    discovered_name: str = Field(description="The name of the company as found.")
    source_url: str = Field(
        description="The URL of the page where the company was mentioned."
    )
    country: str = Field(description="The two-letter country code (e.g., 'NL', 'BE').")
    primary_industry: str = Field(
        description="The main industry of the company (e.g., 'Healthcare', 'Sustainability')."
    )
    initial_reasoning: str = Field(
        description="A brief justification for why this company is a potential lead."
    )


class GraphState(BaseModel):
    """The state object that moves through the lead generation graph."""

    raw_icp_text: str
    target_country: str  # 'NL' or 'BE'

    structured_icp: dict = Field(default_factory=dict)
    search_queries: list[str] = Field(default_factory=list)
    search_results: list[dict] = Field(default_factory=list)
    candidate_leads: list[CandidateLead] = Field(default_factory=list)
    enriched_companies: list[dict] = Field(default_factory=list)

    # For refinement loop
    refinement_attempts: int = 0
    refinement_queries: dict = Field(default_factory=dict)
    refinement_results: dict = Field(default_factory=dict)

    # Final output
    newly_saved_leads_count: int = 0
    error_message: str | None = None
