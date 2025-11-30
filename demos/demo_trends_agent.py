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
    """Quick demo: Test trends_agent with 15 commits showing realistic patterns."""
    
    test_repo = get_test_repo_name()
    
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  TRENDS AGENT - Realistic Quality Patterns Demo".center(78) + "║")
    print("║" + " "*78 + "║")
    print("║" + "  15 commits with ups & downs (like real life)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝\n")
    
    print(f"Repository: {test_repo}")
    print("Commits: 15 (realistic evolution with regressions and improvements)")
    print("Data source: Firestore (deterministic)")
    print("Agent: query_trends (pattern detection)\n")
    
    print("Commit timeline:")
    print("  1-5:   Initial dev + security fixes")
    print("  6-7:   REGRESSION (removed validation, unsafe upload)")
    print("  8-9:   RECOVERY (security fixes)")
    print("  10-11: GROWTH (caching, metrics)")
    print("  12-13: IMPROVEMENT (removed eval, added auth)")
    print("  14-15: REGRESSION (rushed admin, disabled logging)\n")
    
    # Create runner
    runner = InMemoryRunner(agent=trends_agent, app_name="trends_agent_dev")
    
    # Test queries designed to show different patterns
    # Dates based on: initial commit 35 days ago, then commits every day starting 30 days ago
    queries = [
        {
            "q": f"Show quality trends for {test_repo}",
            "desc": "Full history - expect VOLATILE pattern",
            "pattern": "VOLATILE (ups and downs throughout)"
        },
        {
            "q": f"Show trends for {test_repo} from October 31 to November 4",
            "desc": "Early phase (commits 1-5) - expect LINEAR improvement",
            "pattern": "LINEAR (initial development)"
        },
        {
            "q": f"Show trends for {test_repo} from November 4 to November 6",
            "desc": "Regression phase (commits 5-7) - expect SPIKE_DOWN",
            "pattern": "SPIKE_DOWN (validation removed)"
        },
        {
            "q": f"Show trends for {test_repo} from November 6 to November 8",
            "desc": "Recovery phase (commits 7-9) - expect SPIKE_UP",
            "pattern": "SPIKE_UP (security fixes)"
        },
        {
            "q": f"Show trends for {test_repo} from November 8 to November 12",
            "desc": "Growth phase (commits 9-13) - expect ACCELERATING",
            "pattern": "ACCELERATING (features + auth)"
        },
        {
            "q": f"Show trends for {test_repo} from November 12 to November 14",
            "desc": "Final regression (commits 13-15) - expect SPIKE_DOWN",
            "pattern": "SPIKE_DOWN (rushed features)"
        },
    ]
    
    for i, query_data in enumerate(queries, 1):
        question = query_data["q"]
        desc = query_data["desc"]
        expected_pattern = query_data["pattern"]
        
        print_header(f"Test {i}/{len(queries)}: {desc}")
        print(f"Expected pattern: {expected_pattern}\n")
        
        try:
            # run_debug() prints agent response automatically, returns complex object with parts
            # We don't need to capture or print the response - just let ADK handle it
            await runner.run_debug(question)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print_header("Summary")
    print(f"Tests completed: {len(queries)}")
    print("\nPattern demonstration:")
    print("  ✓ VOLATILE - full history with ups and downs")
    print("  ✓ LINEAR - steady improvement in early phase")
    print("  ✓ SPIKE_DOWN - regressions at commits 5-7 and 13-15")
    print("  ✓ SPIKE_UP - recovery at commits 7-9")
    print("  ✓ ACCELERATING - growth phase at commits 9-13")
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
