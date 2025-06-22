import logging
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


def save_search_results(query: str, provider: str, results: list[dict]):
    """Save search results to a file for debugging purposes."""
    try:
        # Ensure directory exists
        results_dir = (
            Path(__file__).parent.parent.parent.parent.parent / "search_results"
        )
        results_dir.mkdir(exist_ok=True)

        # Create filename with timestamp and truncated query
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_query = "".join(c for c in query if c.isalnum() or c in " -_")[:50]
        clean_query = clean_query.replace(" ", "_")
        filename = f"{provider}_{timestamp}_{clean_query}.txt"

        filepath = results_dir / filename

        # Format results for saving
        content = f"Query: {query}\nProvider: {provider.upper()}\nTimestamp: {timestamp}\nResults: {len(results)}\n\n"

        for i, result in enumerate(results, 1):
            content += f"Result {i}:\n"
            content += f"Title: {result.get('title', 'N/A')}\n"
            content += f"URL: {result.get('url', 'N/A')}\n"
            content += f"Description: {result.get('description') or ''}...\n"
            content += "-" * 80 + "\n"

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"💾 Saved {len(results)} results to {filename}")

    except Exception as e:
        logger.error(f"❌ Failed to save search results: {e}")
