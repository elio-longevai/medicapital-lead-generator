from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from .models import (
    CompanyResponse,
    CompanyListResponse,
    DashboardStats,
    CompanyStatusUpdate,
)
from ..db.session import get_db
from ..db.models import Company
from ..services.company_service import CompanyService
import logging

app = FastAPI(title="MediCapital Lead API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # Frontend URL
        "http://localhost:5173",  # Default Vite dev port
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
    limit: int = 100,
    icp_name: Optional[str] = None,
    status: Optional[str] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "score",
    db: Session = Depends(get_db),
):
    """Get companies with filtering and pagination"""
    service = CompanyService(db)
    return service.get_companies_with_filters(
        skip=skip,
        limit=limit,
        icp_name=icp_name,
        status=status,
        country=country,
        search=search,
        sort_by=sort_by,
    )


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    """Get details for a single company."""
    service = CompanyService(db)
    company = service.get_company_by_id(company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@app.patch("/api/companies/{company_id}/status", response_model=CompanyResponse)
def update_company_status(
    company_id: int,
    status_update: CompanyStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update the status of a company (e.g., 'contacted', 'rejected')."""
    service = CompanyService(db)
    updated_company = service.update_company_status(company_id, status_update.status)

    if not updated_company:
        # Check if company exists at all
        company_exists = db.query(Company.id).filter(Company.id == company_id).first()
        if not company_exists:
            raise HTTPException(status_code=404, detail="Company not found")
        # If it exists, the status must have been invalid
        raise HTTPException(
            status_code=400, detail=f"Invalid status: '{status_update.status}'"
        )

    return updated_company


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    service = CompanyService(db)
    return service.get_dashboard_statistics()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
