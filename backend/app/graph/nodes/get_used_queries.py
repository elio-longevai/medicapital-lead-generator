import logging

from app.graph.state import GraphState
from app.services.search_query_service import SearchQueryService

logger = logging.getLogger(__name__)


def get_used_queries(state: GraphState) -> dict:
    """Fetches all previously used search queries from the database."""
    logger.info("---NODE: Fetching Used Queries---")
    country = state.target_country
    with SearchQueryService() as query_service:
        used_queries = query_service.get_all_used_queries(country)
        logger.info(
            f"  > Found {len(used_queries)} used queries for country '{country}'."
        )
        return {"used_queries": used_queries}
