"""E2E Test: Query Agent - Quality Trends Analysis.

Tests the query_agent's ability to analyze quality trends:
- Trend direction (IMPROVING/STABLE/DEGRADING)
- Recent vs historical score comparison
- Specific metrics and calculations
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
async def test_quality_trends_analysis(runner, test_repo):
    """Test: Analyze overall quality direction (improving/stable/degrading).
    
    Expected output:
    - Trend direction (IMPROVING/DECLINING/STABLE)
    - Recent average quality score
    - Historical average quality score
    - Key issues driving the trend
    - Actionable recommendations
    """
    question = f"Show quality trends for {test_repo}"
    
    print(f"\n{'='*80}")
    print(f"TEST: Quality Trends Analysis")
    print(f"{'='*80}\n")
    print(f"Question: {question}\n")
    print("Agent Response:")
    print("-" * 80)
    
    response = await runner.run_debug(question)
    
    print("-" * 80)
    print("\nValidation Points:")
    print("- Did agent call query_trends tool?")
    print("- Does response include trend direction?")
    print("- Does response show recent vs historical scores?")
    print("- Are specific issues mentioned?")
    print("- Are recommendations actionable?")
    
    # Basic validation
    assert response is not None, "Agent should return a response"


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_improvement_check(runner, test_repo):
    """Test: Check if code quality is improving over time.
    
    Expected output:
    - Clear yes/no answer
    - Comparison of recent vs historical quality
    - Evidence from commit data
    """
    question = f"Is code quality improving in {test_repo}?"
    
    print(f"\n{'='*80}")
    print(f"TEST: Improvement Check")
    print(f"{'='*80}\n")
    print(f"Question: {question}\n")
    print("Agent Response:")
    print("-" * 80)
    
    response = await runner.run_debug(question)
    
    print("-" * 80)
    print("\nValidation Points:")
    print("- Is the answer clear (improving/declining)?")
    print("- Does it compare recent vs historical data?")
    print("- Is evidence provided from commits?")
    
    assert response is not None


if __name__ == "__main__":
    # Run tests individually for debugging
    pytest.main([__file__, "-v", "-s"])
