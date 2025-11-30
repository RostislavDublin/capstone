"""Demo: Advanced filtering in query_trends.

Tests new filtering capabilities:
- File-specific trends
- Author-specific trends  
- Quality/security thresholds
- Combined filters

Assumes Firestore+RAG already populated (run demo_quality_guardian_agent.py first).
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

# Setup logging BEFORE imports to suppress warnings
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s"
)

# Suppress verbose warnings (must be set before importing agents)
# google.genai: response parts concatenation warnings (known behavior with tool calls)
# google.adk: app name mismatch warnings (not critical for development)
logging.getLogger("google_genai.types").setLevel(logging.ERROR)
logging.getLogger("google.adk").setLevel(logging.ERROR)
logging.getLogger("google.adk.runners").setLevel(logging.ERROR)

# Now import agents
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


async def demo_filtering():
    """Demo: Test advanced filtering capabilities."""
    
    test_repo = get_test_repo_name()
    
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  TRENDS AGENT - Advanced Filtering Demo".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝\n")
    
    print(f"Repository: {test_repo}")
    print("Testing: File filters, author filters, quality thresholds\n")
    
    # Create runner (use consistent app_name across all demos)
    runner = InMemoryRunner(agent=trends_agent, app_name="quality_guardian")
    
    # Test scenarios
    scenarios = [
        {
            "title": "File-specific trends: app/main.py",
            "query": f"Show quality trends for app/main.py file in {test_repo}",
            "description": "Filter commits that touched app/main.py"
        },
        {
            "title": "Author-specific trends: Junior Dev",
            "query": f"Show quality trends for commits by Junior Dev in {test_repo}",
            "description": "Filter commits by specific author"
        },
        {
            "title": "Same file again (verification)",
            "query": f"Show quality trends for app/main.py in {test_repo}",
            "description": "Verify consistent results for same file"
        },
        {
            "title": "Quality threshold: Only good commits",
            "query": f"Show quality trends for commits with quality score above 80 in {test_repo}",
            "description": "Filter by minimum quality score"
        },
        {
            "title": "Security focus: High security scores only",
            "query": f"Show security trends for commits with security score above 85 in {test_repo}",
            "description": "Filter by minimum security score"
        },
        {
            "title": "Combined: app/main.py by Junior Dev with good quality",
            "query": f"Show trends for app/main.py commits by Junior Dev with quality above 75 in {test_repo}",
            "description": "Multiple filters combined"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print_header(f"Scenario {i}: {scenario['title']}")
        print(f"Description: {scenario['description']}")
        print(f"Query: {scenario['query']}\n")
        
        try:
            # Capture output and filter Event objects
            import io
            import contextlib
            
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                await runner.run_debug(scenario["query"])
            
            # Print only User/Agent dialogue, skip Event lines
            for line in f.getvalue().split('\n'):
                if not line.strip().startswith('[Event(') and not line.strip().startswith(')'):
                    print(line)
        except Exception as e:
            print(f"ERROR: {e}")
        
        if i < len(scenarios):
            print("\n" + "-"*80 + "\n")
    
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + "  Demo completed - Advanced filtering working!".center(78) + "║")
    print("╚" + "="*78 + "╝\n")


if __name__ == "__main__":
    asyncio.run(demo_filtering())
