import asyncio
import logging
import httpx
import pytest
import re
from collections import defaultdict
from typing import Dict, List, Optional

from app.core.clients import create_multi_provider_search_client
from app.graph.nodes.refinement.generate_refinement_queries import (
    generate_employee_queries,
)
from app.graph import prompts
from app.core.clients import llm_client
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Top 4 companies from the screenshot to test (reduced for faster testing)
TEST_COMPANIES = [
    {"name": "Memodo", "country": "NL"},
    {"name": "Eco Technics", "country": "NL"},
    {"name": "MR Solar", "country": "NL"},
    {"name": "SolarComfort", "country": "NL"},
]


class MultiProviderQueryAnalyzer:
    """Analyzes which queries work best with multi-provider search for employee count discovery."""

    def __init__(self):
        self.query_performance = defaultdict(
            list
        )  # query_type -> list of (company, success, employee_count, provider)
        self.company_results = {}  # company -> {query_type: (success, employee_count, provider, raw_text)}

    def add_result(
        self,
        company: str,
        query_type: str,
        query_text: str,
        success: bool,
        employee_count: Optional[str],
        provider: Optional[str],
        raw_search_text: str = "",
    ):
        """Add a query result for analysis."""
        self.query_performance[query_type].append(
            (company, success, employee_count, query_text, provider)
        )
        if company not in self.company_results:
            self.company_results[company] = {}
        self.company_results[company][query_type] = (
            success,
            employee_count,
            provider,
            raw_search_text[:200],
        )

    def extract_employee_numbers_from_text(self, text: str) -> List[str]:
        """Extract potential employee numbers from search result text."""
        # Look for patterns like "50 employees", "10-25 werknemers", "501-1000", etc.
        patterns = [
            r"\b(\d{1,5})\s*(?:employees?|werknemers?|medewerkers?)\b",
            r"\b(\d{1,4}[-–]\d{1,5})\s*(?:employees?|werknemers?|medewerkers?)\b",
            r"\b(\d{1,4}[-–]\d{1,5})\b(?=\s*(?:employees?|people|staff))",
            r"(?:Company Size[:\s]*|Size[:\s]*|Employees?[:\s]*|Team[:\s]*|Staff[:\s]*)(\d{1,5})",
            r"(?:Company Size[:\s]*|Size[:\s]*|Employees?[:\s]*|Team[:\s]*|Staff[:\s]*)(\d{1,4}[-–]\d{1,5})",
        ]

        found_numbers = []
        text_lower = text.lower()

        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            found_numbers.extend(matches)

        return list(set(found_numbers))  # Remove duplicates

    def log_detailed_results(self):
        """Log detailed results for each company and query type."""
        logger.info("\n" + "=" * 100)
        logger.info("🔍 MULTI-PROVIDER QUERY PERFORMANCE ANALYSIS - DETAILED RESULTS")
        logger.info("=" * 100)

        for company_info in TEST_COMPANIES:
            company_name = company_info["name"]
            logger.info(f"\n🏢 {company_name}:")
            logger.info("-" * 60)

            if company_name in self.company_results:
                results = self.company_results[company_name]
                best_result = None
                best_employee_count = None
                best_provider = None

                for query_type, (
                    success,
                    employee_count,
                    provider,
                    raw_text,
                ) in results.items():
                    if success and employee_count and employee_count.lower() != "null":
                        # Try to extract numbers from the raw search text too
                        extracted_numbers = self.extract_employee_numbers_from_text(
                            raw_text
                        )
                        extracted_info = (
                            f" | Extracted from text: {extracted_numbers}"
                            if extracted_numbers
                            else ""
                        )

                        logger.info(
                            f"  ✅ {query_type:20} | Provider: {provider:8} | LLM Result: {employee_count}{extracted_info}"
                        )
                        if not best_result:
                            best_result = query_type
                            best_employee_count = employee_count
                            best_provider = provider
                    else:
                        provider_info = f" (tried {provider})" if provider else ""
                        logger.info(
                            f"  ❌ {query_type:20} | No employee count found{provider_info}"
                        )

                if best_result:
                    logger.info(
                        f"  🎯 BEST RESULT: {best_employee_count} employees (via {best_result} using {best_provider})"
                    )
                else:
                    logger.info("  ⚠️  NO EMPLOYEE COUNT FOUND BY ANY QUERY")
            else:
                logger.info("  ❗ No search results available")

    def log_query_performance_summary(self):
        """Log overall query type performance statistics."""
        logger.info("\n" + "=" * 100)
        logger.info("📊 QUERY TYPE PERFORMANCE SUMMARY")
        logger.info("=" * 100)

        query_stats = {}
        provider_stats = defaultdict(int)

        for query_type, results in self.query_performance.items():
            total_tests = len(results)
            successful_tests = sum(
                1
                for _, success, employee_count, _, provider in results
                if success and employee_count and employee_count.lower() != "null"
            )
            success_rate = (
                (successful_tests / total_tests * 100) if total_tests > 0 else 0
            )

            # Count provider usage
            for _, success, employee_count, _, provider in results:
                if (
                    success
                    and employee_count
                    and employee_count.lower() != "null"
                    and provider
                ):
                    provider_stats[provider] += 1

            query_stats[query_type] = {
                "total": total_tests,
                "successful": successful_tests,
                "success_rate": success_rate,
                "results": results,
            }

            logger.info(
                f"📈 {query_type:25} | "
                f"Success: {successful_tests:2d}/{total_tests:2d} | "
                f"Rate: {success_rate:5.1f}%"
            )

        # Log provider performance
        if provider_stats:
            logger.info("\n📊 PROVIDER SUCCESS COUNT:")
            for provider, count in sorted(
                provider_stats.items(), key=lambda x: x[1], reverse=True
            ):
                logger.info(f"   🔧 {provider:10} | {count} successful extractions")

        # Find best performing query type
        if query_stats:
            best_query_type = max(
                query_stats.items(),
                key=lambda x: (x[1]["successful"], x[1]["success_rate"]),
            )

            logger.info(f"\n🏆 BEST PERFORMING QUERY TYPE: {best_query_type[0]}")
            logger.info(
                f"   📊 {best_query_type[1]['successful']} successes out of {best_query_type[1]['total']} attempts"
            )
            logger.info(f"   📈 {best_query_type[1]['success_rate']:.1f}% success rate")

            # Show which companies worked with the best query type
            successful_companies = [
                f"{company} (via {provider})"
                for company, success, count, _, provider in best_query_type[1][
                    "results"
                ]
                if success and count and count.lower() != "null"
            ]
            if successful_companies:
                logger.info(
                    f"   🎯 Successful companies: {', '.join(successful_companies)}"
                )

        return query_stats


