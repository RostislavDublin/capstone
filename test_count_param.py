#!/usr/bin/env python3
"""Quick test: Does bootstrap agent respect count parameter?"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env.dev
env_file = Path(__file__).parent / ".env.dev"
if env_file.exists():
    load_dotenv(env_file)

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import root_agent
from google.adk.runners import InMemoryRunner

async def test():
    runner = InMemoryRunner(agent=root_agent)
    
    print("=" * 60)
    print("TEST: Bootstrap with 3 commits")
    print("=" * 60)
    
    # Try different phrasings
    commands = [
        'Analyze 3 commits from RostislavDublin/quality-guardian-test-fixture',
        'Bootstrap RostislavDublin/quality-guardian-test-fixture, analyze 3 commits',
        'For RostislavDublin/quality-guardian-test-fixture: analyze exactly 3 commits'
    ]
    
    response = await runner.run_debug(commands[0])
    
    # Extract relevant info from response
    response_str = str(response)
    if "analyzed 3 commits" in response_str.lower():
        print("\n✅ SUCCESS: Agent analyzed exactly 3 commits!")
    elif "analyzed 10 commits" in response_str.lower():
        print("\n❌ FAIL: Agent analyzed 10 commits (ignored count parameter)")
    else:
        print(f"\n⚠️  Response: {response_str[:200]}...")

if __name__ == "__main__":
    asyncio.run(test())
