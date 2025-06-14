Excellent. The plan is approved, and the mission is clear: to build an exceptional, high-quality backend that delivers a steady stream of relevant leads for MediCapital Solutions. I will now translate our robust plan into clean, modular, and maintainable Python code.

Here is the complete backend implementation, structured for clarity and scalability.

### **1. Project Setup**

First, create the project directory and environment.

```sh
# Create the main project directory
mkdir medicapital_lead_engine
cd medicapital_lead_engine

# Initialize the uv environment
uv venv

# Activate the environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Create the necessary files and directories
mkdir -p app/core app/db app/graph app/services tests
touch app/__init__.py app/main.py app/core/__init__.py app/core/settings.py app/core/clients.py \
      app/db/__init__.py app/db/models.py app/db/session.py \
      app/graph/__init__.py app/graph/state.py app/graph/prompts.py app/graph/nodes.py app/graph/workflow.py \
      app/services/__init__.py app/services/company_name_normalizer.py \
      tests/__init__.py pyproject.toml .env.example README.md
```

### **2. Dependency Management (`pyproject.toml`)**

This file defines our project and all its dependencies for `uv`.

```toml
# pyproject.toml

[project]
name = "medicapital_lead_engine"
version = "0.1.0"
description = "AI-Powered Lead Generation Engine for MediCapital Solutions"
authors = [{ name = "Your Name", email = "your@email.com" }]
requires-python = ">=3.12"
dependencies = [
    "uv",
    "langchain>=0.2.5",
    "langgraph>=0.1.1",
    "langchain-google-genai>=1.0.6",
    "pydantic>=2.7.4",
    "sqlalchemy>=2.0.30",
    "alembic>=1.13.1",
    "psycopg2-binary>=2.9.9", # For PostgreSQL in production
    "python-dotenv>=1.0.1",
    "typer[all]>=0.12.3",
    "apscheduler>=3.10.4",
    "httpx>=0.27.0", # For making API calls
    "langsmith", # For observability
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.2",
    "pytest-cov>=5.0.0",
]

[tool.uv.sources]
# This section is optional but good practice
pypi = { url = "https://pypi.org/simple" }
```

Install the dependencies:

```sh
uv pip install -e .[dev]
```

### **3. Environment Variables (`.env.example`)**

Create a template for the required secrets. Users will copy this to a `.env` file.

```dotenv
# .env.example

# LangSmith settings for observability and debugging
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="YOUR_LANGSMITH_API_KEY"
LANGCHAIN_PROJECT="MediCapital Lead Engine"

# API Keys
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
BRAVE_API_KEY="YOUR_BRAVE_SEARCH_API_KEY"

# Database Configuration
# For local development with SQLite:
DATABASE_URL="sqlite:///./medicapital.db"
# For production with PostgreSQL:
# DATABASE_URL="postgresql://user:password@host:port/dbname"

# Application Settings
LOG_LEVEL="INFO"
```

### **4. Core Application Files**

#### **`app/core/settings.py`**
Manages all configuration using Pydantic for validation.

```python
# app/core/settings.py

import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Manages application settings and secrets."""
    
    # Load from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LangSmith
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "MediCapital Lead Engine"

    # API Keys
    GOOGLE_API_KEY: str
    BRAVE_API_KEY: str

    # Database
    DATABASE_URL: str = "sqlite:///./medicapital.db"
    
    # Application
    LOG_LEVEL: str = "INFO"

# Instantiate settings to be imported by other modules
settings = Settings()

# Set environment variables for LangSmith, as it's read directly by the library
os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
```

#### **`app/db/models.py`**
Defines the SQLAlchemy data models.

```python
# app/db/models.py

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
# Use JSONB for PostgreSQL for better performance and functionality
# from sqlalchemy.dialects.postgresql import JSONB 

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
    enriched_data = Column(Text, nullable=True) # For SQLite, use Text. For PG, use JSONB.
    
    # For Sprint 3+
    qualification_score = Column(Integer, nullable=True)
    qualification_reasoning = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (UniqueConstraint('normalized_name', name='uq_normalized_name'),)

    def __repr__(self):
        return f"<Company(name='{self.discovered_name}', status='{self.status}')>"
```

