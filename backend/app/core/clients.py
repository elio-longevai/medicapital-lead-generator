import httpx
import asyncio
import logging
from aiolimiter import AsyncLimiter
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings
from app.db.session import SessionLocal
from app.services.api_usage_service import ApiUsageService

logger = logging.getLogger(__name__)


def get_llm_client() -> ChatGoogleGenerativeAI:
    """Returns a configured instance of the Gemini client."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-05-20",
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.0,
    )


class BraveSearchClient:
    """A client for the Brave Search API."""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.limiter = AsyncLimiter(1, 1)  # 1 request per second

    def search(self, query: str, country: str) -> list[dict]:
        """Performs a web search and returns the results."""
        headers = {"X-Subscription-Token": self.api_key, "Accept": "application/json"}
        params = {
            "q": query,
            "country": country.lower(),
            "count": 5,
        }  # Reduced from 20 to 5

        try:
            with httpx.Client() as client:
                response = client.get(self.BASE_URL, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("web", {}).get("results", [])
        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ Brave Search API error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during Brave Search: {e}")
            return []

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> list[dict]:
        """Performs an async web search using Brave."""
        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json",
        }
        params = {"q": query, "country": country.lower()}

        try:
            async with self.limiter:
                response = await client.get(
                    self.BASE_URL, headers=headers, params=params
                )
            response.raise_for_status()
            data = response.json()
            # Standardize the output
            return data.get("web", {}).get("results", [])
        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ Brave Search API error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during Brave Search: {e}")
            return []


class SerperClient:
    """A client for the Serper Search API."""

    BASE_URL = "https://google.serper.dev/search"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> list[dict]:
        """Performs an async web search using Serper."""
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {"q": query, "gl": country.lower(), "num": 5}

        try:
            response = await client.post(self.BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            # Standardize the output to match the expected format
            return [
                {"title": item.get("title"), "description": item.get("snippet")}
                for item in data.get("organic", [])
            ]
        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ Serper API error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during Serper Search: {e}")
            return []


class TavilyClient:
    """A client for the Tavily Search API."""

    BASE_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.limiter = AsyncLimiter(100, 60)  # 100 requests per minute

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> list[dict]:
        """Performs an async web search using Tavily."""
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
        }

        try:
            async with self.limiter:
                response = await client.post(self.BASE_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            # Standardize the output
            return [
                {"title": item.get("title"), "description": item.get("content")}
                for item in data.get("results", [])
            ]
        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ Tavily API error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"❌ An unexpected error occurred during Tavily Search: {e}")
            return []


class FirecrawlClient:
    """A client for the Firecrawl Search + Scrape API."""

    BASE_URL = "https://api.firecrawl.dev/v0/search"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.limiter = AsyncLimiter(10, 60)  # 10 requests per minute

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> list[dict]:
        """Performs a search and returns full page content."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Use pageOptions to get the full markdown content
        payload = {"query": query, "pageOptions": {"fetchPageContent": True}}

        try:
            async with self.limiter:
                response = await client.post(
                    self.BASE_URL, headers=headers, json=payload
                )
            response.raise_for_status()
            data = response.json()
            # Standardize the output, using markdown as the description
            return [
                {
                    "title": item.get("metadata", {}).get("title"),
                    "description": item.get("markdown"),
                }
                for item in data.get("data", [])
                if item.get("markdown")  # Ensure we have content
            ]
        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ Firecrawl API error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(
                f"❌ An unexpected error occurred during Firecrawl Search: {e}"
            )
            return []


class MultiProviderSearchClient:
    """Orchestrates searches across multiple providers based on a tier list."""

    # Tier list from search.todo: Firecrawl is highest quality
    PROVIDER_TIER = ["firecrawl", "tavily", "brave", "serper"]

    def __init__(self, clients: dict, api_usage_service: ApiUsageService):
        self.clients = clients
        self.api_usage_service = api_usage_service

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> list[dict]:
        """
        Attempts to search using providers in the tier order.
        Falls back to the next provider if a limit is reached or an error occurs.
        """
        for provider_name in self.PROVIDER_TIER:
            # Check if the API can be used (rate limit)
            can_use = await asyncio.to_thread(
                self.api_usage_service.can_use_api, provider_name
            )

            if not can_use:
                logger.warning(f"⚠️  Skipping {provider_name}: Daily limit reached.")
                continue

            logger.info(f"➡️  Trying search provider: {provider_name}")
            search_client = self.clients.get(provider_name)
            if not search_client:
                continue

            try:
                results = await search_client.search_async(query, country, client)
                if results:
                    logger.info(
                        f"✅ Success! Got {len(results)} results from {provider_name}."
                    )
                    # Increment usage count on success
                    await asyncio.to_thread(
                        self.api_usage_service.increment_usage, provider_name
                    )
                    return results
                else:
                    logger.info(f"    - No results from {provider_name}.")
            except Exception as e:
                logger.error(f"❌ Error with {provider_name}: {e}", exc_info=True)
                # Don't increment usage on error, just try the next provider

        logger.warning("⚠️  All search providers failed or returned no results.")
        return []


# Instantiate clients for use in the graph
llm_client = get_llm_client()

# Note: For a long-running app, a scoped session or per-request session is better.
# Given the script-like nature of the graph execution, we create a new session here.
db_session = SessionLocal()
api_usage_service = ApiUsageService(db=db_session)

# Individual search clients
brave_client = BraveSearchClient(api_key=settings.BRAVE_API_KEY)
serper_client = SerperClient(api_key=settings.SERPER_API_KEY)
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
firecrawl_client = FirecrawlClient(api_key=settings.FIRECRAWL_API_KEY)

# Multi-provider orchestrator
multi_provider_search_client = MultiProviderSearchClient(
    clients={
        "brave": brave_client,
        "serper": serper_client,
        "tavily": tavily_client,
        "firecrawl": firecrawl_client,
    },
    api_usage_service=api_usage_service,
)
