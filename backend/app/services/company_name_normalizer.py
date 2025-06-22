import re


def normalize_name(name: str) -> str:
    """
    Cleans and standardizes a company name for consistent matching.

    - Converts to lowercase.
    - Removes common legal entity suffixes for NL/BE.
    - Removes punctuation except for hyphens.
    - Collapses extra whitespace.
    """
    if not isinstance(name, str):
        return ""

    normalized = name.lower()

    # Remove punctuation first, except for hyphens.
    # This turns "B.V." into "bv" and "(CommV)" into "commv", simplifying suffix removal.
    normalized = re.sub(r"[^\w\s-]", "", normalized)

    # List of suffixes to remove from the end of the name.
    # These should be checked after punctuation is removed.
    suffixes_to_remove = [
        "bv",
        "besloten vennootschap",
        "nv",
        "naamloze vennootschap",
        "vof",
        "vennootschap onder firma",
        "gcv",
        "gewone commanditaire vennootschap",
        "commv",
        "commanditaire vennootschap",
        "coop",
        "coöperatie",
        "inc",
        "ltd",
        "llc",
        "gmbh",
        "sarl",
        "sa",
    ]

    # Iteratively remove suffixes from the end of the string.
    for suffix in suffixes_to_remove:
        # Match the whole word suffix at the end of the string.
        pattern = r"\s+\b" + re.escape(suffix) + r"$"
        normalized = re.sub(pattern, "", normalized)

    # Collapse multiple whitespace characters into a single space and strip
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized
