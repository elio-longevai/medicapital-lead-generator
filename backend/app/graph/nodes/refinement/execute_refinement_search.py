import asyncio
import logging

import httpx

from app.graph.state import GraphState
from ..utils.search_utils import execute_search_with_provider

logger = logging.getLogger(__name__)


async def _execute_single_refinement_search(
    queries: list[str], country: str
) -> list[dict]:
    """Helper to run searches for one company using distributed providers."""
    all_results = []
    providers = ["brave", "serper", "tavily", "firecrawl"]

    async with httpx.AsyncClient() as client:
        tasks = []

        # Distribute queries across providers with Brave priority
        for i, query in enumerate(queries):
            provider = providers[i % len(providers)]
            task = execute_search_with_provider(query, country, provider, client)
            tasks.append((provider, task))  # Store provider name with task

        search_results_list = await asyncio.gather(
            *[task for _, task in tasks], return_exceptions=True
        )

        # Process results with provider information
        for (provider, _), result in zip(tasks, search_results_list):
            if isinstance(result, Exception):
                logger.error(f"  > ❌ Refinement search task failed: {result}")
                continue

            # Add provider info to each search result
            for res in result:
                res["_provider"] = provider
                all_results.append(res)

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
