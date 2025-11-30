"""E2E Test: Query Agent - Issue Patterns Analysis.

Tests the query_agent's ability to identify recurring problems:
- Most common security issues
- Most common complexity problems
- Issue type distribution
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
async def test_common_issues_analysis(runner, test_repo):
    """Test: Identify most common issues in repository.
    
    Expected output:
    - List of recurring security issues
    - List of recurring complexity issues
    - Issue type frequencies
    - Specific files/commits affected
    - Recommendations to address patterns
    """
    question = f"What are the most common issues in {test_repo}?"
    
    print(f"\n{'='*80}")
    print(f"TEST: Common Issues Analysis")
    print(f"{'='*80}\n")
    print(f"Question: {question}\n")
    print("Agent Response:")
    print("-" * 80)
    
    response = await runner.run_debug(question)
    
    print("-" * 80)
    print("\nValidation Points:")
    print("- Are security issues identified?")
    print("- Are complexity issues identified?")
    print("- Are specific files mentioned?")
    print("- Are issue types categorized?")
    print("- Are recommendations provided?")
    
    assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
