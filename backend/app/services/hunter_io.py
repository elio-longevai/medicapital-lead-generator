"""
Hunter.io client for email finding and verification.

This service provides email validation and finding capabilities using Hunter.io API's free tier.
"""

import logging
from typing import List, Optional, Dict, Any
import httpx

from app.core.settings import settings
from app.graph.nodes.schemas import ContactPerson

logger = logging.getLogger(__name__)


class HunterIOClient:
    """Client for Hunter.io API - email finding and verification."""

    def __init__(self):
        self.api_key = getattr(settings, "HUNTER_IO_API_KEY", None)
        self.base_url = "https://api.hunter.io/v2"
        self.timeout = 10.0

    async def find_emails(self, company_domain: str) -> List[str]:
        """
        Find email addresses for a company domain.

        Args:
            company_domain: Company domain (e.g., "example.com")

        Returns:
            List of email addresses found
        """
        if not self.api_key:
            logger.debug("Hunter.io API key not configured")
            return []

        try:
            url = f"{self.base_url}/domain-search"
            params = {
                "domain": company_domain,
                "api_key": self.api_key,
                "type": "personal",  # Focus on personal emails, not generic ones
                "limit": 10,
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    emails = []

                    for email_data in data.get("data", {}).get("emails", []):
                        email = email_data.get("value")
                        confidence = email_data.get("confidence", 0)

                        # Only include emails with reasonable confidence
                        if email and confidence >= 50:
                            emails.append(email)

                    logger.info(
                        f"Found {len(emails)} emails for domain {company_domain}"
                    )
                    return emails

                elif response.status_code == 401:
                    logger.warning("Hunter.io API key invalid")
                    return []
                elif response.status_code == 429:
                    logger.warning("Hunter.io API rate limit exceeded")
                    return []
                else:
                    logger.warning(
                        f"Hunter.io API returned status {response.status_code}"
                    )
                    return []

        except Exception as e:
            logger.error(
                f"Hunter.io email search failed for {company_domain}: {str(e)}"
            )
            return []

    async def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify if an email address is valid and deliverable.

        Args:
            email: Email address to verify

        Returns:
            Dictionary with verification results
        """
        if not self.api_key:
            logger.debug("Hunter.io API key not configured")
            return {"valid": None, "score": 0}

        try:
            url = f"{self.base_url}/email-verifier"
            params = {"email": email, "api_key": self.api_key}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    result = data.get("data", {})

                    return {
                        "valid": result.get("result") == "deliverable",
                        "score": result.get("score", 0),
                        "status": result.get("result"),
                        "regexp": result.get("regexp"),
                        "gibberish": result.get("gibberish"),
                        "disposable": result.get("disposable"),
                        "webmail": result.get("webmail"),
                    }
                else:
                    logger.warning(
                        f"Hunter.io email verification failed with status {response.status_code}"
                    )
                    return {"valid": None, "score": 0}

        except Exception as e:
            logger.error(f"Hunter.io email verification failed for {email}: {str(e)}")
            return {"valid": None, "score": 0}

    async def enhance_contacts_with_emails(
        self, contacts: List[ContactPerson], company_domain: Optional[str] = None
    ) -> List[ContactPerson]:
        """
        Enhance contact list by finding and verifying emails.

        Args:
            contacts: List of existing contacts
            company_domain: Company domain for email finding

        Returns:
            Enhanced list of contacts with validated emails
        """
        if not self.api_key:
            return contacts

        enhanced_contacts = []

        # Find additional emails for the domain if provided
        domain_emails = []
        if company_domain:
            domain_emails = await self.find_emails(company_domain)

        # Process existing contacts
        for contact in contacts:
            enhanced_contact = contact.model_copy()

            # Verify existing email if present
            if contact.email:
                verification = await self.verify_email(contact.email)
                if verification["valid"] is False:
                    logger.info(f"Email {contact.email} failed verification")
                    enhanced_contact.email = None

            # Try to find email if missing
            if not enhanced_contact.email and contact.name and company_domain:
                # Try to match name with domain emails
                name_parts = contact.name.lower().split()
                for domain_email in domain_emails:
                    email_lower = domain_email.lower()
                    # Simple matching logic
                    if any(part in email_lower for part in name_parts if len(part) > 2):
                        verification = await self.verify_email(domain_email)
                        if (
                            verification["valid"] is not False
                        ):  # Include uncertain emails
                            enhanced_contact.email = domain_email
                            break

            enhanced_contacts.append(enhanced_contact)

        # Add any remaining domain emails as new contacts
        used_emails = {c.email for c in enhanced_contacts if c.email}
        for email in domain_emails:
            if email not in used_emails:
                verification = await self.verify_email(email)
                if verification["valid"] is not False and verification["score"] >= 70:
                    # Create a basic contact with just the email
                    new_contact = ContactPerson(
                        name=None,
                        role=None,
                        email=email,
                        phone=None,
                        department="Other",
                        seniority_level="Other",
                    )
                    enhanced_contacts.append(new_contact)

                    # Limit additional contacts
                    if len(enhanced_contacts) >= 10:
                        break

        return enhanced_contacts


# Create a default instance
hunter_io_client = HunterIOClient()
