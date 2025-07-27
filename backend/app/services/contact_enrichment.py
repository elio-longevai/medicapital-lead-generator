import asyncio
import json
import logging
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import httpx

from app.core.clients import llm_client, create_multi_provider_search_client
from app.graph.nodes.schemas import ContactPerson

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

        # Validate and clean contacts
        validated_contacts = self._validate_and_clean_contacts(all_contacts)

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

        # Create extraction prompt
        extraction_prompt = f"""
Je bent een expert in het extraheren van contactinformatie uit webtekst. Analyseer de volgende zoekresultaten en extraheer relevante contactpersonen voor het bedrijf "{company_name}".

ZOEKRESULTATEN:
{combined_text[:8000]}  # Limit to prevent token overflow

INSTRUCTIES:
1. Zoek naar personen met leidinggevende functies: CEO, CFO, CTO, COO, Directors, Heads of departments
2. Focus op Sales, Finance, HR, Operations, en Technology functies
3. Extraheer naam, functie, e-mail, telefoon (indien beschikbaar)
4. Bepaal department en seniority level op basis van functietitel
5. BELANGRIJK: Als je algemene contactgegevens vindt (info@, sales@, algemeen telefoonnummer) zonder specifieke persoon, maak dan een entry met name "Contactgegevens" en de gevonden contactinfo
6. ALLEEN contacten met e-mail OF telefoon worden opgeslagen

DEPARTMENTS: Sales, Finance, HR, Operations, Technology, Marketing, Legal, Other
SENIORITY LEVELS: C-Level, Director, Manager, Specialist, Other

Geef maximaal 5 relevante contactpersonen terug in JSON formaat:
[
  {{
    "name": "Volledige naam (of 'Contactgegevens' voor algemene info)",
    "role": "Functietitel in het Nederlands",
    "email": "email@company.com of null",
    "phone": "telefoonnummer of null", 
    "department": "department naam",
    "seniority_level": "seniority level"
  }}
]

Als geen relevante contacten gevonden worden, geef dan een lege lijst [] terug.
"""

        try:
            response = await asyncio.wait_for(
                llm_client.ainvoke(extraction_prompt), timeout=45.0
            )

            # Parse LLM response
            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            # Try to extract JSON from response
            # Look for JSON array in response
            json_match = re.search(r"\[.*?\]", response_text, re.DOTALL)
            if json_match:
                contacts_data = json.loads(json_match.group())
                contacts = []

                for contact_data in contacts_data:
                    if isinstance(contact_data, dict) and contact_data.get("name"):
                        contact = ContactPerson(
                            name=contact_data.get("name"),
                            role=contact_data.get("role"),
                            email=contact_data.get("email"),
                            phone=contact_data.get("phone"),
                            department=contact_data.get("department"),
                            seniority_level=contact_data.get("seniority_level"),
                        )
                        contacts.append(contact)

                logger.info(f"Extracted {len(contacts)} contacts for {company_name}")
                return contacts
            else:
                logger.warning(
                    f"No valid JSON found in LLM response for {company_name}"
                )
                return []

        except asyncio.TimeoutError:
            logger.error(f"Timeout during contact extraction for {company_name}")
            return []
        except Exception as e:
            logger.error(f"Failed to extract contacts for {company_name}: {str(e)}")
            return []

    def _validate_and_clean_contacts(
        self, contacts: List[ContactPerson]
    ) -> List[ContactPerson]:
        """Validate and clean extracted contact information."""
        validated_contacts = []

        for contact in contacts:
            # Skip contacts without name or role
            if not contact.name or not contact.role:
                continue

            # Clean and validate email
            if contact.email:
                contact.email = self._clean_email(contact.email, contact.name)
                if not self._is_valid_email(contact.email):
                    contact.email = None

            # Clean phone number
            if contact.phone:
                contact.phone = self._clean_phone(contact.phone)

            # IMPORTANT: Only save contacts that have actual contact information
            # Skip contacts that have neither email nor phone
            if not contact.email and not contact.phone:
                logger.debug(
                    f"Skipping contact {contact.name} - no email or phone information"
                )
                continue

            # Validate department and seniority
            contact.department = self._normalize_department(contact.department)
            contact.seniority_level = self._normalize_seniority(contact.seniority_level)

            validated_contacts.append(contact)

        # Remove duplicates based on name and email
        unique_contacts = []
        seen = set()

        for contact in validated_contacts:
            key = (
                contact.name.lower() if contact.name else "",
                contact.email.lower() if contact.email else "",
            )
            if key not in seen:
                seen.add(key)
                unique_contacts.append(contact)

        # Prioritize Dutch contacts
        prioritized_contacts = self._prioritize_dutch_contacts(unique_contacts)

        return prioritized_contacts

    def _clean_email(self, email: str, contact_name: str = None) -> Optional[str]:
        """Clean and normalize email address."""
        if not email:
            return None

        email = email.strip().lower()

        # Allow generic emails for "Contactgegevens" entries
        if contact_name and contact_name.lower() in ["contactgegevens", "contact info"]:
            return email

        # Skip generic emails for individual contacts
        generic_prefixes = ["info", "contact", "sales", "support", "admin", "office"]
        email_prefix = email.split("@")[0]
        if email_prefix in generic_prefixes:
            return None

        return email

    def _prioritize_dutch_contacts(
        self, contacts: List[ContactPerson]
    ) -> List[ContactPerson]:
        """Prioritize Dutch contacts by email domain and filter out non-Dutch emails where possible."""
        dutch_contacts = []
        international_contacts = []

        for contact in contacts:
            if contact.email:
                domain = contact.email.split("@")[-1].lower()
                # Prioritize Dutch domains
                if domain.endswith(".nl") or domain.endswith(".be"):
                    dutch_contacts.append(contact)
                else:
                    international_contacts.append(contact)
            else:
                # Contacts without email - add to Dutch pile
                dutch_contacts.append(contact)

        # Return Dutch contacts first, then international
        return dutch_contacts + international_contacts

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _clean_phone(self, phone: str) -> Optional[str]:
        """Clean and normalize phone number."""
        if not phone:
            return None

        # Remove common phone number formatting
        cleaned = re.sub(r"[^\d+\-\(\)\s]", "", phone)
        cleaned = cleaned.strip()

        # Skip if too short or too long
        digits_only = re.sub(r"[^\d]", "", cleaned)
        if len(digits_only) < 8 or len(digits_only) > 15:
            return None

        return cleaned

    def _normalize_department(self, department: str) -> Optional[str]:
        """Normalize department names."""
        if not department:
            return None

        department_mapping = {
            "sales": "Sales",
            "finance": "Finance",
            "hr": "HR",
            "human resources": "HR",
            "operations": "Operations",
            "technology": "Technology",
            "it": "Technology",
            "marketing": "Marketing",
            "legal": "Legal",
        }

        dept_lower = department.lower()
        for key, value in department_mapping.items():
            if key in dept_lower:
                return value

        return "Other"

    def _normalize_seniority(self, seniority: str) -> Optional[str]:
        """Normalize seniority levels."""
        if not seniority:
            return None

        seniority_lower = seniority.lower()

        if any(
            term in seniority_lower for term in ["ceo", "cfo", "cto", "coo", "chief"]
        ):
            return "C-Level"
        elif any(
            term in seniority_lower
            for term in ["director", "head of", "vp", "vice president"]
        ):
            return "Director"
        elif "manager" in seniority_lower:
            return "Manager"
        elif any(
            term in seniority_lower for term in ["specialist", "analyst", "coordinator"]
        ):
            return "Specialist"
        else:
            return "Other"

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
