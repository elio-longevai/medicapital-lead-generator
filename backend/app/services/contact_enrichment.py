import asyncio
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

        # Execute searches
        search_results = []
        for query in search_queries:
            try:
                result = await self._execute_search(company_name, query)
                search_results.append(result)
                # Add delay between searches to respect rate limits
                await asyncio.sleep(2)  # Increased delay for API rate limiting
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {str(e)}")
                continue

        # Extract contacts from search results
        extracted_contacts = await self._extract_contacts_from_results(
            company_name, search_results, existing_contacts
        )

        # Validate and clean contacts
        validated_contacts = self._validate_and_clean_contacts(extracted_contacts)

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
        """Generate targeted search queries for finding contact information."""
        queries = []

        # Basic leadership search
        queries.append(f'"{company_name}" CEO email contact')
        queries.append(f'"{company_name}" CFO "Chief Financial Officer" contact')
        queries.append(f'"{company_name}" CTO "Chief Technology Officer" email')
        queries.append(f'"{company_name}" leadership team contact information')

        # Management and department heads
        queries.append(f'"{company_name}" "Head of Sales" "Sales Director" email')
        queries.append(f'"{company_name}" "Head of HR" "Human Resources" contact')
        queries.append(f'"{company_name}" management team email phone')

        # Website-specific searches
        if website_url:
            domain = (
                website_url.replace("https://", "").replace("http://", "").split("/")[0]
            )
            queries.append(f"site:{domain} contact management team")
            queries.append(f'site:{domain} "about us" team leadership')

        # LinkedIn-specific searches
        queries.append(f'site:linkedin.com "{company_name}" CEO')
        queries.append(f'site:linkedin.com "{company_name}" CFO')
        queries.append(f'site:linkedin.com "{company_name}" Director')

        return queries[:8]  # Limit to prevent excessive API usage

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
5. Vermijd algemene contactadressen zoals info@, sales@, etc.

DEPARTMENTS: Sales, Finance, HR, Operations, Technology, Marketing, Legal, Other
SENIORITY LEVELS: C-Level, Director, Manager, Specialist, Other

Geef maximaal 5 relevante contactpersonen terug in JSON formaat:
[
  {{
    "name": "Volledige naam",
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
            import json

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
                contact.email = self._clean_email(contact.email)
                if not self._is_valid_email(contact.email):
                    contact.email = None

            # Clean phone number
            if contact.phone:
                contact.phone = self._clean_phone(contact.phone)

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

        return unique_contacts

    def _clean_email(self, email: str) -> Optional[str]:
        """Clean and normalize email address."""
        if not email:
            return None

        email = email.strip().lower()

        # Skip generic emails
        generic_prefixes = ["info", "contact", "sales", "support", "admin", "office"]
        email_prefix = email.split("@")[0]
        if email_prefix in generic_prefixes:
            return None

        return email

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
