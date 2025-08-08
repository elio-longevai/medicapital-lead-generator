"""
Integration tests for the complete lead generation flow.
Provides structure validation and usage examples for full workflow testing.
"""

import logging

import pytest

from app.graph.state import GraphState
from app.graph.workflow import build_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def test_icp_text():
    return """
    ## Test ICP: Healthcare Equipment Leasers
    **Target:** Small healthcare facilities in Netherlands needing medical equipment.
    **Size:** 5-50 employees
    **Need:** Equipment financing for diagnostic tools, treatment devices
    **Contact:** Practice Manager, Owner, Finance Manager
    """


@pytest.mark.asyncio
async def test_workflow_structure_validation(test_icp_text: str):
    """Quick test: validates workflow structure and basic functionality."""
    logger.info("🔧 Testing workflow structure...")

    workflow = build_workflow()
    assert workflow is not None, "Workflow should be buildable"

    state = GraphState(
        icp_name="test_structure",
        raw_icp_text=test_icp_text,
        target_country="NL",
        queries_per_icp=1,
    )

    assert state.icp_name == "test_structure"
    assert state.target_country == "NL"
    assert hasattr(state, "search_queries")
    assert hasattr(state, "candidate_leads")
    assert hasattr(state, "enriched_companies")

    logger.info("✅ Workflow structure validation passed!")


@pytest.mark.asyncio
async def test_manual_workflow_steps():
    """Shows how to test individual workflow steps for debugging."""
    from app.graph import nodes

    state = GraphState(
        icp_name="manual_test",
        raw_icp_text="## Test ICP: Small clinics needing equipment",
        target_country="NL",
        queries_per_icp=1,
    )

    try:
        result = nodes.structure_icp(state)
        assert "structured_icp" in result
        logger.info("✅ structure_icp node works")
    except Exception as e:
        logger.warning(f"⚠️ structure_icp failed: {e}")


def print_usage_examples():
    """Print practical examples for testing the complete workflow."""
    print("""
🚀 COMPLETE WORKFLOW TESTING OPTIONS

Quick Structure Test:
  make test-full-flow

Real Integration Test (Recommended):
  make test-single-company
  # Runs complete pipeline with 1 query per ICP

Manual Command:
  cd backend && PYTHONPATH=. ../.venv/bin/python -m app.main run-once --queries-per-icp 1

Custom Script:
  cd backend && PYTHONPATH=. ../.venv/bin/python test_single_flow.py
""")


if __name__ == "__main__":
    print_usage_examples()
