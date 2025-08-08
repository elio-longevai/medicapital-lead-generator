#!/usr/bin/env python3
"""
Test single company flow - runs complete pipeline with just 1 query.
Usage: cd backend && PYTHONPATH=. ../.venv/bin/python test_single_flow.py
"""

import asyncio
import logging

from app.main import _arun_single_icp_workflow, load_icp_text

logging.basicConfig(level=logging.INFO, format="%(message)s")

TEST_ICP = """
## Test ICP: Healthcare Equipment Leasers
**Target:** Small healthcare facilities in Netherlands needing medical equipment.
**Size:** 5-50 employees
**Need:** Equipment financing for diagnostic tools, treatment devices
**Contact:** Practice Manager, Owner, Finance Manager
"""


async def test_custom_icp():
    """Test with simple custom ICP."""
    await _arun_single_icp_workflow(
        icp_name="test_healthcare_single",
        raw_icp_text=TEST_ICP,
        country_code="NL",
        queries_per_icp=1,
    )


async def test_real_icp():
    """Test with real ICP file if available."""
    try:
        icp_text = load_icp_text("icp_healthcare_end_user.txt")
        await _arun_single_icp_workflow(
            icp_name="healthcare_single_test",
            raw_icp_text=icp_text,
            country_code="NL",
            queries_per_icp=1,
        )
    except FileNotFoundError:
        print("⚠️  Real ICP file not found, skipping")


async def main():
    print("🎯 Testing complete workflow with 1 query per ICP...")
    await test_custom_icp()
    print("\n⭐ Custom ICP test complete!")

    await test_real_icp()
    print("\n✅ All tests complete! Check database: make list-leads")


if __name__ == "__main__":
    asyncio.run(main())
