# Frontend-Backend Integration Plan

## Current State Analysis

### Backend Database Schema (Company model)
- `id`: Primary key
- `normalized_name`: Unique normalized company name
- `discovered_name`: Original company name as found
- `source_url`: URL where company was discovered
- `country`: Two-letter country code (NL/BE)
- `primary_industry`: Main industry sector
- `initial_reasoning`: Why this is a potential lead
- `status`: Current status (default: "discovered")
- `website_url`: Company website (nullable)
- `enriched_data`: Additional data as text (nullable)
- `qualification_score`: Numeric score (nullable)
- `qualification_reasoning`: Text reasoning (nullable)
- `created_at`, `updated_at`: Timestamps

### Frontend Mock Data Structure
- Much richer structure with fields like `score`, `equipmentNeed`, `estimatedValue`, `employees`, `email`, `phone`, `notes`, `recentNews`, `qualificationScore` object

## Implementation Steps

### 1. Create FastAPI Backend Server
- Add FastAPI dependency to requirements
- Create API routes for:
  - GET /api/companies - List all companies with filtering/sorting
  - GET /api/companies/{id} - Get single company details
  - GET /api/companies/stats - Dashboard statistics
  - PUT /api/companies/{id} - Update company data
  - POST /api/companies/{id}/notes - Add notes

### 2. Data Transformation Layer
- Create Pydantic models for API responses
- Map database fields to frontend-expected structure
- Handle missing fields gracefully with defaults
- Calculate derived fields (like overall score from qualification_score)

### 3. Frontend API Integration
- Create API client service using fetch/axios
- Replace mock data with API calls
- Add loading states and error handling
- Implement React Query for caching and state management

### 4. Database Migration Preparation
- Abstract database access behind repository pattern
- Create database adapter interface
- Prepare for PostgreSQL/MongoDB migration by using environment-based configuration

### 5. Enhanced Data Model
- Extend Company model with additional fields needed by frontend
- Create migration scripts for new fields
- Add JSON fields for flexible data storage

## Field Mapping Strategy

### Direct Mappings
- `id` → `id`
- `discovered_name` → `company`
- `primary_industry` → `industry`
- `country` → `location` (with formatting)
- `status` → `status`
- `source_url` → `website` (fallback)
- `created_at` → `lastActivity`

### Calculated/Default Fields
- `score` → Calculate from `qualification_score` or default to 75
- `equipmentNeed` → Extract from `initial_reasoning` or default
- `estimatedValue` → Calculate based on industry/size or default
- `employees` → Default based on industry patterns
- `email`, `phone` → Extract from `enriched_data` or defaults
- `notes` → Use `initial_reasoning`
- `recentNews` → Extract from `enriched_data` or generate

### Enhanced Qualification System
- Store qualification breakdown in JSON field
- Calculate component scores for financial stability, equipment need, timing, decision authority
- Provide API endpoints for updating qualification data

## Database Future-Proofing

### Configuration-Based Database Access
```python
# Support multiple database types
DATABASE_TYPE = "sqlite"  # or "postgresql", "mongodb"
DATABASE_URL = "sqlite:///./medicapital.db"  # or postgres://... or mongodb://...
```

### Repository Pattern
```python
class CompanyRepository:
    def get_all(self, filters: dict) -> List[Company]
    def get_by_id(self, id: int) -> Company
    def update(self, id: int, data: dict) -> Company
    def get_stats(self) -> dict
```

### Migration Strategy
- Create database-agnostic models
- Use Alembic for SQL migrations
- Prepare data export/import scripts
- Test with PostgreSQL locally before production migration
