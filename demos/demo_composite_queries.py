"""Demo: Composite Queries with Query Orchestrator.

Shows the "cherry on top" feature: orchestrator combines multiple agents
(trends + root cause) to answer complex questions in one unified response.
"""
import sys
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
import asyncio

# Initialize Vertex AI (using env vars)
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("VERTEX_LOCATION", "us-west1")
)

# Import ADK runner, agent, and test repo helper
from google.adk.runners import InMemoryRunner
from agents.query_orchestrator.agent import root_agent as orchestrator
from fixtures.test_repo_fixture import get_test_repo_name

# Get configured test repo
REPO = get_test_repo_name()

# Create runner
runner = InMemoryRunner(agent=orchestrator, app_name="agents")

print("╔" + "="*78 + "╗")
print("║" + " "*78 + "║")
print("║" + " "*15 + "COMPOSITE QUERIES - Orchestrator Demo" + " "*24 + "║")
print("║" + " "*78 + "║")
print("╚" + "="*78 + "╝")
print()
print(f"Repository: {REPO}")
print("Feature: Query Orchestrator combines trends + root cause analysis")
print()

# Scenario: COMPOSITE query (orchestrator calls multiple agents)
print("="*80)
print("  COMPOSITE QUERY - Trends AND Root Cause Analysis")
print("="*80)
print()
print("Description: Orchestrator intelligently routes to BOTH agents")
print("Query: Show trends and explain root causes")
print()
print()

query = f"""
Show me the quality trends for {REPO} 
and explain what caused any quality degradation. 
I want to see both the trend analysis and the root causes.
"""

print(f"User > {query.strip()}")
print()

async def run_composite_query():
    # Run debug mode with full output to see what's happening
    await runner.run_debug(query)

asyncio.run(run_composite_query())
print()

print("="*80)
print(" Demo completed - Composite queries working!")
print(" Orchestrator intelligently combined trends + root cause analysis")
print("="*80)
