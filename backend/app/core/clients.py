import httpx
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from datetime import datetime, timedelta
from aiolimiter import AsyncLimiter
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings
from app.db.session import SessionLocal
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
    # Class-level limiter to ensure rate limit is shared across all instances.
    limiter = AsyncLimiter(1, 1)  # 1 request per second.

    def __init__(self, api_key: str):
        super().__init__(api_key)

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> List[Dict[str, str]]:
        """Performs an asynchronous web search with a shared rate limit."""
        async with self.limiter:
            return await super().search_async(query, country, client)

    def _prepare_request(self, query: str, country: str):
        headers = {**self.DEFAULT_HEADERS, "X-Subscription-Token": self.api_key}
        params = {"q": query, "country": country.lower(), "count": 5}
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
        payload = {"q": query, "gl": country.lower(), "num": 5}
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
            "search_depth": "basic",
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
            "max_results": 5,
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
            "limit": 5,
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
    """Orchestrates searches across multiple providers based on a tier list."""

    # Tier list from search.todo: Brave is highest quality
    PROVIDER_TIER = ["brave", "tavily", "serper", "firecrawl"]

    def __init__(self, clients: dict, api_usage_service: ApiUsageService = None):
        self.clients = clients
        self.circuit_breaker = CircuitBreaker()
        # Semaphore to limit concurrent database access to a safe number
        self.db_semaphore = asyncio.Semaphore(10)
        # api_usage_service is now optional - we'll create our own sessions

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> tuple[list[dict], str | None]:
        """
        Attempts to search using providers in the tier order.
        Falls back to the next provider if a limit is reached or an error occurs.
        Returns the results and the name of the successful provider.
        """
        # Acquire semaphore to limit concurrent executions and thus DB connections
        async with self.db_semaphore:
            db_session = None
            try:
                # Create a new database session for this search operation
                db_session = SessionLocal()
                api_usage_service = ApiUsageService(db=db_session)

                for provider_name in self.PROVIDER_TIER:
                    # Check circuit breaker first
                    if self.circuit_breaker.is_disabled(provider_name):
                        logger.info(
                            f"⏭️ Skipping {provider_name}: temporarily disabled by circuit breaker"
                        )
                        continue

                    # Check if the API can be used (daily limit)
                    can_use = await asyncio.to_thread(
                        api_usage_service.can_use_api, provider_name
                    )

                    if not can_use:
                        logger.warning(
                            f"⚠️ Skipping {provider_name}: Daily limit reached."
                        )
                        continue

                    search_client = self.clients.get(provider_name)
                    if not search_client:
                        logger.error(
                            f"Misconfigured provider: {provider_name} not found."
                        )
                        continue

                    try:
                        logger.info(f"➡️ Trying search provider: {provider_name}")
                        results = await search_client.search_async(
                            query, country, client
                        )

                        if results:
                            logger.info(
                                f"✅ Success! Got {len(results)} results from {provider_name}."
                            )
                            # Record success and increment usage count
                            self.circuit_breaker.record_success(provider_name)
                            await asyncio.to_thread(
                                api_usage_service.increment_usage, provider_name
                            )
                            return results, provider_name
                        else:
                            logger.info(f"    - No results from {provider_name}.")

                    except (RateLimitError, TimeoutError) as e:
                        # These are expected recoverable errors
                        logger.warning(
                            f"⚠️ {provider_name} failed: {e}. Trying next provider."
                        )
                        self.circuit_breaker.record_failure(provider_name)
                        continue  # Try next provider
                    except Exception as e:
                        logger.error(
                            f"❌ Unexpected error with {provider_name}: {e}",
                            exc_info=True,
                        )
                        self.circuit_breaker.record_failure(provider_name)
                        # Don't increment usage on error, just try the next provider

                logger.warning("⚠️ All search providers failed or returned no results.")
                return [], None

            except Exception as e:
                logger.error(
                    f"❌ Critical error in MultiProviderSearchClient: {e}",
                    exc_info=True,
                )
                return [], None
            finally:
                # Ensure database session is always closed
                if db_session:
                    try:
                        db_session.close()
                    except Exception as e:
                        logger.error(f"❌ Error closing database session: {e}")


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
