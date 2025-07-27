import logging
from datetime import datetime
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..main import arun_all_icps
from ..services.company_service import CompanyService
from .models import (
    CompanyListResponse,
    CompanyResponse,
    CompanyStatusUpdate,
    DashboardStats,
    ScrapingStatus,
)

app = FastAPI(title="MediCapital Lead API", version="1.0.0")

# Global scraping status tracker
_scraping_status = {"is_scraping": False}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # Frontend URL
        "http://localhost:5173",  # Default Vite dev port
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error in {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500, content={"detail": "An internal server error occurred"}
    )


@app.get("/api/companies", response_model=CompanyListResponse)
def get_companies(
    skip: int = 0,
    icp_name: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    entity_type: Optional[str] = None,
    sub_industry: Optional[str] = None,
    sort_by: str = "score",
):
    """Get companies with filtering and pagination"""
    service = CompanyService()
    return service.get_companies_with_filters(
        skip=skip,
        icp_name=icp_name,
        status=status,
        country=country,
        search=search,
        entity_type=entity_type,
        sub_industry=sub_industry,
        sort_by=sort_by,
    )


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: str):
    """Get details for a single company."""
    service = CompanyService()
    company = service.get_company_by_id(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@app.patch("/api/companies/{company_id}/status", response_model=CompanyResponse)
def update_company_status(
    company_id: str,
    status_update: CompanyStatusUpdate,
):
    """Update the status of a company (e.g., 'contacted', 'rejected')."""
    service = CompanyService()
    updated_company = service.update_company_status(company_id, status_update.status)

    if not updated_company:
        # Check if company exists at all
        company = service.get_company_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        # If it exists, the status must have been invalid
        raise HTTPException(
            status_code=400, detail=f"Invalid status: '{status_update.status}'"
        )

    return updated_company


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats():
    """Get dashboard statistics"""
    service = CompanyService()
    return service.get_dashboard_statistics()


async def run_scraping_with_status_tracking(queries_per_icp: int):
    """
    Wrapper function to track scraping status during the process.
    """
    global _scraping_status
    _scraping_status["is_scraping"] = True
    try:
        await arun_all_icps(queries_per_icp=queries_per_icp)
    finally:
        _scraping_status["is_scraping"] = False


@app.get("/api/scrape-status", response_model=ScrapingStatus)
def get_scrape_status():
    """
    Returns the current scraping status.
    """
    return _scraping_status


@app.post("/api/scrape-leads", status_code=202)
async def scrape_leads(background_tasks: BackgroundTasks):
    """
    Triggers a new lead scraping process in the background.
    """
    if _scraping_status["is_scraping"]:
        raise HTTPException(
            status_code=409,
            detail="Scraping is already in progress. Please wait for it to complete.",
        )

    background_tasks.add_task(run_scraping_with_status_tracking, queries_per_icp=5)
    return {
        "message": "Lead scraping process started. It will take approximately 10 minutes to complete."
    }


@app.get("/api/companies/{company_id}/contacts")
def get_company_contacts(company_id: str):
    """Get detailed contact information for a company."""
    service = CompanyService()
    company = service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    contacts = company.contactPersons or []
    enrichment_status = company.contactEnrichmentStatus
    enriched_at = company.contactEnrichedAt

    return {
        "companyId": company_id,
        "companyName": company.company,
        "contacts": contacts,
        "enrichmentStatus": enrichment_status,
        "enrichedAt": enriched_at,
    }


@app.post("/api/companies/{company_id}/enrich-contacts")
async def enrich_company_contacts(company_id: str, background_tasks: BackgroundTasks):
    """Trigger contact enrichment for a specific company."""
    from app.db.repositories import CompanyRepository
    from app.services.contact_enrichment import ContactEnrichmentService

    # Get company details
    service = CompanyService()
    company = service.get_company_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company_name = company.company
    website_url = company.website

    # Start enrichment in background
    async def perform_enrichment():
        repo = CompanyRepository()
        try:
            contact_service = ContactEnrichmentService()
            result = await contact_service.enrich_company_contacts(
                company_name=company_name, website_url=website_url
            )

            # Update company record
            update_data = {
                "contact_persons": [
                    contact.model_dump() for contact in result["contacts"]
                ],
                "contact_enrichment_status": result["enrichment_status"],
                "contact_enriched_at": datetime.utcnow(),
            }
            repo.update_company(company_id, update_data)

        except Exception as e:
            logger.error(f"Contact enrichment failed for {company_name}: {str(e)}")
            # Update with error status
            repo.update_company(
                company_id,
                {
                    "contact_enrichment_status": "failed",
                    "contact_enriched_at": datetime.utcnow(),
                },
            )

    background_tasks.add_task(perform_enrichment)

    return {
        "message": f"Contact enrichment started for {company_name}",
        "companyId": company_id,
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
