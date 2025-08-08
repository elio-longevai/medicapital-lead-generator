"""
LLM Service Utilities

Shared utilities for LLM prompt handling and response processing.
Consolidates duplicate LLM interaction code across multiple services.
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

from ..core.clients import llm_client

logger = logging.getLogger(__name__)


class LLMService:
    """Shared utilities for LLM prompt handling and response processing."""

    @staticmethod
    def replace_prompt_variables(prompt: str, variables: Dict[str, Any]) -> str:
        """Replace variables in prompt template with actual values."""
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))
        return prompt

    @staticmethod
    async def invoke_with_timeout(
        prompt: str, variables: Dict[str, Any] = None, timeout: float = 60.0
    ) -> Optional[str]:
        """
        Invoke LLM with timeout and consistent error handling.

        Args:
            prompt: The prompt template or direct prompt
            variables: Variables to replace in prompt template
            timeout: Timeout in seconds

        Returns:
            LLM response content or None if failed
        """
        try:
            # Replace variables if provided
            if variables:
                prompt = LLMService.replace_prompt_variables(prompt, variables)

            # Invoke LLM with timeout
            response = await asyncio.wait_for(
                llm_client.ainvoke(prompt), timeout=timeout
            )

            # Parse response content
            return LLMService.parse_response(response)

        except asyncio.TimeoutError:
            logger.error(f"LLM request timed out after {timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"LLM request failed: {str(e)}")
            return None

    @staticmethod
    def parse_response(response) -> Optional[str]:
        """Parse LLM response content consistently."""
        try:
            if hasattr(response, "content"):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                return str(response)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None

    @staticmethod
    def extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from LLM response text."""
        if not response_text:
            return None

        try:
            # Try to parse entire response as JSON first
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass

        # Look for JSON object in response using regex
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        logger.warning("No valid JSON found in LLM response")
        return None

    @staticmethod
    def extract_json_array_from_response(
        response_text: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Extract JSON array from LLM response text."""
        if not response_text:
            return None

        try:
            # Try to parse entire response as JSON array first
            result = json.loads(response_text.strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        # Look for JSON array in response using regex
        json_match = re.search(r"\[.*\]", response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        logger.warning("No valid JSON array found in LLM response")
        return None

    @staticmethod
    async def extract_contacts_from_text(
        company_name: str, text_content: str, max_contacts: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Extract contact information from text using standardized LLM prompt.

        Args:
            company_name: Name of the company
            text_content: Text content to extract contacts from
            max_contacts: Maximum number of contacts to extract

        Returns:
            List of contact dictionaries
        """
        extraction_prompt = f"""
Je bent een expert in het extraheren van contactinformatie uit webtekst. Analyseer de volgende tekst en extraheer relevante contactpersonen voor het bedrijf "{company_name}".

TEKST:
{text_content[:8000]}  # Limit to prevent token overflow

INSTRUCTIES:
1. Zoek naar personen met leidinggevende functies: CEO, CFO, CTO, COO, Directors, Heads of departments
2. Focus op Sales, Finance, HR, Operations, en Technology functies
3. Extraheer naam, functie, e-mail, telefoon (indien beschikbaar)
4. Bepaal department en seniority level op basis van functietitel
5. BELANGRIJK: Als je algemene contactgegevens vindt (info@, sales@, algemeen telefoonnummer) zonder specifieke persoon, maak dan een entry met name "Contactgegevens" en de gevonden contactinfo
6. ALLEEN contacten met e-mail OF telefoon worden opgeslagen
7. LINKEDIN PROFIELEN: Zoek naar LinkedIn profiel URLs in de tekst. Als je een LinkedIn URL vindt die overeenkomt met een contactpersoon, voeg deze toe aan het contact.

DEPARTMENTS: Sales, Finance, HR, Operations, Technology, Marketing, Legal, Other
SENIORITY LEVELS: C-Level, Director, Manager, Specialist, Other

Geef maximaal {max_contacts} relevante contactpersonen terug in JSON formaat:
[
  {{
    "name": "Volledige naam (of 'Contactgegevens' voor algemene info)",
    "role": "Functietitel in het Nederlands",
    "email": "email@company.com of null",
    "phone": "telefoonnummer of null", 
    "linkedin_url": "https://linkedin.com/in/username of null",
    "department": "department naam",
    "seniority_level": "seniority level"
  }}
]

Als geen relevante contacten gevonden worden, geef dan een lege lijst [] terug.
        """

        response_text = await LLMService.invoke_with_timeout(
            extraction_prompt, timeout=45.0
        )

        if not response_text:
            return []

        contacts_data = LLMService.extract_json_array_from_response(response_text)
        if not contacts_data:
            return []

        # Validate and clean contact data
        valid_contacts = []
        for contact_data in contacts_data:
            if isinstance(contact_data, dict) and contact_data.get("name"):
                valid_contacts.append(contact_data)

        logger.info(f"Extracted {len(valid_contacts)} contacts for {company_name}")
        return valid_contacts

    @staticmethod
    async def generate_contact_search_queries(
        company_name: str, website_url: Optional[str] = None, country: str = "NL"
    ) -> List[str]:
        """
        Generate targeted search queries for finding key decision-makers using LLM.

        Args:
            company_name: Name of the company
            website_url: Company website URL (optional)
            country: Country code for localization

        Returns:
            List of optimized search queries
        """
        domain = ""
        if website_url:
            domain = (
                website_url.replace("https://", "").replace("http://", "").split("/")[0]
            )

        prompt = f"""
Je bent een expert in het vinden van bedrijfscontacten via zoekmachines. 
Genereer 6 zeer specifieke en effectieve zoekopdrachten om belangrijke beslissers en hun contactgegevens te vinden voor:

Bedrijf: {company_name}
Website: {website_url or "Onbekend"}
Land: {country}

DOEL: Vind de volgende personen met hun e-mail en telefoonnummer:
- CEO / Directeur / Algemeen Directeur
- CFO / Financieel Directeur
- Head of Sales / Sales Director
- COO / Operations Manager
- HR Manager / Head of HR

INSTRUCTIES:
1. Gebruik verschillende zoekstrategieën: LinkedIn, bedrijfswebsite, nieuwsartikelen, directories
2. Focus op Nederlandse/Belgische bronnen voor NL/BE bedrijven
3. Combineer bedrijfsnaam met functietitels en contact termen
4. Gebruik site: operators voor gerichte zoekacties
5. Prioriteer queries die waarschijnlijk e-mailadressen en telefoonnummers opleveren

Geef EXACT 6 zoekopdrachten terug in JSON formaat:
[
  "zoekopdracht 1",
  "zoekopdracht 2",
  "zoekopdracht 3",
  "zoekopdracht 4",
  "zoekopdracht 5",
  "zoekopdracht 6"
]

Voor Nederlandse/Belgische bedrijven, gebruik ook Nederlandse zoektermen.
        """

        response_text = await LLMService.invoke_with_timeout(prompt, timeout=30.0)

        if not response_text:
            # Fallback to basic queries if LLM fails
            queries = [
                f'"{company_name}" CEO CFO director email contact',
                f'"{company_name}" management team contact',
            ]
            if domain:
                queries.append(f"site:{domain} contact team management")
            queries.append(f'site:linkedin.com "{company_name}" CEO director')
            return queries[:4]

        # Extract queries from response
        queries = LLMService.extract_json_array_from_response(response_text)

        if not queries or not isinstance(queries, list):
            # Fallback to basic queries
            queries = [
                f'"{company_name}" CEO CFO director email contact',
                f'"{company_name}" management team contact',
            ]
            if domain:
                queries.append(f"site:{domain} contact team management")
            queries.append(f'site:linkedin.com "{company_name}" CEO director')
            return queries[:4]

        # Ensure we have string queries
        valid_queries = []
        for query in queries:
            if isinstance(query, str) and query.strip():
                valid_queries.append(query.strip())

        # If we don't have enough valid queries, add some basic ones
        if len(valid_queries) < 4:
            if domain:
                valid_queries.append(f"site:{domain} contact team management")
            valid_queries.append(f'site:linkedin.com "{company_name}" CEO director')
            valid_queries.append(f'"{company_name}" contact email phone')

        logger.info(f"Generated {len(valid_queries)} search queries for {company_name}")
        return valid_queries[:6]  # Return max 6 queries

    @staticmethod
    def build_prompt_with_context(
        base_prompt: str, context_data: Dict[str, Any], instruction_suffix: str = ""
    ) -> str:
        """Build a prompt with context data and optional instruction suffix."""
        prompt = base_prompt

        # Add context data
        if context_data:
            context_section = "\nCONTEXT:\n"
            for key, value in context_data.items():
                context_section += f"{key}: {value}\n"
            prompt += context_section

        # Add instruction suffix
        if instruction_suffix:
            prompt += f"\n{instruction_suffix}"

        return prompt