#### **`app/db/session.py`**
Manages database connections.

```python
# app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Provides a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### **`app/services/company_name_normalizer.py`**
A focused utility for cleaning company names to prevent duplicates.

```python
# app/services/company_name_normalizer.py

import re

def normalize_name(name: str) -> str:
    """
    Cleans and standardizes a company name for consistent matching.
    
    - Converts to lowercase.
    - Removes common legal entity suffixes for NL/BE.
    - Removes punctuation and extra whitespace.
    """
    if not isinstance(name, str):
        return ""
        
    # Lowercase the name
    normalized = name.lower()
    
    # Remove common legal suffixes
    suffixes = [
        r'\b(b\.v\.|bv|besloten vennootschap)\b',
        r'\b(n\.v\.|nv|naamloze vennootschap)\b',
        r'\b(vof|vennootschap onder firma)\b',
        r'\b(gcv|gewone commanditaire vennootschap)\b',
        r'\b(commv|commanditaire vennootschap)\b',
        r'\b(coop|coöperatie)\b',
        r'\b(inc|ltd|llc|gmbh|sarl|sa)\b',
    ]
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
        
    # Remove punctuation except hyphens
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    
    # Collapse multiple spaces/hyphens and strip whitespace
    normalized = re.sub(r'[\s-]+', ' ', normalized).strip()
    
    return normalized
```

### **5. The LangGraph Engine**

This is the core AI logic, split into clear, maintainable files.

#### **`app/graph/state.py`**
Defines the data structure that flows through our graph.

```python
# app/graph/state.py

from pydantic import BaseModel, Field

class CandidateLead(BaseModel):
    """A pre-vetted lead, extracted from search results."""
    discovered_name: str = Field(description="The name of the company as found.")
    source_url: str = Field(description="The URL of the page where the company was mentioned.")
    country: str = Field(description="The two-letter country code (e.g., 'NL', 'BE').")
    primary_industry: str = Field(description="The main industry of the company (e.g., 'Healthcare', 'Sustainability').")
    initial_reasoning: str = Field(description="A brief justification for why this company is a potential lead.")

class GraphState(BaseModel):
    """The state object that moves through the lead generation graph."""
    raw_icp_text: str
    target_country: str # 'NL' or 'BE'
    
    structured_icp: dict = Field(default_factory=dict)
    search_queries: list[str] = Field(default_factory=list)
    search_results: list[dict] = Field(default_factory=list)
    candidate_leads: list[CandidateLead] = Field(default_factory=list)
    
    # Final output
    newly_saved_leads_count: int = 0
    error_message: str | None = None
```

#### **`app/graph/prompts.py`**
A centralized location for our high-quality, fine-tuned prompts.

```python
# app/graph/prompts.py

ICP_STRUCTURING_PROMPT = """
You are an expert data analyst. Your task is to parse the following unstructured text, which describes an Ideal Customer Profile (ICP), and convert it into a structured JSON object. The ICP focuses on both suppliers/manufacturers and end-users of equipment.

Focus on extracting these key fields:
- sectors: A list of primary industries (e.g., "Healthcare", "Sustainability", "Hospitality").
- target_entities: A list of company types (e.g., "Suppliers", "Installers", "Private Clinics", "Restaurants").
- geo_focus: The primary countries of operation (e.g., "NL", "BE").
- key_products: A list of relevant equipment or product types (e.g., "Ultrasound devices", "Solar panels", "Kitchen robotics").
- financial_criteria: A summary of financial health indicators mentioned.
- scale_indicators: Information on company size (e.g., "< 10 employees").
- investment_range: The typical value range of the equipment being financed.

Unstructured ICP Text:
---
{raw_icp_text}
---

Produce a clean JSON object. Do not include any explanatory text outside of the JSON.
"""

