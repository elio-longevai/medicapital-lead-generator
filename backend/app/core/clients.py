import httpx
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
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


class BaseSearchClient(ABC):
    """Abstract base class for a web search client."""

    BASE_URL: str
    DEFAULT_HEADERS: Dict[str, str] = {"Accept": "application/json"}
    REQUEST_METHOD: str = "GET"  # Can be overridden by subclasses

    def __init__(self, api_key: str):
        self.api_key = api_key
        # Limiter is created per-request in async method to avoid event loop issues
        # self.limiter = AsyncLimiter(1, 1) # Default: 1 request per second

    @abstractmethod
    def _prepare_request(
        self, query: str, country: str
    ) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
        """
        Prepare the URL, headers, and params/payload for the request.
        Returns a tuple of (url, headers, params_or_payload).
        """
        pass

    @abstractmethod
    def _parse_response(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Parse the JSON response from the API into a standardized list of results.
        """
        pass

    def search(self, query: str, country: str) -> List[Dict[str, str]]:
        """Performs a synchronous web search."""
        url, headers, params_or_payload = self._prepare_request(query, country)
        request_key = "params" if self.REQUEST_METHOD == "GET" else "json"

        try:
            with httpx.Client() as client:
                response = client.request(
                    self.REQUEST_METHOD,
                    url,
                    headers=headers,
                    **{request_key: params_or_payload},
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_response(data)
        except Exception as e:
            logger.error(f"❌ {self.__class__.__name__} API error: {e}", exc_info=True)
            return []

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> List[Dict[str, str]]:
        """Performs an asynchronous web search."""
        url, headers, params_or_payload = self._prepare_request(query, country)
        request_key = "params" if self.REQUEST_METHOD == "GET" else "json"

        try:
            limiter = AsyncLimiter(1, 1)  # 1 req/sec; re-created for each call
            async with limiter:
                response = await client.request(
                    self.REQUEST_METHOD,
                    url,
                    headers=headers,
                    **{request_key: params_or_payload},
                )
                response.raise_for_status()
                data = response.json()
                return self._parse_response(data)
        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ {self.__class__.__name__} API HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(
                f"❌ {self.__class__.__name__} API async error: {e}", exc_info=True
            )
            return []


class BraveSearchClient(BaseSearchClient):
    """A client for the Brave Search API."""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def _prepare_request(self, query: str, country: str):
        headers = {**self.DEFAULT_HEADERS, "X-Subscription-Token": self.api_key}
        params = {"q": query, "country": country.lower(), "count": 5}
        return self.BASE_URL, headers, params

    def _parse_response(self, data: dict) -> list[dict]:
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "url": item.get("url", ""),
                }
            )
        return results


class SerperClient(BaseSearchClient):
    """A client for the Serper API."""

    BASE_URL = "https://google.serper.dev/search"
    REQUEST_METHOD = "POST"

    def _prepare_request(self, query: str, country: str):
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "gl": country.lower(), "num": 5}
        return self.BASE_URL, headers, payload

    def _parse_response(self, data: dict) -> list[dict]:
        results = []
        for item in data.get("organic", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "description": item.get("snippet", ""),
                    "url": item.get("link", ""),
                }
            )
        return results


class TavilyClient(BaseSearchClient):
    """A client for the Tavily API."""

    BASE_URL = "https://api.tavily.com/search"
    REQUEST_METHOD = "POST"

    def _get_country_name(self, country_code: str) -> str:
        """Convert country code to full country name for Tavily API."""
        country_mapping = {
            "NL": "Netherlands",
            "BE": "Belgium",
            "US": "United States",
            "UK": "United Kingdom",
            "DE": "Germany",
            "FR": "France",
        }
        return country_mapping.get(country_code.upper(), "Netherlands")

    def _prepare_request(self, query: str, country: str):
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": 5,
            "country": self._get_country_name(country),
        }
        return self.BASE_URL, headers, payload

    def _parse_response(self, data: dict) -> list[dict]:
        results = []
        for item in data.get("results", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "description": item.get("content", ""),
                    "url": item.get("url", ""),
                }
            )
        return results


class FirecrawlClient(BaseSearchClient):
    """A client for the Firecrawl API."""

    BASE_URL = "https://api.firecrawl.dev/v0/search"
    REQUEST_METHOD = "POST"

    def _get_country_name(self, country_code: str) -> str:
        """Convert country code to full country name for Firecrawl API."""
        country_mapping = {
            "NL": "Netherlands",
            "BE": "Belgium",
            "US": "United States",
            "UK": "United Kingdom",
            "DE": "Germany",
            "FR": "France",
        }
        return country_mapping.get(country_code.upper())

    def _prepare_request(self, query: str, country: str):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "pageOptions": {"fetchPageContent": False},
            "limit": 5,
        }
        # Add location only if country is valid
        location = self._get_country_name(country)
        if location:
            payload["location"] = location

        return self.BASE_URL, headers, payload

    def _parse_response(self, data: dict) -> list[dict]:
        results = []
        for item in data.get("data", []):
            results.append(
                {
                    "title": item.get("metadata", {}).get("title", ""),
                    "description": item.get("metadata", {}).get("description", ""),
                    "url": item.get("url", ""),
                }
            )
        return results


class MultiProviderSearchClient:
    """Orchestrates searches across multiple providers based on a tier list."""

    # Tier list from search.todo: Firecrawl is highest quality
    PROVIDER_TIER = ["firecrawl", "tavily", "brave", "serper"]

    def __init__(self, clients: dict, api_usage_service: ApiUsageService = None):
        self.clients = clients
        # api_usage_service is now optional - we'll create our own sessions

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> list[dict]:
        """
        Attempts to search using providers in the tier order.
        Falls back to the next provider if a limit is reached or an error occurs.
        """
        # Create a new database session for this search operation
        db_session = SessionLocal()
        api_usage_service = ApiUsageService(db=db_session)

        try:
            for provider_name in self.PROVIDER_TIER:
                # Check if the API can be used (rate limit)
                can_use = await asyncio.to_thread(
                    api_usage_service.can_use_api, provider_name
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
                            api_usage_service.increment_usage, provider_name
                        )
                        return results
                    else:
                        logger.info(f"    - No results from {provider_name}.")
                except Exception as e:
                    logger.error(f"❌ Error with {provider_name}: {e}", exc_info=True)
                    # Don't increment usage on error, just try the next provider

            logger.warning("⚠️  All search providers failed or returned no results.")
            return []
        finally:
            db_session.close()


# Instantiate clients for use in the graph
llm_client = get_llm_client()

# Individual search clients
brave_client = BraveSearchClient(api_key=settings.BRAVE_API_KEY)
serper_client = SerperClient(api_key=settings.SERPER_API_KEY)
tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
firecrawl_client = FirecrawlClient(api_key=settings.FIRECRAWL_API_KEY)

# Multi-provider orchestrator - create api_usage_service per request
multi_provider_search_client = MultiProviderSearchClient(
    clients={
        "brave": brave_client,
        "serper": serper_client,
        "tavily": tavily_client,
        "firecrawl": firecrawl_client,
    },
    api_usage_service=None,  # Will be created per request
)
