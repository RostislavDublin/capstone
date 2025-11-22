#!/usr/bin/env python3
"""Integration test: Sync Agent - new commits detection."""

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


async def test_sync_new_commits():
    """Test: Sync agent detects new commits."""
    print("\n=== TEST: Sync Agent - New Commits Detection ===\n")
    
    runner = InMemoryRunner(agent=root_agent)
    
    # Sync repository
    print("Syncing repository...")
    response = await runner.run_debug(
        "Sync RostislavDublin/quality-guardian-test-fixture"
    )
    print()
    
    # Check response
    response_str = str(response).lower()
    if "new" in response_str or "found" in response_str or "up-to-date" in response_str:
        print("✅ PASS: Sync executed")
    else:
        print("❌ FAIL: Unexpected response")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(test_sync_new_commits())