QUERY_GENERATION_PROMPT = """
You are a strategic marketing expert for MediCapital, a company specializing in equipment leasing for B2B clients in the Netherlands and Belgium. Based on the structured Ideal Customer Profile (ICP) provided below, generate a diverse list of 15-20 highly specific and creative search queries to find potential leads.

The goal is to find both **suppliers/manufacturers** of equipment and **end-user businesses** that would need to acquire such equipment. The queries should be in Dutch.

**Structured ICP:**
```json
{structured_icp}
```

**Query Generation Strategies:**
1.  **Supplier/Distributor Search:** Find wholesalers, manufacturers, and distributors of the key products.
    *   Example: "groothandel medische laserapparatuur Nederland"
2.  **Installer/Service Provider Search:** Find companies that install or service the equipment.
    *   Example: "erkende installateurs zonnepanelen B2B België"
3.  **New Business/Expansion Search:** Find news of new companies or locations opening, which implies a need for new equipment. Use recent years in the query.
    *   Example: "nieuwe privékliniek geopend 2024 Amsterdam"
    *   Example: "restaurant verbouwing aankondiging Utrecht"
4.  **Industry-Specific Need Search:** Target niche communities or business types.
    *   Example: "vereniging van huidtherapeuten ledenlijst"
    *   Example: "leveranciers voor professionele keukens horeca"
5.  **Problem-Oriented Search:** Search for problems that MediCapital's leasing solutions can solve.
    *   Example: "financiering medische apparatuur voor startende praktijk"
    *   Example: "duurzame investeringen voor MKB-bedrijven"

Generate a JSON list of strings. Do not add any commentary.
["query1", "query2", ...]
"""

LEAD_TRIAGE_PROMPT = """
You are a lead qualification analyst for MediCapital Solutions. Your task is to meticulously evaluate a single web search result and determine if it points to a specific, legitimate B2B company in the Netherlands or Belgium that matches our Ideal Customer Profile (ICP).

**Ideal Customer Profile (ICP) Summary:**
- **Sectors:** Healthcare (Medical, Labs, Wellness, Beauty), Sustainability (Energy, Infrastructure), Hospitality (Restaurants).
- **Company Types:** Suppliers, Manufacturers, Installers, Private Clinics, Small/Medium Businesses (<100 staff). We are NOT looking for news sites, blogs, directories, or government agencies.
- **Geography:** Must be clearly located in or operating in the Netherlands (NL) or Belgium (BE).

**Your Task:**
Based *only* on the provided `title` and `description` of the search result, decide if it represents a potential lead.

**Search Result:**
- **Title:** {title}
- **Description:** {description}

**Analysis and Output:**
1.  **Analyze:** Does the text suggest a specific B2B company? Does it fit the sectors and geography?
2.  **Justify:** If it's a potential lead, write a brief, one-sentence justification explaining *why* it's a good fit based on the text.
3.  **Format:** Respond with a single, clean JSON object that matches the following Pydantic model.

```pydantic
class CandidateLead(BaseModel):
    discovered_name: str
    source_url: str
    country: str
    primary_industry: str
    initial_reasoning: str
```

- If the result is a **GOOD LEAD**, populate the JSON object. Use the provided `{source_url}` and `{country}`.
- If the result is **NOT A LEAD** (e.g., a news article, a forum, a directory site like 'Europages', a government site), you **MUST** respond with the word `null` and nothing else.
"""
```

#### **`app/core/clients.py`**
Clean wrappers for external API clients.

```python
# app/core/clients.py

import httpx
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings

