import asyncio
import logging

import httpx

from app.graph.state import GraphState
from app.services.search_query_service import SearchQueryService
from .utils.search_utils import execute_search_with_provider

logger = logging.getLogger(__name__)


def execute_web_search(state: GraphState) -> dict:
    """Executes web searches concurrently using distributed providers."""
    queries_to_run = state.search_queries
    limit = state.search_query_limit

    if not queries_to_run:
        logger.warning("⚠️ No search queries were generated. Skipping web search.")
        return {"search_results": []}

    if limit and limit > 0:
        logger.info(f"---NODE: Executing Web Search (LIMITED to {limit} queries)---")
        queries_to_run = queries_to_run[:limit]
    else:
        logger.info(f"---NODE: Executing Web Search ({len(queries_to_run)} queries)---")

    async def _run_searches():
        """Internal async function to handle the concurrent searches."""
        all_results = []
        query_tracking_data = []  # Track queries for database storage
        providers = [
            "brave",
            "serper",
            "tavily",
            "firecrawl",
        ]  # Brave prioritized first

        async with httpx.AsyncClient() as client:
            tasks = []

            # Distribute queries across providers with Brave priority
            for i, query in enumerate(queries_to_run):
                provider = providers[i % len(providers)]
                task = execute_search_with_provider(
                    query, state.target_country, provider, client
                )
                tasks.append((query, provider, task))

            search_results_list = await asyncio.gather(
                *[task for _, _, task in tasks], return_exceptions=True
            )

            for i, (query, provider, result) in enumerate(
                zip([t[0] for t in tasks], [t[1] for t in tasks], search_results_list)
            ):
                if isinstance(result, Exception):
                    logger.error(
                        f"❌ Search failed for query '{query[:50]}...' with provider {provider}: {result}"
                    )
                    query_tracking_data.append(
                        (query, state.target_country, 0, [provider], False)
                    )
                else:
                    all_results.extend(result)
                    query_tracking_data.append(
                        (query, state.target_country, len(result), [provider], True)
                    )
                    logger.info(
                        f"✅ Search completed for query '{query[:30]}...' via {provider}: {len(result)} results"
                    )

        # Save query usage to database
        with SearchQueryService() as query_service:
            query_service.mark_queries_as_used_batch(query_tracking_data)
            stats = query_service.get_query_stats()
            logger.info(
                f"📈 Query stats: {stats['total_queries']} total, {stats['successful_queries']} successful"
            )

        return all_results

    # Run the async searches
    search_results = asyncio.run(_run_searches())

    logger.info(f"🎯 Total search results collected: {len(search_results)}")
    return {"search_results": search_results}
