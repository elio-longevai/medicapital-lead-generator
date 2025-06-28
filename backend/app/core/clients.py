import httpx
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from datetime import datetime, timedelta
from aiolimiter import AsyncLimiter
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings
from app.services.api_usage_service import ApiUsageService

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Custom exception for when a search provider API rate limit is hit."""

    pass


class TimeoutError(Exception):
    """Custom exception for when a search provider times out."""

    pass


class CircuitBreakerError(Exception):
    """Custom exception for when a provider is temporarily disabled."""

    pass


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
    DEFAULT_TIMEOUT: float = 15.0  # Reduced from 30.0 for faster failure detection

    def __init__(self, api_key: str):
        self.api_key = api_key

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
            with httpx.Client(timeout=self.DEFAULT_TIMEOUT) as client:
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
            response = await client.request(
                self.REQUEST_METHOD,
                url,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT,
                **{request_key: params_or_payload},
            )
            response.raise_for_status()
            return self._parse_response(response.json())
        except httpx.TimeoutException as e:
            logger.warning(
                f"⏰ {self.__class__.__name__} API timeout after {self.DEFAULT_TIMEOUT}s"
            )
            raise TimeoutError(f"Timeout for {self.__class__.__name__}") from e
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"⚠️ {self.__class__.__name__} API rate limit exceeded.")
                raise RateLimitError(
                    f"Rate limit hit for {self.__class__.__name__}"
                ) from e
            logger.error(
                f"❌ {self.__class__.__name__} API HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(
                f"❌ {self.__class__.__name__} API async error: {e}", exc_info=True
            )
            return []


class CountryMappingMixin:
    """Provides a utility to map country codes to full names."""

    COUNTRY_MAPPING = {
        "NL": "Netherlands",
        "BE": "Belgium",
        "US": "United States",
        "UK": "United Kingdom",
        "DE": "Germany",
        "FR": "France",
    }

    def _get_country_name(self, country_code: str, default: str = "Netherlands") -> str:
        """Convert country code to full country name."""
        return self.COUNTRY_MAPPING.get(country_code.upper(), default)


class BraveSearchClient(BaseSearchClient, CountryMappingMixin):
    """A client for the Brave Search API."""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        # Limiter will be created lazily to avoid event loop binding
        self._limiter = None

    @property
    def limiter(self):
        """Lazy initialization of limiter to ensure it's bound to the current event loop."""
        if self._limiter is None:
            self._limiter = AsyncLimiter(1, 1)
        return self._limiter

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> List[Dict[str, str]]:
        """Performs an asynchronous web search with a shared rate limit."""
        async with self.limiter:
            return await super().search_async(query, country, client)

    def _prepare_request(self, query: str, country: str):
        headers = {**self.DEFAULT_HEADERS, "X-Subscription-Token": self.api_key}
        params = {"q": query, "country": country.lower(), "count": 10}
        return self.BASE_URL, headers, params

    def _parse_response(self, data: dict) -> list[dict]:
        return [
            {
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
            }
            for item in data.get("web", {}).get("results", [])
        ]


class SerperClient(BaseSearchClient, CountryMappingMixin):
    """A client for the Serper API."""

    BASE_URL = "https://google.serper.dev/search"
    REQUEST_METHOD = "POST"

    def _prepare_request(self, query: str, country: str):
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "gl": country.lower(), "num": 10}
        return self.BASE_URL, headers, payload

    def _parse_response(self, data: dict) -> list[dict]:
        return [
            {
                "title": item.get("title", ""),
                "description": item.get("snippet", ""),
                "url": item.get("link", ""),
            }
            for item in data.get("organic", [])
        ]


class TavilyClient(BaseSearchClient, CountryMappingMixin):
    """A client for the Tavily API."""

    BASE_URL = "https://api.tavily.com/search"
    REQUEST_METHOD = "POST"

    def _prepare_request(self, query: str, country: str):
        headers = {"Content-Type": "application/json"}
        payload = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": True,
            "max_results": 10,
            "country": self._get_country_name(country),
        }
        return self.BASE_URL, headers, payload

    def _parse_response(self, data: dict) -> list[dict]:
        return [
            {
                "title": item.get("title", ""),
                "description": item.get("content", ""),
                "url": item.get("url", ""),
            }
            for item in data.get("results", [])
        ]


class FirecrawlClient(BaseSearchClient, CountryMappingMixin):
    """A client for the Firecrawl API."""

    BASE_URL = "https://api.firecrawl.dev/v0/search"
    REQUEST_METHOD = "POST"
    DEFAULT_TIMEOUT: float = 10.0  # Shorter timeout for Firecrawl due to instability

    def _prepare_request(self, query: str, country: str):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "pageOptions": {"fetchPageContent": False},
            "limit": 10,
        }
        # Add location only if country is valid
        location = self._get_country_name(country)
        if location:
            payload["location"] = location

        return self.BASE_URL, headers, payload

    def _parse_response(self, data: dict) -> list[dict]:
        return [
            {
                "title": item.get("metadata", {}).get("title", ""),
                "description": item.get("metadata", {}).get("description", ""),
                "url": item.get("url", ""),
            }
            for item in data.get("data", [])
        ]


