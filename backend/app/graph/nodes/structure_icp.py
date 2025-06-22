import json
import logging
from pathlib import Path

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.clients import llm_client
from app.graph import prompts
from app.graph.state import GraphState

logger = logging.getLogger(__name__)


def structure_icp(state: GraphState) -> dict:
    """Parses the raw ICP text into a structured dictionary. Caches result to a file."""
    logger.info("---NODE: Structuring ICP---")
    icp_name = state.icp_name

    # Define cache path based on the ICP name
    base_prompts_dir = Path(__file__).parent.parent.parent.parent / "prompts"
    cache_path = base_prompts_dir / f"structured_{icp_name}.json"

    # Check if cached file exists
    if cache_path.exists():
        logger.info(f"  > Found cached structured ICP at {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            structured_icp = json.load(f)
        return {"structured_icp": structured_icp}

    # If not cached, generate it
    logger.info("  > No cache found. Generating structured ICP from raw text...")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.ICP_STRUCTURING_PROMPT,
        input_variables=["raw_icp_text"],
        partial_variables={"parser_instructions": parser.get_format_instructions()},
    )
    chain = prompt | llm_client | parser
    structured_icp = chain.invoke({"raw_icp_text": state.raw_icp_text})

    # Save to cache
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(structured_icp, f, indent=2, ensure_ascii=False)
    logger.info(f"  > Saved new structured ICP to {cache_path}")

    return {"structured_icp": structured_icp}
