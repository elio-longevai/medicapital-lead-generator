import re

def normalize_name(name: str) -> str:
    """
    Cleans and standardizes a company name for consistent matching.
    
    - Converts to lowercase.
    - Removes common legal entity suffixes for NL/BE.
    - Removes punctuation and extra whitespace.
    """
    if not isinstance(name, str):
        return ""
        
    # Lowercase the name
    normalized = name.lower()
    
    # Remove common legal suffixes
    suffixes = [
        r'\b(b\.v\.|bv|besloten vennootschap)\b',
        r'\b(n\.v\.|nv|naamloze vennootschap)\b',
        r'\b(vof|vennootschap onder firma)\b',
        r'\b(gcv|gewone commanditaire vennootschap)\b',
        r'\b(commv|commanditaire vennootschap)\b',
        r'\b(coop|coöperatie)\b',
        r'\b(inc|ltd|llc|gmbh|sarl|sa)\b',
    ]
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
        
    # Remove punctuation except hyphens
    normalized = re.sub(r'[^\w\s-]', '', normalized)
    
    # Collapse multiple spaces/hyphens and strip whitespace
    normalized = re.sub(r'[\s-]+', ' ', normalized).strip()
    
    return normalized