def get_llm_client() -> ChatGoogleGenerativeAI:
    """Returns a configured instance of the Gemini client."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-0520",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0,
        convert_system_message_to_human=True # Helps with some models
    )

class BraveSearchClient:
    """A client for the Brave Search API."""
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def search(self, query: str, country: str) -> list[dict]:
        """Performs a web search and returns the results."""
        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json"
        }
        params = {"q": query, "country": country.lower(), "count": 20}
        
        try:
            with httpx.Client() as client:
                response = client.get(self.BASE_URL, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("web", {}).get("results", [])
        except httpx.HTTPStatusError as e:
            print(f"Brave Search API error: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during Brave Search: {e}")
            return []

# Instantiate clients for use in the graph
brave_client = BraveSearchClient(api_key=settings.BRAVE_API_KEY)
llm_client = get_llm_client()
```

#### **`app/graph/nodes.py`**
Contains the core logic for each step in the graph.

```python
# app/graph/nodes.py

import json
from typing import TypedDict
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.clients import llm_client, brave_client
from app.db.models import Company
from app.db.session import SessionLocal
from app.graph.state import GraphState, CandidateLead
from app.graph import prompts
from app.services.company_name_normalizer import normalize_name

class NodeResult(TypedDict):
    """Defines the structure for node return values to update the state."""
    pass

def structure_icp(state: GraphState) -> NodeResult:
    """Parses the raw ICP text into a structured dictionary."""
    print("---NODE: Structuring ICP---")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.ICP_STRUCTURING_PROMPT,
        input_variables=["raw_icp_text"],
        partial_variables={"parser_instructions": parser.get_format_instructions()}
    )
    chain = prompt | llm_client | parser
    structured_icp = chain.invoke({"raw_icp_text": state["raw_icp_text"]})
    return {"structured_icp": structured_icp}

def generate_search_queries(state: GraphState) -> NodeResult:
    """Generates strategic search queries based on the structured ICP."""
    print("---NODE: Generating Search Queries---")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.QUERY_GENERATION_PROMPT,
        input_variables=["structured_icp"],
        partial_variables={"parser_instructions": parser.get_format_instructions()}
    )
    chain = prompt | llm_client | parser
    queries = chain.invoke({"structured_icp": state["structured_icp"]})
    return {"search_queries": queries}

def execute_web_search(state: GraphState) -> NodeResult:
    """Executes web searches for the generated queries."""
    print(f"---NODE: Executing Web Search for {len(state['search_queries'])} queries---")
    all_results = []
    for query in state["search_queries"]:
        print(f"  > Searching for: '{query}'")
        results = brave_client.search(query=query, country=state["target_country"])
        all_results.extend(results)
    print(f"  > Found {len(all_results)} total results.")
    return {"search_results": all_results}

def triage_and_extract_leads(state: GraphState) -> NodeResult:
    """Uses an LLM to triage search results and extract candidate leads."""
    print(f"---NODE: Triaging {len(state['search_results'])} Search Results---")
    parser = PydanticOutputParser(pydantic_object=CandidateLead)
    prompt = PromptTemplate(
        template=prompts.LEAD_TRIAGE_PROMPT,
        input_variables=["title", "description", "source_url", "country"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm_client | parser

    candidate_leads = []
    for i, result in enumerate(state["search_results"]):
        # The triage prompt is very sensitive to low-quality/irrelevant input
        if not result.get("title") or not result.get("description"):
            continue

        try:
            candidate = chain.invoke({
                "title": result["title"],
                "description": result.get("description", ""),
                "source_url": result["url"],
                "country": state["target_country"],
            })
            print(f"  > [Result {i+1}] PASS: Found potential lead '{candidate.discovered_name}'")
            candidate_leads.append(candidate)
        except Exception:
            # Pydantic parser will raise an exception if the output is not valid JSON
            # or if the LLM outputs `null`, which we treat as a rejection.
            print(f"  > [Result {i+1}] REJECTED: Not a B2B lead.")
            continue
            
    return {"candidate_leads": candidate_leads}

def save_leads_to_db(state: GraphState) -> NodeResult:
    """Saves unique, new leads to the database."""
    print(f"---NODE: Saving {len(state['candidate_leads'])} Candidate Leads to DB---")
    db = SessionLocal()
    saved_count = 0
    
    try:
        existing_names = {row[0] for row in db.query(Company.normalized_name).all()}
        
        for lead in state["candidate_leads"]:
            norm_name = normalize_name(lead.discovered_name)
            if not norm_name or norm_name in existing_names:
                print(f"  > SKIPPING (Duplicate or empty): '{lead.discovered_name}'")
                continue

            new_company = Company(
                normalized_name=norm_name,
                discovered_name=lead.discovered_name,
                source_url=lead.source_url,
                country=lead.country,
                primary_industry=lead.primary_industry,
                initial_reasoning=lead.initial_reasoning,
                status="discovered",
            )
            db.add(new_company)
            existing_names.add(norm_name) # Add to set to handle intra-batch duplicates
            saved_count += 1
            print(f"  > ADDING New Lead: '{lead.discovered_name}'")

        db.commit()
        print(f"---SUCCESS: Saved {saved_count} new leads to the database.---")
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        db.rollback()
        return {"error_message": str(e)}
    finally:
        db.close()
        
    return {"newly_saved_leads_count": saved_count}
```

#### **`app/graph/workflow.py`**
Assembles the nodes into a coherent, runnable graph.

```python
# app/graph/workflow.py

from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph import nodes

def build_workflow():
    """Builds and compiles the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("structure_icp", nodes.structure_icp)
    workflow.add_node("generate_search_queries", nodes.generate_search_queries)
    workflow.add_node("execute_web_search", nodes.execute_web_search)
    workflow.add_node("triage_and_extract_leads", nodes.triage_and_extract_leads)
    workflow.add_node("save_leads_to_db", nodes.save_leads_to_db)

    # Define edges
    workflow.set_entry_point("structure_icp")
    workflow.add_edge("structure_icp", "generate_search_queries")
    workflow.add_edge("generate_search_queries", "execute_web_search")
    workflow.add_edge("execute_web_search", "triage_and_extract_leads")
    workflow.add_edge("triage_and_extract_leads", "save_leads_to_db")
    workflow.add_edge("save_leads_to_db", END)
    
    # Compile the graph
    app = workflow.compile()
    return app

