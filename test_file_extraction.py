"""Test trends agent file path extraction."""
import os
import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "src"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(Path(__file__).parent / "service-account-key.json")

from google.genai.adk import InMemoryRunner
from agents.query_trends.agent import root_agent

# Initialize runner
runner = InMemoryRunner(root_agent, app_name="agents")

# Test query from Scenario 1 (FAILED in demo)
query = "Show quality trends for app/main.py file in RostislavDublin/quality-guardian-test-fixture"

print("=" * 80)
print(f"Query: {query}")
print("=" * 80)

# Run query
session = runner.create_session()
result = session.send_message(query)

print("\nAgent Response:")
print(result.text)

# Check if response mentions file name
if "app/main.py" in result.text:
    print("\n✅ GOOD: Response mentions file name")
else:
    print("\n❌ BAD: Response doesn't mention file name (treats as repository query)")

# Check if response says "No data"
if "No" in result.text and ("data" in result.text or "commits" in result.text):
    print("❌ BAD: Still returning no data (file path extraction issue)")
else:
    print("✅ GOOD: Found data for file")