async def test_query_with_multi_provider(
    company_name: str,
    country: str,
    query_type: str,
    query_text: str,
    search_client,
    analyzer: MultiProviderQueryAnalyzer,
) -> bool:
    """Test a single query with multi-provider search and extract employee count."""

    logger.info(f"   Testing {query_type}: {query_text}")

    # Use shorter timeout to prevent hanging
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Use multi-provider search with automatic fallback
            results, provider = await search_client.search_async(
                query_text, country, client
            )

            if results and provider:
                logger.info(f"      Got {len(results)} search results from {provider}")

                # Extract using LLM with timeout protection
                employee_count = await extract_employee_count_from_results_with_timeout(
                    company_name, results
                )

                # Also try direct text extraction for comparison
                full_text = " ".join(
                    [
                        f"{r.get('title', '')} {r.get('description', '')}"
                        for r in results
                    ]
                )
                extracted_numbers = analyzer.extract_employee_numbers_from_text(
                    full_text
                )

                success = employee_count and employee_count.lower() != "null"
                if success:
                    logger.info(
                        f"      ✅ LLM extracted: {employee_count} (via {provider})"
                    )
                    if extracted_numbers:
                        logger.info(
                            f"      📊 Direct extraction found: {extracted_numbers}"
                        )
                else:
                    logger.info(
                        f"      ❌ No employee count extracted (tried {provider})"
                    )
                    if extracted_numbers:
                        logger.info(
                            f"      📊 But direct extraction found: {extracted_numbers}"
                        )

                analyzer.add_result(
                    company_name,
                    query_type,
                    query_text,
                    success,
                    employee_count,
                    provider,
                    full_text,
                )
                return success
            else:
                logger.info("      ❌ No search results from any provider")
                analyzer.add_result(
                    company_name, query_type, query_text, False, None, None, ""
                )
                return False

        except asyncio.TimeoutError:
            logger.error("      ❌ Query timed out")
            analyzer.add_result(
                company_name, query_type, query_text, False, None, None, ""
            )
            return False
        except Exception as e:
            logger.error(f"      ❌ Query failed: {str(e)[:100]}")
            analyzer.add_result(
                company_name, query_type, query_text, False, None, None, ""
            )
            return False


