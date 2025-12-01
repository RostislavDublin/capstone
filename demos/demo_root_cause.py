"""Demo: Root Cause Analysis using RAG Semantic Search.

This demonstrates the killer feature: RAG-powered root cause analysis.
Shows WHY quality degraded by finding patterns in commit history.
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

# Initialize Vertex AI (using env vars)
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("VERTEX_LOCATION", "us-west1")
)

# Import agent and test repo helper
from agents.query_root_cause.agent import root_agent
from fixtures.test_repo_fixture import get_test_repo_name

# Get configured test repo
REPO = get_test_repo_name()

# Create runner
runner = InMemoryRunner(agent=root_agent, app_name="agents")

print("╔" + "="*78 + "╗")
print("║" + " "*78 + "║")
print("║" + " "*20 + "ROOT CAUSE ANALYSIS - RAG Demo" + " "*27 + "║")
print("║" + " "*78 + "║")
print("╚" + "="*78 + "╝")
print()
print(f"Repository: {REPO}")
print("Feature: RAG semantic search finds WHY quality degraded")
print()

# Scenario 1: Why did quality drop?
print("="*80)
print("  Scenario 1: Why did quality drop in last 2 weeks?")
print("="*80)
print()
print("Description: Use RAG semantic search to find problematic commits")
print(f"Query: Why did quality drop in {REPO}")
print("       in the last 2 weeks?")
print()
print()

query1 = f"""
Why did code quality drop in {REPO} 
in the last 2 weeks? Find the root causes.
"""

print(f"User > {query1.strip()}")
print()

async def run_query1():
    # Capture output and filter Event objects (keep only agent dialogue)
    import io
    import contextlib
    
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        await runner.run_debug(query1)
    
    # Print only User/Agent dialogue, skip Event lines and raw tool outputs
    for line in f.getvalue().split('\n'):
        if not line.strip().startswith('[Event(') and not line.strip().startswith(')'):
            print(line)

asyncio.run(run_query1())
print()

print("="*80)
print(" Demo completed - Root Cause Agent with RAG semantic search working!")
print("="*80)