# A single, compiled instance to be used by the application
main_workflow = build_workflow()
```

### **6. Main Application Entrypoint & Scheduler**

#### **`app/main.py`**
The main CLI for running the engine manually or on a schedule.

```python
# app/main.py

import typer
from apscheduler.schedulers.blocking import BlockingScheduler
from app.db.models import Base
from app.db.session import engine
from app.graph.workflow import main_workflow
from app.graph.state import GraphState

# This is the raw text from the provided documents
# In a real app, this might be loaded from a file or a database
MEDICAPITAL_ICP_TEXT = """
Sectoren leveranciers / gebruikers van Duurzaam => energie voorzieningen / infrastructuur en Healthcare => Medisch (diagnose & behandeling) => Verpleeg => Laboratorium / onderzoek => Sport => Wellness / beauty.
Producten duurzaam: Batterijen, zonnepanelen, laadpalen, LED, infraroodpanelen, ge-electrificeerd bouwmaterieel, boilers, warmtepomp, airco, etc.
Producten healthcare: Medische en laboratorium apparatuur / inrichten zoals Ultrasound, holters, ecg, lasers maar ook behandeltafels, stoelen etc.
Ideale contact bij leveranciers (Duurzaam en healthcare) is de sales verantwoordelijke / eigenaar.
Ideale contact bij klanten / gebruikers van units is dat (project-)verantwoordelijke voor operations/ finance manager bij grotere bedrijven of eigenaar van kleinere bedrijven (< 10 man personeel).
Vereisten klant: B2B, geregistreerd in NL / BE. Financieel: minimale bestaansduur 1,5 jaar, omzet in relatie tot investering (3 x), winstgevend, positief vermogen en werkkapitaal.
Investering minimaal bedrag per unit 2.500,- euro, optimaal bedrag 35.000 tot 125.000.
"""

cli = typer.Typer()

def run_lead_generation_for_country(country_code: str):
    """Executes the full lead generation workflow for a given country."""
    print(f"\n{'='*50}")
    print(f"🚀 STARTING LEAD GENERATION RUN FOR: {country_code.upper()} 🚀")
    print(f"{'='*50}\n")
    
    initial_state = GraphState(
        raw_icp_text=MEDICAPITAL_ICP_TEXT,
        target_country=country_code
    )
    
    # The .stream() method is useful for observing the state at each step
    final_state = None
    for event in main_workflow.stream(initial_state):
        state_key = list(event.keys())[0]
        final_state = event[state_key]
        print(f"\n--- Just finished {state_key} ---")

    print(f"\n{'='*50}")
    print(f"🏁 LEAD GENERATION RUN FOR {country_code.upper()} COMPLETE 🏁")
    saved = final_state.get('newly_saved_leads_count', 0)
    print(f"✅ New Leads Saved: {saved}")
    print(f"{'='*50}\n")

