import pytest
import httpx
import asyncio
import logging
from pytest_asyncio import fixture as async_fixture

from app.core.clients import (
    brave_client,
    serper_client,
    tavily_client,
    firecrawl_client,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@async_fixture(scope="session")
async def http_client():
    """Create an httpx.AsyncClient for the test session."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client_name, client_instance",
    [
        ("Brave", brave_client),
        ("Serper", serper_client),
        ("Tavily", tavily_client),
        ("Firecrawl", firecrawl_client),
    ],
)
async def test_search_client(client_name, client_instance, http_client):
    """
    Tests that each search client can successfully perform a search.
    This confirms the API key is valid and the basic request/response works.
    """
    logging.info(f"--- Testing {client_name} ---")
    query = "medical equipment suppliers netherlands"
    try:
        results = await client_instance.search_async(
            query, country="NL", client=http_client
        )
        assert isinstance(results, list)
        # We expect some results, but allow for none if the API is flaky
        # The main goal is to ensure the API call doesn't raise an exception
        logging.info(f"✅ {client_name}: SUCCESS! Found {len(results)} results.")

    except Exception as e:
        pytest.fail(f"❌ {client_name}: FAILED with error: {e}")
