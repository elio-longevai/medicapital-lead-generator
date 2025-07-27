"""
Contact Validation Utilities

Shared validation logic for contact information across all services.
Consolidates duplicate validation code from contact_enrichment.py,
people_data_labs.py, and hunter_io.py.
"""

import re
import logging
from typing import Optional, List
from ..graph.nodes.schemas import ContactPerson

logger = logging.getLogger(__name__)


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

        # Skip generic emails for individual contacts
        email_prefix = email.split("@")[0]
        if email_prefix in ContactValidator.GENERIC_EMAIL_PREFIXES:
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
        validated_contacts = []

        for contact in contacts:
            cleaned_contact = ContactValidator.validate_and_clean_contact(contact)
            if cleaned_contact:
                validated_contacts.append(cleaned_contact)

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
