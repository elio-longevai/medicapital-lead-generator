"""
Contact Validation Utilities

Shared validation logic for contact information across all services.
Consolidates duplicate validation code from contact_enrichment.py,
people_data_labs.py, and hunter_io.py.
"""

import logging
import re
from typing import List, Optional

from app.graph.nodes.schemas import ContactPerson

logger = logging.getLogger(__name__)


def validate_and_clean_linkedin_url(url: Optional[str]) -> Optional[str]:
    """
    Validate and clean LinkedIn URL to ensure it's properly formatted.

    Args:
        url: LinkedIn URL to validate

    Returns:
        Cleaned LinkedIn URL or None if invalid
    """
    if not url:
        return None

    # Remove any extra whitespace
    url = url.strip()

    # Common LinkedIn URL patterns
    linkedin_patterns = [
        r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?",
        r"https?://(?:www\.)?linkedin\.com/company/[a-zA-Z0-9\-_]+/?",
        r"linkedin\.com/in/[a-zA-Z0-9\-_]+/?",
        r"linkedin\.com/company/[a-zA-Z0-9\-_]+/?",
    ]

    for pattern in linkedin_patterns:
        if re.match(pattern, url):
            # Ensure it starts with https://
            if not url.startswith("http"):
                url = "https://" + url
            return url

    return None


class ContactValidator:
    """Shared utilities for contact validation and normalization."""

    # Shared mapping dictionaries
    DEPARTMENT_MAPPING = {
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

    SENIORITY_MAPPING = {
        "ceo": "C-Level",
        "cfo": "C-Level",
        "cto": "C-Level",
        "coo": "C-Level",
        "chief": "C-Level",
        "director": "Director",
        "head of": "Director",
        "vp": "Director",
        "vice president": "Director",
        "manager": "Manager",
        "specialist": "Specialist",
        "analyst": "Specialist",
        "coordinator": "Specialist",
    }

    GENERIC_EMAIL_PREFIXES = {
        "info",
        "contact",
        "sales",
        "support",
        "admin",
        "office",
        "hello",
        "general",
        "main",
        "inquiry",
        "help",
    }

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email format using regex."""
        if not email:
            return False
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def clean_email(email: str, contact_name: str = None) -> Optional[str]:
        """Clean and normalize email address."""
        if not email:
            return None

        email = email.strip().lower()

        # Allow generic emails for "Contactgegevens" entries
        if contact_name and contact_name.lower() in ["contactgegevens", "contact info"]:
            return email if ContactValidator.is_valid_email(email) else None

        # Skip generic emails for individual contacts using the more robust regex approach
        if ContactValidator._is_generic_email(email):
            return None

        return email if ContactValidator.is_valid_email(email) else None

    @staticmethod
    def clean_phone(phone: str) -> Optional[str]:
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

    @staticmethod
    def normalize_department(department: str) -> Optional[str]:
        """Normalize department names to standard values."""
        if not department:
            return None

        dept_lower = department.lower()
        for key, value in ContactValidator.DEPARTMENT_MAPPING.items():
            if key in dept_lower:
                return value

        return "Other"

    @staticmethod
    def normalize_seniority(seniority: str) -> Optional[str]:
        """Normalize seniority levels to standard values."""
        if not seniority:
            return None

        seniority_lower = seniority.lower()

        for key, value in ContactValidator.SENIORITY_MAPPING.items():
            if key in seniority_lower:
                return value

        return "Other"

    @staticmethod
    def validate_and_clean_contact(contact: ContactPerson) -> Optional[ContactPerson]:
        """Validate and clean a single contact with comprehensive checks."""
        # Skip contacts without name or role
        if not contact.name or not contact.role:
            return None

        # Clean and validate email
        if contact.email:
            contact.email = ContactValidator.clean_email(contact.email, contact.name)

        # Clean phone number
        if contact.phone:
            contact.phone = ContactValidator.clean_phone(contact.phone)

        # IMPORTANT: Only save contacts that have actual contact information
        # Skip contacts that have neither email nor phone
        if not contact.email and not contact.phone:
            logger.debug(
                f"Skipping contact {contact.name} - no email or phone information"
            )
            return None

        # Normalize department and seniority
        contact.department = ContactValidator.normalize_department(contact.department)
        contact.seniority_level = ContactValidator.normalize_seniority(
            contact.seniority_level
        )

        return contact

    @staticmethod
    def validate_and_clean_contacts(
        contacts: List[ContactPerson],
    ) -> List[ContactPerson]:
        """Validate and clean a list of contacts, removing duplicates and invalid entries."""
        if not contacts:
            return []

        # Clean and validate each contact
        cleaned_contacts = []
        seen_emails = set()
        seen_names = set()

        for contact in contacts:
            if not contact:
                continue

            # Clean LinkedIn URL
            if contact.linkedin_url:
                contact.linkedin_url = validate_and_clean_linkedin_url(
                    contact.linkedin_url
                )

            # Skip contacts without any contact method
            if not contact.email and not contact.phone:
                continue

            # Skip generic email addresses
            if contact.email and ContactValidator._is_generic_email(contact.email):
                continue

            # Skip duplicates based on email or name
            if contact.email and contact.email in seen_emails:
                continue
            if contact.name and contact.name in seen_names:
                continue

            # Add to tracking sets
            if contact.email:
                seen_emails.add(contact.email)
            if contact.name:
                seen_names.add(contact.name)

            cleaned_contacts.append(contact)

        logger.info(
            f"Cleaned {len(contacts)} contacts to {len(cleaned_contacts)} valid contacts"
        )
        return cleaned_contacts

    @staticmethod
    def prioritize_dutch_contacts(contacts: List[ContactPerson]) -> List[ContactPerson]:
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

    @staticmethod
    def _is_generic_email(email: str) -> bool:
        """Check if email is a generic business email."""
        if not email:
            return False

        generic_patterns = [
            r"^info@",
            r"^contact@",
            r"^hello@",
            r"^sales@",
            r"^support@",
            r"^admin@",
            r"^noreply@",
            r"^no-reply@",
            r"^webmaster@",
            r"^postmaster@",
        ]

        email_lower = email.lower()
        for pattern in generic_patterns:
            if re.match(pattern, email_lower):
                return True

        return False