class CircuitBreaker:
    """Simple circuit breaker to temporarily disable failing providers."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout  # seconds
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_times: Dict[str, datetime] = {}
        self.disabled_until: Dict[str, datetime] = {}

    def is_disabled(self, provider: str) -> bool:
        """Check if provider is currently disabled."""
        if provider not in self.disabled_until:
            return False

        if datetime.now() >= self.disabled_until[provider]:
            # Recovery time has passed, re-enable provider
            del self.disabled_until[provider]
            self.failure_counts[provider] = 0
            logger.info(f"🔄 Re-enabled provider {provider} after recovery timeout")
            return False

        return True

    def record_failure(self, provider: str):
        """Record a failure for the provider."""
        self.failure_counts[provider] = self.failure_counts.get(provider, 0) + 1
        self.last_failure_times[provider] = datetime.now()

        if self.failure_counts[provider] >= self.failure_threshold:
            self.disabled_until[provider] = datetime.now() + timedelta(
                seconds=self.recovery_timeout
            )
            logger.warning(
                f"🚫 Temporarily disabled provider {provider} due to {self.failure_counts[provider]} failures"
            )

    def record_success(self, provider: str):
        """Record a success for the provider."""
        if provider in self.failure_counts:
            self.failure_counts[provider] = 0


class MultiProviderSearchClient:
    """Orchestrates searches across multiple providers."""

    PROVIDER_TIER = ["serper", "tavily", "brave", "firecrawl"]

    def __init__(self, clients: Dict[str, BaseSearchClient]):
        self.clients = clients
        self.circuit_breaker = CircuitBreaker()
        # Semaphore will be created lazily to avoid event loop binding
        self._db_semaphore = None

    @property
    def db_semaphore(self):
        """Lazy initialization of semaphore to ensure it's bound to the current event loop."""
        if self._db_semaphore is None:
            self._db_semaphore = asyncio.Semaphore(10)
        return self._db_semaphore

    async def _try_provider(
        self,
        provider_name: str,
        query: str,
        country: str,
        client: httpx.AsyncClient,
        api_usage_service: ApiUsageService,
    ) -> List[Dict[str, str]] | None:
        """Attempt a search with a single provider, handling errors."""
        if self.circuit_breaker.is_disabled(provider_name):
            logger.info(f"⏭️ Skipping {provider_name}: temporarily disabled")
            return None

        search_client = self.clients.get(provider_name)
        if not search_client:
            logger.error(f"Misconfigured provider: {provider_name} not found.")
            return None

        try:
            logger.info(f"➡️ Trying search provider: {provider_name}")
            if results := await search_client.search_async(query, country, client):
                logger.info(
                    f"✅ Success! Got {len(results)} results from {provider_name}."
                )
                self.circuit_breaker.record_success(provider_name)
                await asyncio.to_thread(
                    api_usage_service.increment_usage, provider_name
                )
                return results
            logger.info(f"    - No results from {provider_name}.")
        except (RateLimitError, TimeoutError) as e:
            logger.warning(f"⚠️ {provider_name} failed: {e}. Trying next.")
            self.circuit_breaker.record_failure(provider_name)
        except Exception as e:
            logger.error(
                f"❌ Unexpected error with {provider_name}: {e}", exc_info=True
            )
            self.circuit_breaker.record_failure(provider_name)
        return None

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> tuple[list[dict], str | None]:
        """
        Attempts searches using providers in tier order, with concurrency limits.
        """
        async with self.db_semaphore:
            try:
                api_usage_service = ApiUsageService()
                for provider_name in self.PROVIDER_TIER:
                    if results := await self._try_provider(
                        provider_name, query, country, client, api_usage_service
                    ):
                        return results, provider_name
                logger.warning("⚠️ All search providers failed or returned no results.")
                return [], None
            except Exception as e:
                logger.error(f"❌ Critical error in search client: {e}", exc_info=True)
                return [], None


# Instantiate clients for use in the graph
llm_client = get_llm_client()


def create_multi_provider_search_client() -> MultiProviderSearchClient:
    """Factory to create a new instance of the search client."""
    return MultiProviderSearchClient(
        clients={
            "brave": BraveSearchClient(api_key=settings.BRAVE_API_KEY),
            "serper": SerperClient(api_key=settings.SERPER_API_KEY),
            "tavily": TavilyClient(api_key=settings.TAVILY_API_KEY),
            "firecrawl": FirecrawlClient(api_key=settings.FIRECRAWL_API_KEY),
        }
    )


# Default instance for convenience, but factory should be preferred
# for operations running in different event loops.
multi_provider_search_client = create_multi_provider_search_client()
