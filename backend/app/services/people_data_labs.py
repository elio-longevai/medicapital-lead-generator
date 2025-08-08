"""
People Data Labs client for direct contact enrichment.

This service provides direct contact lookups using the People Data Labs API,
allowing us to find executive contacts without search queries.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.settings import settings
from app.graph.nodes.schemas import ContactPerson

logger = logging.getLogger(__name__)


class PeopleDataLabsClient:
    """Client for People Data Labs API - direct contact enrichment."""

    def __init__(self):
        self.api_key = getattr(settings, "PEOPLE_DATA_LABS_API_KEY", None)
        self.base_url = "https://api.peopledatalabs.com/v5"
        self.timeout = 15.0

    async def find_company_contacts(
        self, company_name: str, website_url: Optional[str] = None
    ) -> List[ContactPerson]:
        """
        Find contacts for a company using People Data Labs Person Search API.

        Args:
            company_name: Name of the company
            website_url: Company website (optional, helps with accuracy)

        Returns:
            List of ContactPerson objects
        """
        if not self.api_key:
            logger.warning("People Data Labs API key not configured")
            return []

        try:
            # Search for people at the company
            contacts = await self._search_people(company_name, website_url)

            # Convert to ContactPerson objects
            contact_objects = []
            for contact_data in contacts[:5]:  # Limit to top 5 contacts
                contact = self._parse_contact(contact_data)
                if contact:
                    contact_objects.append(contact)

            logger.info(
                f"Found {len(contact_objects)} contacts for {company_name} via People Data Labs"
            )
            return contact_objects

        except Exception as e:
            logger.error(f"People Data Labs search failed for {company_name}: {str(e)}")
            return []

    async def _search_people(
        self, company_name: str, website_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for people at a company."""

        # Build search criteria
        search_params = {
            "sql": self._build_search_sql(company_name, website_url),
            "size": 10,  # Get up to 10 results
            "pretty": "true",
        }

        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

        url = f"{self.base_url}/person/search"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=search_params, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            elif response.status_code == 402:
                logger.warning("People Data Labs API quota exceeded")
                return []
            else:
                logger.warning(
                    f"People Data Labs API returned status {response.status_code}"
                )
                return []

    def _build_search_sql(
        self, company_name: str, website_url: Optional[str] = None
    ) -> str:
        """Build SQL query for People Data Labs."""

        # Start with company name search
        conditions = [f"job_company_name:'{company_name}'"]

        # Add website domain if available
        if website_url:
            domain = (
                website_url.replace("https://", "").replace("http://", "").split("/")[0]
            )
            conditions.append(f"job_company_website:'{domain}'")

        # Focus on senior roles
        role_conditions = [
            "job_title_role:(ceo OR cfo OR cto OR coo OR founder OR director OR head OR president OR vp)"
        ]

        # Combine conditions
        company_condition = " OR ".join(conditions)
        sql = f"SELECT * FROM person WHERE ({company_condition}) AND ({' OR '.join(role_conditions)})"

        return sql

    def _parse_contact(self, contact_data: Dict[str, Any]) -> Optional[ContactPerson]:
        """Parse People Data Labs response into ContactPerson object."""
        try:
            # Extract basic info
            full_name = contact_data.get("full_name")
            if not full_name:
                return None

            # Get job information
            experience = contact_data.get("experience", [])
            current_job = None
            for job in experience:
                if job.get("end_date") is None:  # Current job
                    current_job = job
                    break

            if not current_job:
                return None

            # Extract role and department info
            job_title = current_job.get("title", "")

            # Get contact information
            emails = contact_data.get("emails", [])
            email = None
            if emails:
                # Prefer work emails
                work_emails = [e for e in emails if e.get("type") == "work"]
                if work_emails:
                    email = work_emails[0].get("address")
                else:
                    email = emails[0].get("address")

            phone_numbers = contact_data.get("phone_numbers", [])
            phone = None
            if phone_numbers:
                phone = phone_numbers[0].get("number")

            # Get LinkedIn
            linkedin_url = None
            profiles = contact_data.get("profiles", [])
            for profile in profiles:
                if profile.get("network") == "linkedin":
                    linkedin_url = profile.get("url")
                    break

            # Validate LinkedIn URL
            if linkedin_url:
                from app.utils.contact_validator import validate_and_clean_linkedin_url

                linkedin_url = validate_and_clean_linkedin_url(linkedin_url)

            # Use ContactValidator for department and seniority normalization
            from app.utils.contact_validator import ContactValidator

            department = ContactValidator.normalize_department(job_title)
            seniority_level = ContactValidator.normalize_seniority(job_title)

            return ContactPerson(
                name=full_name,
                role=job_title,
                email=email,
                phone=phone,
                linkedin_url=linkedin_url,
                department=department,
                seniority_level=seniority_level,
            )

        except Exception as e:
            logger.warning(f"Failed to parse contact data: {str(e)}")
            return None


# Create a default instance
people_data_labs_client = PeopleDataLabsClient()