@cli.command()
def run_once(
    country: str = typer.Option("NL", help="Country to target ('NL' or 'BE').")
):
    """Run the lead generation process one time for the specified country."""
    if country.upper() not in ["NL", "BE"]:
        print("Error: Country must be 'NL' or 'BE'.")
        raise typer.Exit()
    run_lead_generation_for_country(country.upper())

@cli.command()
def start_scheduler(
    interval_hours: int = typer.Option(4, help="Number of hours between runs.")
):
    """
    Start the scheduler to run the lead generation process periodically.
    It will alternate between NL and BE on each run.
    """
    scheduler = BlockingScheduler()
    
    # Schedule the job to run immediately and then at intervals
    scheduler.add_job(
        run_lead_generation_for_country, 
        'interval', 
        hours=interval_hours, 
        args=["NL"], 
        id="nl_run"
    )
    scheduler.add_job(
        run_lead_generation_for_country, 
        'interval', 
        hours=interval_hours, 
        args=["BE"], 
        id="be_run",
        # Start the BE run halfway through the interval
        next_run_time=datetime.datetime.now() + datetime.timedelta(hours=interval_hours/2)
    )

    print(f"📅 Scheduler started. Running every {interval_hours} hours for NL and BE (offset).")
    print("Press Ctrl+C to exit.")
    
    try:
        run_lead_generation_for_country("NL") # Run once immediately on start
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")

@cli.command()
def create_db():
    """Creates the database tables based on the models."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    cli()
```

### **7. Database Migrations & Testing**

#### **Setup Alembic**
This is a one-time setup to manage database schema changes.

```sh
# Make sure you are in the project root with the venv activated
# Initialize Alembic. This creates an `alembic` directory and `alembic.ini`.
# NOTE: This command is interactive. I will assume standard answers.
# The alembic.ini needs to be edited to point to the DB URL.
# I will simulate this step. For a real project, you'd run:
# alembic init alembic

# For this automated setup, I will provide the generated files.
# In a real scenario, you'd edit alembic.ini to set `sqlalchemy.url`:
# sqlalchemy.url = sqlite:///./medicapital.db (or from env var)
# And in `env.py`, you'd set `target_metadata = Base.metadata` from your models.
```
Due to the complexity of auto-generating Alembic files here, the user should run `alembic init alembic` and configure `alembic.ini` and `alembic/env.py` to point to the database and models.

**Generate Initial Migration:**
```sh
alembic revision --autogenerate -m "Initial schema for companies"
```
**Apply Migration:**
```sh
alembic upgrade head
```

#### **Placeholder Test (`tests/test_normalizer.py`)**

A simple test to ensure the test suite is working and to validate our normalizer logic.

```python
# tests/test_normalizer.py

import pytest
from app.services.company_name_normalizer import normalize_name

@pytest.mark.parametrize("input_name, expected_name", [
    ("LongevAI B.V.", "longevai"),
    ("MediCapital Solutions N.V.", "medicapital solutions"),
    ("CleanEnergy Installateurs", "cleanenergy installateurs"),
    ("Dr. Jansen's Kliniek (CommV)", "dr jansens kliniek"),
    ("  Extra   Whitespace  Co. ", "extra whitespace co"),
    ("Punctuation!@#$Be-Gone", "punctuationbe-gone"),
])
def test_normalize_name(input_name, expected_name):
    """Tests that company names are normalized correctly."""
    assert normalize_name(input_name) == expected_name

def test_normalize_name_with_none():
    """Tests that the normalizer handles None input gracefully."""
    assert normalize_name(None) == ""
```
Run tests with `pytest`.

### **How to Run**

1.  **Fill in `.env`:** Copy `.env.example` to `.env` and add your API keys.
2.  **Create Database:** Run `python -m app.main create-db`. (Or use Alembic).
3.  **Run Manually:** `python -m app.main run-once --country NL`
4.  **Start Scheduler:** `python -m app.main start-scheduler --interval-hours 4`

This complete implementation delivers on the promise of an exceptional, modular, and powerful backend, ready to fuel MediCapital's growth.