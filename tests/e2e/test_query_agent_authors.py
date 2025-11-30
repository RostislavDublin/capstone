"""E2E Test: Query Agent - Author Analysis.

Tests the query_agent's ability to analyze code quality by author:
- Best authors (highest quality scores)
- Authors needing help (lowest scores)
- Author-specific patterns
"""
import pytest
import asyncio
import logging
from pathlib import Path
import sys

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from agents.query.agent import root_agent
from google.adk.runners import InMemoryRunner

# Setup logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("google_genai.types").setLevel(logging.ERROR)
logging.getLogger("stevedore.extension").setLevel(logging.ERROR)


@pytest.fixture
def test_repo():
    """Get test repository name."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
    from test_repo_fixture import get_test_repo_name
    return get_test_repo_name()


@pytest.fixture
def runner():
    """Create query agent runner."""
    return InMemoryRunner(agent=root_agent, app_name="quality_guardian")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_author_quality_comparison(runner, test_repo):
    """Test: Compare authors by quality scores and issue counts.
    
    Expected output:
    - Best authors (by quality score)
    - Authors with most issues
    - Author-specific patterns
    - Commit volume vs quality correlation
    """
    question = f"Who writes the best code in {test_repo}?"
    
    print(f"\n{'='*80}")
    print(f"TEST: Author Quality Comparison")
    print(f"{'='*80}\n")
    print(f"Question: {question}\n")
    print("Agent Response:")
    print("-" * 80)
    
    response = await runner.run_debug(question)
    
    print("-" * 80)
    print("\nValidation Points:")
    print("- Are authors identified by name?")
    print("- Are quality scores compared?")
    print("- Are specific commits cited?")
    print("- Is there actionable insight (mentoring, review)?")
    
    assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