async def extract_employee_count_from_results_with_timeout(
    company_name: str, search_results: List[Dict], timeout_seconds: int = 15
) -> Optional[str]:
    """Extract employee count from search results using LLM with timeout protection."""

    # Combine search results into snippet
    combined_snippets = "\n\n".join(
        [
            f"Source: {r.get('url', 'N/A')}\nTitle: {r.get('title', '')}\n{r.get('description', '')}"
            for r in search_results[:5]  # Use top 5 results
        ]
    )

    # Use the refinement prompt to extract employee count
    prompt = PromptTemplate.from_template(prompts.REFINEMENT_PROMPT)
    chain = prompt | llm_client | StrOutputParser()

    try:
        # Add timeout protection for LLM call
        result = await asyncio.wait_for(
            chain.ainvoke(
                {
                    "company_name": company_name,
                    "snippet": combined_snippets,
                    "field_name": "aantal medewerkers",  # Use Dutch term
                }
            ),
            timeout=timeout_seconds,
        )

        return result.strip() if result else None
    except asyncio.TimeoutError:
        logger.warning(
            f"LLM extraction timed out for {company_name} after {timeout_seconds}s"
        )
        return None
    except Exception as e:
        logger.warning(f"LLM extraction failed for {company_name}: {str(e)}")
        return None


@pytest.mark.asyncio
async def test_multi_provider_employee_count_query_performance():
    """
    Test different query types with multi-provider search (Serper + Tavily fallback)
    to determine which work best for employee count discovery.
    """
    logger.info("🚀 Starting Multi-Provider Employee Count Query Performance Test")
    logger.info(
        f"📋 Testing {len(TEST_COMPANIES)} companies with different query types"
    )
    logger.info("🔧 Using multi-provider search: Serper → Tavily → Brave → Firecrawl")

    search_client = create_multi_provider_search_client()
    analyzer = MultiProviderQueryAnalyzer()

    # Search for each company with different query types
    for company_info in TEST_COMPANIES:
        company_name = company_info["name"]
        country = company_info["country"]

        logger.info("\n" + "=" * 80)
        logger.info(f"🏢 TESTING: {company_name}")
        logger.info("=" * 80)

        # Generate different types of queries
        linkedin_queries = generate_employee_queries(company_name, country, tier="flat")

        query_types = {
            "linkedin_site_nl": linkedin_queries[
                0
            ],  # site:linkedin.com/company/{} medewerkers
            "linkedin_site_en": linkedin_queries[
                2
            ],  # site:linkedin.com/company/{} employees
            "linkedin_general": linkedin_queries[
                3
            ],  # "{Company}" linkedin company size
            "traditional_nl": f'"{company_name}" aantal medewerkers',
            "company_size": f'"{company_name}" company size employees',
            "team_size": f'"{company_name}" team size werknemers',
        }

        # Test each query type
        for query_type, query_text in query_types.items():
            await test_query_with_multi_provider(
                company_name, country, query_type, query_text, search_client, analyzer
            )
            # Reduced delay to speed up testing
            await asyncio.sleep(0.2)

        # Shorter delay between companies
        await asyncio.sleep(0.5)

    # Log detailed analysis
    analyzer.log_detailed_results()
    query_stats = analyzer.log_query_performance_summary()

    # Test assertions
    logger.info(
        f"\n📋 Completed searches for {len(analyzer.company_results)} companies"
    )

    # Calculate overall statistics
    total_attempts = (
        sum(stats["total"] for stats in query_stats.values()) if query_stats else 0
    )
    total_successes = (
        sum(stats["successful"] for stats in query_stats.values()) if query_stats else 0
    )
    overall_success_rate = (
        (total_successes / total_attempts * 100) if total_attempts > 0 else 0
    )

    logger.info("📊 Overall Results:")
    logger.info(f"   🎯 Total successful extractions: {total_successes}")
    logger.info(f"   📈 Overall success rate: {overall_success_rate:.1f}%")

    if total_successes > 0:
        logger.info(
            "🎉 Successfully found employee counts using multi-provider search!"
        )
    else:
        logger.warning(
            "⚠️ No employee counts found - may indicate need for query refinement"
        )

    logger.info("\n✅ Multi-provider query performance test completed!")


if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_multi_provider_employee_count_query_performance())
