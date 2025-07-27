import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import httpx

from app.core.clients import create_multi_provider_search_client
from app.graph.nodes.schemas import ContactPerson
from app.utils.contact_validator import ContactValidator
from app.utils.llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class ContactSearchResult:
    """Represents search results for contact information."""

    company_name: str
    search_query: str
    results: List[Dict[str, Any]]
    success: bool
    error_message: Optional[str] = None


class ContactEnrichmentService:
    """Service for enriching company contact information through web search."""

    def __init__(self):
        self.search_timeout = 30
        self.max_results_per_query = 10
        self.search_client = create_multi_provider_search_client()

    async def enrich_company_contacts(
        self,
        company_name: str,
        website_url: Optional[str] = None,
        existing_contacts: Optional[List[ContactPerson]] = None,
    ) -> Dict[str, Any]:
        """
        Enrich contact information for a company using web search.

        Args:
            company_name: Name of the company
            website_url: Company website URL
            existing_contacts: Existing contact information

        Returns:
            Dict containing enriched contact data and status
        """
        logger.info(f"Starting contact enrichment for {company_name}")

        # Generate search queries
        search_queries = self._generate_search_queries(company_name, website_url)

        # Try People Data Labs first (direct contact lookup - fastest method)
        pdl_contacts = await self._try_people_data_labs(company_name, website_url)

        # If we have sufficient contacts from PDL, use them directly
        if len(pdl_contacts) >= 2:
            logger.info(
                f"Found {len(pdl_contacts)} contacts via People Data Labs for {company_name}"
            )
            validated_contacts = self._validate_and_clean_contacts(pdl_contacts)

            return {
                "contacts": validated_contacts,
                "search_queries_executed": 0,  # No search queries needed
                "contacts_found": len(validated_contacts),
                "enrichment_status": "completed",
                "search_results_summary": {
                    "pdl_contacts": len(pdl_contacts),
                    "search_used": False,
                },
            }

        # Execute search queries in parallel (much faster than sequential)
        logger.info(
            f"Running {len(search_queries)} search queries in parallel for {company_name}"
        )
        search_tasks = [
            self._execute_search(company_name, query) for query in search_queries
        ]

        try:
            # Execute all searches concurrently
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Filter out exceptions and convert to proper results
            valid_results = []
            for result in search_results:
                if isinstance(result, Exception):
                    logger.warning(f"Search task failed: {str(result)}")
                elif isinstance(result, ContactSearchResult):
                    valid_results.append(result)

            search_results = valid_results

        except Exception as e:
            logger.error(
                f"Parallel search execution failed for {company_name}: {str(e)}"
            )
            search_results = []

        # Extract contacts from search results (combining with PDL results if any)
        search_contacts = await self._extract_contacts_from_results(
            company_name, search_results, existing_contacts
        )

        # Combine PDL contacts with search-based contacts
        all_contacts = pdl_contacts + search_contacts

        # Validate and clean contacts using shared utility
        validated_contacts = ContactValidator.validate_and_clean_contacts(all_contacts)

        # Enhance with Hunter.io email verification (if API key available)
        if validated_contacts and website_url:
            validated_contacts = await self._enhance_with_hunter_io(
                validated_contacts, website_url
            )

        return {
            "contacts": validated_contacts,
            "search_queries_executed": len(search_results),
            "contacts_found": len(validated_contacts),
            "enrichment_status": "completed" if validated_contacts else "partial",
            "search_results_summary": self._summarize_search_results(search_results),
        }

    def _generate_search_queries(
        self, company_name: str, website_url: Optional[str]
    ) -> List[str]:
        """Generate optimized search queries for finding contact information (reduced from 8 to 4)."""
        queries = []

        # Combined leadership search (combines CEO, CFO, CTO in one query) - prioritize Dutch contacts
        queries.append(
            f'"{company_name}" CEO CFO CTO director email contact Nederland Netherlands Dutch .nl'
        )

        # Management team search - prioritize Dutch contacts
        queries.append(
            f'"{company_name}" management team leadership contact email phone Nederland Netherlands'
        )

        # Website-specific search (if available)
        if website_url:
            domain = (
                website_url.replace("https://", "").replace("http://", "").split("/")[0]
            )
            queries.append(
                f"site:{domain} contact team leadership management {company_name}"
            )

        # LinkedIn professional search - prioritize Netherlands location
        queries.append(
            f'site:linkedin.com "{company_name}" CEO director manager Netherlands Nederland location:nl'
        )

        return queries[:4]  # Reduced from 8 to 4 queries for faster execution

    async def _try_people_data_labs(
        self, company_name: str, website_url: Optional[str] = None
    ) -> List[ContactPerson]:
        """Try to get contacts directly from People Data Labs (fastest method)."""
        try:
            from app.services.people_data_labs import people_data_labs_client

            contacts = await people_data_labs_client.find_company_contacts(
                company_name, website_url
            )
            return contacts

        except Exception as e:
            logger.debug(f"People Data Labs lookup failed for {company_name}: {str(e)}")
            return []

    async def _execute_search(
        self, company_name: str, query: str
    ) -> ContactSearchResult:
        """Execute a web search query using the multi-provider search client."""
        try:
            async with httpx.AsyncClient(timeout=self.search_timeout) as client:
                results, provider_used = await self.search_client.search_async(
                    query=query,
                    country="NL",  # Default to Netherlands, could be made configurable
                    client=client,
                )

                if results:
                    # Convert results to format expected by contact extraction
                    formatted_results = []
                    for result in results[: self.max_results_per_query]:
                        formatted_results.append(
                            {
                                "Text": result.get("description", ""),
                                "FirstURL": result.get("url", ""),
                                "title": result.get("title", ""),
                            }
                        )

                    logger.info(
                        f"Found {len(formatted_results)} results using {provider_used} for: {query}"
                    )

                    return ContactSearchResult(
                        company_name=company_name,
                        search_query=query,
                        results=formatted_results,
                        success=True,
                    )
                else:
                    logger.warning(f"No results found for query: {query}")
                    return ContactSearchResult(
                        company_name=company_name,
                        search_query=query,
                        results=[],
                        success=False,
                        error_message="No results found",
                    )

        except Exception as e:
            logger.error(f"Search execution failed for query '{query}': {str(e)}")
            return ContactSearchResult(
                company_name=company_name,
                search_query=query,
                results=[],
                success=False,
                error_message=str(e),
            )

    async def _extract_contacts_from_results(
        self,
        company_name: str,
        search_results: List[ContactSearchResult],
        existing_contacts: Optional[List[ContactPerson]] = None,
    ) -> List[ContactPerson]:
        """Extract contact information from search results using LLM."""

        # Combine all search result text
        combined_text = ""
        for result in search_results:
            if result.success:
                for item in result.results:
                    text_content = item.get("Text", "") + " " + item.get("FirstURL", "")
                    combined_text += text_content + "\n"

        if not combined_text.strip():
            logger.warning(f"No search content found for {company_name}")
            return []

        # Use shared LLM service for contact extraction
        try:
            contacts_data = await LLMService.extract_contacts_from_text(
                company_name, combined_text, max_contacts=5
            )

            contacts = []
            for contact_data in contacts_data:
                contact = ContactPerson(
                    name=contact_data.get("name"),
                    role=contact_data.get("role"),
                    email=contact_data.get("email"),
                    phone=contact_data.get("phone"),
                    department=contact_data.get("department"),
                    seniority_level=contact_data.get("seniority_level"),
                )
                contacts.append(contact)

            return contacts

        except Exception as e:
            logger.error(f"Failed to extract contacts for {company_name}: {str(e)}")
            return []

    def _summarize_search_results(
        self, search_results: List[ContactSearchResult]
    ) -> Dict[str, Any]:
        """Create a summary of search results for logging."""
        successful_searches = sum(1 for r in search_results if r.success)
        total_results = sum(len(r.results) for r in search_results if r.success)

        return {
            "total_queries": len(search_results),
            "successful_queries": successful_searches,
            "total_search_results": total_results,
            "failed_queries": len(search_results) - successful_searches,
        }

    async def _enhance_with_hunter_io(
        self, contacts: List[ContactPerson], website_url: str
    ) -> List[ContactPerson]:
        """Enhance contacts with Hunter.io email verification and domain search."""
        try:
            from app.services.hunter_io import hunter_io_client

            # Extract domain from website URL
            domain = (
                website_url.replace("https://", "").replace("http://", "").split("/")[0]
            )
            if domain.startswith("www."):
                domain = domain[4:]

            # Use Hunter.io to enhance contacts
            enhanced_contacts = await hunter_io_client.enhance_contacts_with_emails(
                contacts, domain
            )

            logger.info(
                f"Enhanced {len(contacts)} contacts to {len(enhanced_contacts)} contacts using Hunter.io"
            )
            return enhanced_contacts

        except Exception as e:
            logger.debug(f"Hunter.io enhancement failed: {str(e)}")
            return contacts  # Return original contacts if enhancement fails
