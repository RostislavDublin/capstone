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

# Suppress verbose warnings
# google.genai: response parts concatenation warnings (known behavior with tool calls)
# google.adk: app name mismatch warnings (not critical for development)
logging.getLogger("google_genai.types").setLevel(logging.ERROR)
logging.getLogger("google.adk").setLevel(logging.ERROR)
logging.getLogger("google.adk.runners").setLevel(logging.ERROR)

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
    
    # Get actual commit dates from Firestore
    from storage.firestore_client import FirestoreAuditDB
    db = FirestoreAuditDB()
    commits = db.query_by_repository(repository=test_repo, limit=20, descending=False)
    
    if not commits or len(commits) < 15:
        print("ERROR: Not enough commits in test repo. Run reset_fixture.py first.")
        return
    
    # Extract base date from first commit
    base_date = commits[0].date
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  TRENDS AGENT - Realistic Quality Patterns Demo".center(78) + "║")
    print("║" + " "*78 + "║")
    print("║" + "  15 commits with ups & downs (like real life)".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝\n")
    
    print(f"Repository: {test_repo}")
    print(f"Commits: {len(commits)} (realistic evolution with regressions and improvements)")
    print("Data source: Firestore (deterministic)")
    print(f"Base date: {base_date.strftime('%Y-%m-%d')} (first commit)")
    print("Agent: query_trends (pattern detection)\n")
    
    print("Commit timeline:")
    print("  1-5:   Initial dev + security fixes")
    print("  6-7:   REGRESSION (removed validation, unsafe upload)")
    print("  8-9:   RECOVERY (security fixes)")
    print("  10-11: GROWTH (caching, metrics)")
    print("  12-13: IMPROVEMENT (removed eval, added auth)")
    print("  14-15: REGRESSION (rushed admin, disabled logging)\n")
    
    # Create runner (use consistent app_name across all demos)
    runner = InMemoryRunner(agent=trends_agent, app_name="agents")
    
    # Calculate date ranges based on actual commit dates
    # Commits: [0]=init+35d, [1-15]=30d ago + 0-14 days
    from datetime import timedelta
    
    # Use actual commit dates for precise queries
    c1_date = commits[0].date.strftime('%Y-%m-%d')  # Commit 1 (init)
    c5_date = commits[4].date.strftime('%Y-%m-%d')  # Commit 5
    c7_date = commits[6].date.strftime('%Y-%m-%d')  # Commit 7
    c9_date = commits[8].date.strftime('%Y-%m-%d')  # Commit 9
    c13_date = commits[12].date.strftime('%Y-%m-%d')  # Commit 13
    c15_date = commits[14].date.strftime('%Y-%m-%d')  # Commit 15
    last_date = commits[-1].date.strftime('%Y-%m-%d')  # Last commit
    
    queries = [
        {
            "q": f"Show quality trends for {test_repo}",
            "desc": "Full history (all commits)",
        },
        {
            "q": f"Show trends for {test_repo} from {c1_date} to {c5_date}",
            "desc": "Early phase (commits 1-5)",
        },
        {
            "q": f"Show trends for {test_repo} from {c5_date} to {c7_date}",
            "desc": "Middle phase (commits 5-7)",
        },
        {
            "q": f"Show trends for {test_repo} from {c7_date} to {c9_date}",
            "desc": "Phase (commits 7-9)",
        },
        {
            "q": f"Show trends for {test_repo} from {c9_date} to {c13_date}",
            "desc": "Growth phase (commits 9-13)",
        },
        {
            "q": f"Show trends for {test_repo} from {c13_date} to {last_date}",
            "desc": "Final phase (commits 13-15)",
        },
    ]
    
    for i, query_data in enumerate(queries, 1):
        question = query_data["q"]
        desc = query_data["desc"]
        
        print_header(f"Test {i}/{len(queries)}: {desc}")
        
        try:
            # Capture output and filter Event objects
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                await runner.run_debug(question)
            
            # Print only User/Agent dialogue, skip Event lines
            for line in f.getvalue().split('\n'):
                if not line.strip().startswith('[Event(') and not line.strip().startswith(')'):
                    print(line)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
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
