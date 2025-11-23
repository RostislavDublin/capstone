"""Demo: Query Agent - Rich Analytics Showcase.

This demo shows the enhanced query_agent capabilities:
- Quality trends analysis (improving/degrading)
- Issue pattern detection (most common problems)
- Author statistics (who writes quality code)
- Problematic files identification (hotspots)
- Specific metrics and actionable recommendations

Uses existing RAG data - no need to run bootstrap/sync first.
"""

import asyncio
import logging
import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Suppress warnings
warnings.filterwarnings("ignore", message=".*Unclosed.*", category=ResourceWarning)

# Load environment
env_file = Path(__file__).parent.parent / ".env.dev"
if env_file.exists():
    load_dotenv(env_file)

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from agents.query.agent import root_agent
from google.adk.runners import InMemoryRunner

# Setup logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("google_adk").setLevel(logging.CRITICAL)
logging.getLogger("google.adk").setLevel(logging.CRITICAL)
logging.getLogger("google_genai").setLevel(logging.CRITICAL)


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_divider():
    """Print divider."""
    print("\n" + "-" * 80 + "\n")


async def demo_query_capabilities():
    """Demo: Enhanced query_agent with rich analytics."""
    
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  QUERY AGENT - Rich Analytics Showcase".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Using existing RAG data (no bootstrap needed)".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝\n")
    
    # Get test repo name
    sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
    from fixtures.test_repo_fixture import get_test_repo_name
    test_repo = get_test_repo_name()
    
    print(f"Using repository: {test_repo}")
    print("RAG corpus: quality-guardian-audits")
    
    # Create runner
    runner = InMemoryRunner(agent=root_agent)
    
    # Define test queries showcasing different capabilities
    queries = [
        {
            "category": "QUALITY TRENDS",
            "question": f"Show quality trends for {test_repo}",
            "description": "Analyze overall quality direction (improving/stable/degrading)"
        },
        {
            "category": "ISSUE PATTERNS",
            "question": f"What are the most common issues in {test_repo}?",
            "description": "Identify recurring problems (security, complexity patterns)"
        },
        {
            "category": "AUTHOR ANALYSIS",
            "question": f"Who writes the best code in {test_repo}?",
            "description": "Compare authors by quality scores and issue counts"
        },
        {
            "category": "PROBLEMATIC FILES",
            "question": f"Which files need refactoring in {test_repo}?",
            "description": "Find hotspot files with most issues (refactoring candidates)"
        },
        {
            "category": "SPECIFIC METRICS",
            "question": f"How many critical issues are in {test_repo}?",
            "description": "Get specific counts (critical/high/medium/low breakdown)"
        },
        {
            "category": "IMPROVEMENT CHECK",
            "question": f"Is code quality improving in {test_repo}?",
            "description": "Compare recent vs historical quality scores"
        },
    ]
    
    # Run queries
    for i, query in enumerate(queries, 1):
        print_header(f"Query {i}/{len(queries)}: {query['category']}")
        
        print(f"Description: {query['description']}\n")
        print(f"Question: \"{query['question']}\"\n")
        print("Agent response:\n")
        
        try:
            await runner.run_debug(query['question'])
            print_divider()
            
        except Exception as e:
            print(f"ERROR: {e}\n")
            print_divider()
    
    # Summary
    print_header("SUMMARY: Query Agent Capabilities")
    
    print("The enhanced query_agent now provides:\n")
    print("1. QUALITY TRENDS")
    print("   - Trend direction (IMPROVING/STABLE/DEGRADING)")
    print("   - Recent vs historical score comparison")
    print("   - Commits analyzed count\n")
    
    print("2. ISSUE PATTERNS")
    print("   - Most common security issues")
    print("   - Most common complexity problems")
    print("   - Issue type distribution\n")
    
    print("3. AUTHOR ANALYSIS")
    print("   - Best authors (highest quality scores)")
    print("   - Authors needing help (lowest scores)")
    print("   - Commit volume vs quality correlation\n")
    
    print("4. PROBLEMATIC FILES")
    print("   - Files with most issues (hotspots)")
    print("   - Refactoring candidates")
    print("   - Security/complexity breakdowns per file\n")
    
    print("5. SPECIFIC METRICS")
    print("   - Total/critical/high/medium/low issue counts")
    print("   - Average quality scores")
    print("   - Security vs complexity breakdown\n")
    
    print("6. ACTIONABLE RECOMMENDATIONS")
    print("   - What to fix first")
    print("   - Which files to refactor")
    print("   - Which patterns to address\n")
    
    print("=" * 80)
    print("\nAll answers are backed by:")
    print("  - Structured analytics (from RAGCorpusManager)")
    print("  - AI insights (from Gemini with RAG grounding)")
    print("  - Specific numbers and evidence")
    print("=" * 80 + "\n")


def main():
    """Run demo."""
    try:
        asyncio.run(demo_query_capabilities())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye!")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
