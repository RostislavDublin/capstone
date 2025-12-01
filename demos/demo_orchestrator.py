"""Demo: Query Orchestrator - Progressive Testing.

Tests orchestrator routing in three stages:
1. Simple trends query (should route to trends_agent only)
2. Simple root cause query (should route to root_cause_agent only)
3. Composite query (should route to BOTH agents and merge)

Goal: Verify orchestrator correctly delegates and returns unmodified responses.
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio

# Load .env FIRST
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add src and tests to path
src_path = Path(__file__).parent.parent / "src"
tests_path = Path(__file__).parent.parent / "tests"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(tests_path))

import vertexai

# Initialize Vertex AI (using env vars)
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("VERTEX_LOCATION", "us-west1")
)

# Import ADK runner, orchestrator, and test repo helper
from google.adk.runners import InMemoryRunner
from agents.query_orchestrator.agent import root_agent as orchestrator
from fixtures.test_repo_fixture import get_test_repo_name

# Get configured test repo
REPO = get_test_repo_name()

# Create runner
runner = InMemoryRunner(agent=orchestrator, app_name="agents")

print("╔" + "="*78 + "╗")
print("║" + " "*78 + "║")
print("║" + " "*18 + "QUERY ORCHESTRATOR - Progressive Testing" + " "*19 + "║")
print("║" + " "*78 + "║")
print("╚" + "="*78 + "╝")
print()
print(f"Repository: {REPO}")
print("Testing orchestrator routing and response integrity")
print()


async def test_trends_only():
    """Test 1: Simple trends query - should route to trends_agent."""
    print("="*80)
    print("  TEST 1: Trends Query (should route to trends_agent only)")
    print("="*80)
    print()
    print("Expected: Orchestrator calls trends_agent and returns its response as-is")
    print("Response should include: trend direction, scores, commit analysis")
    print()
    
    query = f"Show quality trends for {REPO}"
    print(f"User > {query}")
    print()
    
    await runner.run_debug(query)
    print()


async def test_root_cause_only():
    """Test 2: Simple root cause query - should route to root_cause_agent."""
    print("="*80)
    print("  TEST 2: Root Cause Query (should route to root_cause_agent only)")
    print("="*80)
    print()
    print("Expected: Orchestrator calls root_cause_agent and returns its response as-is")
    print("Response should include: primary root cause, file hotspots, recommendations")
    print()
    
    # Use EXACT same query as demo_root_cause.py for comparison
    query = f"""Why did code quality drop in {REPO} 
in the last 2 weeks? Find the root causes."""
    print(f"User > {query.strip()}")
    print()
    
    await runner.run_debug(query)
    print()


async def test_composite():
    """Test 3: Composite query - should route to BOTH agents."""
    print("="*80)
    print("  TEST 3: Composite Query (should route to BOTH agents)")
    print("="*80)
    print()
    print("Expected: Orchestrator calls BOTH agents and merges responses")
    print("Response should include: trends analysis + root cause analysis")
    print()
    
    query = f"""Show me the quality trends for {REPO} 
and explain what caused any quality degradation. 
I want to see both the trend analysis and the root causes."""
    
    print(f"User > {query.strip()}")
    print()
    
    await runner.run_debug(query)
    print()


async def main():
    """Run all three tests sequentially."""
    
    # Test 1: Trends only
    await test_trends_only()
    
    print("\n" + "─"*80 + "\n")
    
    # Test 2: Root cause only
    await test_root_cause_only()
    
    print("\n" + "─"*80 + "\n")
    
    # Test 3: Composite (both)
    await test_composite()
    
    print("="*80)
    print(" All tests completed!")
    print()
    print(" Verification checklist:")
    print("   ✓ Test 1: Trends response matches demo_trends_agent.py output?")
    print("   ✓ Test 2: Root cause response matches demo_root_cause.py output?")
    print("   ✓ Test 3: Composite response contains BOTH analyses?")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
