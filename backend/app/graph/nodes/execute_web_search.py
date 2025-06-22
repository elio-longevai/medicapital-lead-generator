import asyncio
import logging

import httpx

from app.core.clients import create_multi_provider_search_client
from app.graph.state import GraphState
from app.services.search_query_service import SearchQueryService
from .utils.search_utils import save_search_results

logger = logging.getLogger(__name__)


def execute_web_search(state: GraphState) -> dict:
    """Executes web searches concurrently using the multi-provider client."""
    queries_to_run = state.search_queries
    limit = state.queries_per_icp

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
        # Create a fresh search client instance for this event loop
        search_client = create_multi_provider_search_client()
        all_results = []
        query_tracking_data = []  # Track queries for database storage

        async with httpx.AsyncClient() as client:
            tasks = [
                search_client.search_async(query, state.target_country, client)
                for query in queries_to_run
            ]

            search_results_list = await asyncio.gather(*tasks, return_exceptions=True)

            for query, result in zip(queries_to_run, search_results_list):
                if isinstance(result, Exception):
                    logger.error(
                        f"❌ Search failed for query '{query[:50]}...' after all retries: {result}"
                    )
                    query_tracking_data.append(
                        (query, state.target_country, 0, [], False)
                    )
                else:
                    results, provider = result
                    if provider and results:
                        save_search_results(query, provider, results)
                        all_results.extend(results)
                        query_tracking_data.append(
                            (
                                query,
                                state.target_country,
                                len(results),
                                [provider],
                                True,
                            )
                        )
                        logger.info(
                            f"✅ Search completed for query '{query[:30]}...' via {provider}: {len(results)} results"
                        )
                    else:
                        # This case happens if all providers fail without exceptions
                        query_tracking_data.append(
                            (query, state.target_country, 0, [], False)
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
