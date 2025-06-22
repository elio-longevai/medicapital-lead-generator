import asyncio
import logging

import httpx

from app.core.clients import multi_provider_search_client
from app.graph.state import GraphState
from ..utils.search_utils import save_search_results

logger = logging.getLogger(__name__)


async def _execute_single_refinement_search(
    queries: list[str], country: str
) -> list[dict]:
    """Helper to run searches for one company using the multi-provider client."""
    all_results = []

    async with httpx.AsyncClient() as client:
        tasks = [
            multi_provider_search_client.search_async(query, country, client)
            for query in queries
        ]

        search_results_list = await asyncio.gather(*tasks, return_exceptions=True)

        for query, result in zip(queries, search_results_list):
            if isinstance(result, Exception):
                logger.error(
                    f"  > ❌ Refinement search failed for query '{query}': {result}"
                )
                continue

            results, provider = result
            if provider and results:
                # Save results for debugging
                save_search_results(query, provider, results)
                # Add provider info to each search result
                for res in results:
                    res["_provider"] = provider
                all_results.extend(results)

    return all_results


def execute_refinement_search(state: GraphState) -> dict:
    """Executes targeted web searches for missing data points."""
    logger.info("---🕸️ NODE: Executing Refinement Search---")
    refinement_results = {}
    country = state.target_country

    async def run_refinement_searches():
        tasks = []
        for index, queries in state.refinement_queries.items():
            company_name = state.enriched_companies[index]["lead"].discovered_name
            logger.info(f"  > Executing {len(queries)} searches for '{company_name}'")
            # Create a task for each company's search coroutine
            task = asyncio.create_task(
                _execute_single_refinement_search(queries, country)
            )
            tasks.append((index, task))

        # Wait for all tasks to complete
        results = await asyncio.gather(*[task for _, task in tasks])

        # Map results back to company index
        for (index, _), result_list in zip(tasks, results):
            if result_list:
                refinement_results[index] = result_list

    # Run the async orchestration
    asyncio.run(run_refinement_searches())

    logger.info(
        f"  > Refinement search complete. Found new data for {len(refinement_results)} companies."
    )
    return {"refinement_results": refinement_results}
