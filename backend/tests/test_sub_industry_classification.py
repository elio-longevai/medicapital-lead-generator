"""Tests for sub-industry classification functionality."""

import pytest
from unittest.mock import Mock
from app.graph.nodes.schemas import EnrichedCompanyData, ContactPerson
from app.services.company_service import CompanyService


class TestSubIndustryClassification:
    """Test suite for sub-industry classification feature."""

    def test_enriched_company_data_sub_industry_field(self):
        """Test that EnrichedCompanyData model includes sub_industry field."""
        # Test with sub_industry value
        data = EnrichedCompanyData(
            entity_type="end_user",
            sub_industry="Tandartspraktijk",
            company_description="Test clinic",
        )
        assert data.sub_industry == "Tandartspraktijk"
        assert data.entity_type == "end_user"

        # Test with None sub_industry (default)
        data_none = EnrichedCompanyData(entity_type="supplier")
        assert data_none.sub_industry is None

    def test_enriched_company_data_with_contacts(self):
        """Test that EnrichedCompanyData properly handles contacts and sub_industry."""
        contacts = [
            ContactPerson(name="Dr. Test", role="Eigenaar", email="test@clinic.nl")
        ]

        data = EnrichedCompanyData(
            entity_type="end_user",
            sub_industry="Cosmetische Kliniek",
            contacts=contacts,
            company_description="Moderne cosmetische kliniek",
            equipment_needs="Laser apparatuur",
        )

        assert data.sub_industry == "Cosmetische Kliniek"
        assert data.entity_type == "end_user"
        assert len(data.contacts) == 1
        assert data.contacts[0].name == "Dr. Test"
        assert data.contacts[0].role == "Eigenaar"

    def test_company_service_sub_industry_response(self):
        """Test that CompanyService includes sub_industry in response transformation."""
        service = CompanyService()

        # Mock company document with sub_industry
        mock_company = {
            "_id": "507f1f77bcf86cd799439011",
            "discovered_name": "Test Clinic",
            "primary_industry": "Gezondheidszorg",
            "country": "NL",
            "status": "qualified",
            "sub_industry": "Orthopedische Kliniek",
            "entity_type": "end_user",
            "contacts": [
                {"name": "Dr. Smith", "role": "Orthopeed", "email": "smith@clinic.nl"}
            ],
            "company_description": "Gespecialiseerde orthopedische kliniek",
            "qualification_details": {
                "financial_stability": 85,
                "equipment_need": 90,
                "timing": 75,
                "decision_authority": 80,
            },
            "created_at": Mock(),
            "updated_at": Mock(),
        }

        # Mock datetime objects
        mock_company[
            "created_at"
        ].replace.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"
        mock_company[
            "updated_at"
        ].replace.return_value.isoformat.return_value = "2024-01-01T00:00:00Z"

        # Transform company
        response = service._transform_company(mock_company)

        # Verify sub_industry is included
        assert response.subIndustry == "Orthopedische Kliniek"
        assert response.entityType == "end_user"
        assert len(response.contacts) == 1
        assert response.contacts[0].name == "Dr. Smith"
        assert response.contacts[0].email == "smith@clinic.nl"

    @pytest.mark.parametrize(
        "sub_industry,expected",
        [
            ("Tandartspraktijk", "Tandartspraktijk"),
            ("Zonnepaneel Installateur", "Zonnepaneel Installateur"),
            ("Medische Apparatuur Producent", "Medische Apparatuur Producent"),
            (None, None),
            ("", ""),
        ],
    )
    def test_sub_industry_field_validation(self, sub_industry, expected):
        """Test sub_industry field accepts various valid inputs."""
        data = EnrichedCompanyData(entity_type="end_user", sub_industry=sub_industry)
        assert data.sub_industry == expected

    def test_contact_person_schema(self):
        """Test ContactPerson schema validation."""
        # Valid contact
        contact = ContactPerson(
            name="Dr. Jan Jansen", role="Tandarts", email="j.jansen@praktijk.nl"
        )
        assert contact.name == "Dr. Jan Jansen"
        assert contact.role == "Tandarts"
        assert contact.email == "j.jansen@praktijk.nl"

        # Contact with None values
        contact_partial = ContactPerson(name="Dr. Smith", role=None, email=None)
        assert contact_partial.name == "Dr. Smith"
        assert contact_partial.role is None
        assert contact_partial.email is None
