"""Demo: Quality Guardian (Root Agent) - Full Hierarchy Test.

Tests the complete 4-level hierarchy:
  Quality Guardian → Query Orchestrator → trends_agent/root_cause_agent → tools

Uses the same 3 test scenarios as demo_orchestrator.py to verify
responses are not distorted when passing through the full hierarchy.
"""
import sys
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

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
from google.adk.runners import InMemoryRunner

# Initialize Vertex AI
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("VERTEX_LOCATION", "us-west1")
)

# Import ROOT agent (Quality Guardian) and test repo helper
from agents.quality_guardian.agent import root_agent
from fixtures.test_repo_fixture import get_test_repo_name

# Get configured test repo
REPO = get_test_repo_name()

# Create runner
runner = InMemoryRunner(agent=root_agent, app_name="agents")

print("╔" + "="*78 + "╗")
print("║" + " "*78 + "║")
print("║" + " "*15 + "QUALITY GUARDIAN - Full Hierarchy Test" + " "*24 + "║")
print("║" + " "*78 + "║")
print("╚" + "="*78 + "╝")
print()
print(f"Repository: {REPO}")
print("Testing 4-level hierarchy: Guardian → Orchestrator → Sub-agents → Tools")
print()


async def test_trends_only():
    """Test 1: Simple trends query - should route through orchestrator to trends_agent."""
    print("="*80)
    print("  TEST 1: Trends Query (full hierarchy)")
    print("="*80)
    print()
    print("Expected: Guardian → Orchestrator → trends_agent")
    print("Response should match demo_orchestrator.py TEST 1")
    print()
    
    query = f"Show quality trends for {REPO}"
    print(f"User > {query}")
    print()
    
    await runner.run_debug(query)
    print()


async def test_root_cause_only():
    """Test 2: Simple root cause query - should route through orchestrator to root_cause_agent."""
    print("="*80)
    print("  TEST 2: Root Cause Query (full hierarchy)")
    print("="*80)
    print()
    print("Expected: Guardian → Orchestrator → root_cause_agent")
    print("Response should match demo_orchestrator.py TEST 2")
    print()
    
    # Use EXACT same query as demo_orchestrator.py and demo_root_cause.py
    query = f"""Why did code quality drop in {REPO} 
in the last 2 weeks? Find the root causes."""
    print(f"User > {query.strip()}")
    print()
    
    await runner.run_debug(query)
    print()


async def test_composite():
    """Test 3: Composite query - should route through orchestrator to BOTH agents."""
    print("="*80)
    print("  TEST 3: Composite Query (full hierarchy)")
    print("="*80)
    print()
    print("Expected: Guardian → Orchestrator → BOTH agents")
    print("Response should match demo_orchestrator.py TEST 3")
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
    print("   ✓ Test 1: Response matches demo_orchestrator.py TEST 1?")
    print("   ✓ Test 2: Response matches demo_orchestrator.py TEST 2?")
    print("   ✓ Test 3: Response matches demo_orchestrator.py TEST 3?")
    print("   ✓ No information loss through 4-level hierarchy?")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
