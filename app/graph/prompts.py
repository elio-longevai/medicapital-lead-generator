from pathlib import Path
from pydantic import BaseModel

def load_prompt(filename: str) -> str:
    """Loads a prompt template from the prompts directory."""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / filename
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file {filename} not found in prompts/ directory.")

# Load prompts from external files
ICP_STRUCTURING_PROMPT = load_prompt("icp_structuring.txt")
QUERY_GENERATION_PROMPT = load_prompt("query_generation.txt")
LEAD_TRIAGE_PROMPT = load_prompt("lead_triage.txt")

class CandidateLead(BaseModel):
    discovered_name: str
    source_url: str
    country: str
    primary_industry: str
    initial_reasoning: str
