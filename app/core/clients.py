import httpx
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings


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
            print(
                f"Brave Search API error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            print(f"An unexpected error occurred during Brave Search: {e}")
            return []

    async def search_async(
        self, query: str, country: str, client: httpx.AsyncClient
    ) -> list[dict]:
        """Performs an async web search."""
        headers = {"X-Subscription-Token": self.api_key, "Accept": "application/json"}
        params = {
            "q": query,
            "country": country.lower(),
            "count": 5,
        }  # Reduced from 20 to 5

        try:
            response = await client.get(self.BASE_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("web", {}).get("results", [])
        except httpx.HTTPStatusError as e:
            print(
                f"Brave Search API error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            print(f"An unexpected error occurred during Brave Search: {e}")
            return []


# Instantiate clients for use in the graph
brave_client = BraveSearchClient(api_key=settings.BRAVE_API_KEY)
llm_client = get_llm_client()
