import pytest
from app.services.company_name_normalizer import normalize_name


@pytest.mark.parametrize(
    "input_name, expected_name",
    [
        ("LongevAI B.V.", "longevai"),
        ("MediCapital Solutions N.V.", "medicapital solutions"),
        ("CleanEnergy Installateurs", "cleanenergy installateurs"),
        ("Dr. Jansen's Kliniek (CommV)", "dr jansens kliniek"),
        ("  Extra   Whitespace  Co. ", "extra whitespace co"),
        ("Punctuation!@#$Be-Gone", "punctuationbe-gone"),
    ],
)
def test_normalize_name(input_name, expected_name):
    """Tests that company names are normalized correctly."""
    assert normalize_name(input_name) == expected_name


def test_normalize_name_with_none():
    """Tests that the normalizer handles None input gracefully."""
    assert normalize_name(None) == ""
