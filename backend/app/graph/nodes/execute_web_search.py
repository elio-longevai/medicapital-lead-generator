import asyncio
import logging

import httpx

from app.core.clients import create_multi_provider_search_client
from app.graph.state import GraphState
from app.services.search_query_service import SearchQueryService

logger = logging.getLogger(__name__)


def _save_query_usage(query_tracking_data):
    """Synchronous helper to save query usage to the database."""
    with SearchQueryService() as query_service:
        query_service.mark_queries_as_used_batch(query_tracking_data)
        stats = query_service.get_query_stats()
        logger.info(
            f"📈 Query stats: {stats['total_queries']} total, {stats['successful_queries']} successful"
        )


async def execute_web_search(state: GraphState) -> dict:
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
                query_tracking_data.append((query, state.target_country, 0, [], False))
            else:
                results, provider = result
                if provider and results:
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

    # Save query usage to database in a thread to avoid blocking the event loop
    if query_tracking_data:
        await asyncio.to_thread(_save_query_usage, query_tracking_data)

    logger.info(f"🎯 Total search results collected: {len(all_results)}")
    return {"search_results": all_results}
