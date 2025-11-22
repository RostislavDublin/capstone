#!/usr/bin/env python3
"""Integration test: Bootstrap Agent - parameter extraction."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv(Path(__file__).parent.parent.parent / ".env.dev")

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from agent import root_agent
from google.adk.runners import InMemoryRunner


async def test_bootstrap_with_count():
    """Test: Bootstrap respects user's count parameter."""
    print("\n=== TEST: Bootstrap Agent - Count Parameter ===\n")
    
    runner = InMemoryRunner(agent=root_agent)
    
    # Test 1: Explicit count=5
    print("Test 1: Bootstrap with 5 commits")
    response = await runner.run_debug(
        "Bootstrap RostislavDublin/quality-guardian-test-fixture with 5 commits"
    )
    print()
    
    # Check if response mentions correct count
    if "5" in str(response) or "five" in str(response).lower():
        print("✅ PASS: Correct count detected")
    else:
        print("❌ FAIL: Wrong count")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_bootstrap_with_count())
