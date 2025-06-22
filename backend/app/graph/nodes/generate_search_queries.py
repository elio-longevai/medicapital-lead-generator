import json
import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

from app.core.clients import llm_client
from app.graph import prompts
from app.graph.state import GraphState

logger = logging.getLogger(__name__)


def generate_search_queries(state: GraphState) -> dict:
    """Generates strategic search queries based on the structured ICP."""
    logger.info("---NODE: Generating Search Queries---")
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=prompts.QUERY_GENERATION_PROMPT,
        input_variables=["structured_icp", "used_queries"],
    )
    chain = prompt | llm_client | parser

    # Format the list of used queries into a JSON string for the prompt
    used_queries_str = json.dumps(state.used_queries, indent=2)

    queries_result = chain.invoke(
        {"structured_icp": state.structured_icp, "used_queries": used_queries_str}
    )

    # The parser may return a dict {'queries': [...]} or a direct list [...]
    if hasattr(queries_result, "get"):
        return {"search_queries": queries_result.get("queries", [])}
    return {"search_queries": queries_result}
