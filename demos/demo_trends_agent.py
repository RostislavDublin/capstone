"""Quick demo: Trends Agent - Fast iteration during development.

Assumes Firestore+RAG already populated (run main demo once first).
Tests only the trends_agent functionality in isolation.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s"
)

# Suppress google.genai verbose warnings about response parts concatenation
# This is a known behavior when agents make tool calls (function_call + text parts)
# Following the pattern from main demo and e2e tests
logging.getLogger("google_genai.types").setLevel(logging.ERROR)

from agents.query_trends.agent import root_agent as trends_agent
from google.adk.runners import InMemoryRunner

# Get test repo name
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
from fixtures.test_repo_fixture import get_test_repo_name


def print_header(title: str):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


async def demo_trends_agent():
    """Quick demo: Test trends_agent in isolation."""
    
    test_repo = get_test_repo_name()
    
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  TRENDS AGENT - Quick Development Test".center(78) + "║")
    print("║" + " "*78 + "║")
    print("║" + "  Assumes data already in Firestore (run main demo once)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝\n")
    
    print(f"Repository: {test_repo}")
    print("Data source: Firestore (deterministic)")
    print("Agent: query_trends (specialist)\n")
    
    # Create runner
    runner = InMemoryRunner(agent=trends_agent, app_name="trends_agent_dev")
    
    # Test queries - all date range scenarios
    queries = [
        {
            "q": f"Show quality trends for {test_repo}",
            "desc": "Full history (beginning to end)"
        },
        {
            "q": f"Show trends for {test_repo} since November 1, 2025",
            "desc": "From date to end (start_date to now)"
        },
        {
            "q": f"Show trends for {test_repo} until October 31, 2025",
            "desc": "Beginning to date (start to end_date)"
        },
        {
            "q": f"Show trends for {test_repo} from October 30 to November 1, 2025",
            "desc": "Date range (start_date to end_date)"
        },
    ]
    
    for i, query_data in enumerate(queries, 1):
        question = query_data["q"]
        desc = query_data["desc"]
        
        print_header(f"Test {i}/{len(queries)}: {desc}")
        print(f"Question: {question}\n")
        print("Agent response:")
        print("-" * 80)
        
        try:
            # run_debug() prints agent response automatically, returns complex object with parts
            # We don't need to capture or print the response - just let ADK handle it
            await runner.run_debug(question)
            print("-" * 80)
            print("\n✓ Agent completed successfully")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print_header("Summary")
    print(f"Tests completed: {len(queries)}")
    print()


def main():
    """Run quick demo."""
    try:
        asyncio.run(demo_trends_agent())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
