"""E2E Test: Query Agent - Specific Metrics.

Tests the query_agent's ability to provide specific numeric metrics:
- Total issue counts
- Critical/high/medium/low breakdown
- Average quality scores
- Security vs complexity distribution
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
async def test_critical_issues_count(runner, test_repo):
    """Test: Get specific counts of critical issues.
    
    Expected output:
    - Total critical issue count
    - Specific critical issues identified
    - Locations of critical issues
    - Severity breakdown
    """
    question = f"How many critical issues are in {test_repo}?"
    
    print(f"\n{'='*80}")
    print(f"TEST: Critical Issues Count")
    print(f"{'='*80}\n")
    print(f"Question: {question}\n")
    print("Agent Response:")
    print("-" * 80)
    
    response = await runner.run_debug(question)
    
    print("-" * 80)
    print("\nValidation Points:")
    print("- Is a specific number provided?")
    print("- Are critical issues identified by type?")
    print("- Are locations (files) specified?")
    print("- Is severity level clear?")
    
    assert response is not None


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_issue_severity_breakdown(runner, test_repo):
    """Test: Get breakdown of all issue severities.
    
    Expected output:
    - Critical count
    - High count
    - Medium count
    - Low count
    - Total issues
    - Security vs complexity distribution
    """
    question = f"Give me a breakdown of all issues by severity in {test_repo}"
    
    print(f"\n{'='*80}")
    print(f"TEST: Issue Severity Breakdown")
    print(f"{'='*80}\n")
    print(f"Question: {question}\n")
    print("Agent Response:")
    print("-" * 80)
    
    response = await runner.run_debug(question)
    
    print("-" * 80)
    print("\nValidation Points:")
    print("- Are all severity levels shown?")
    print("- Are counts specific?")
    print("- Is there a total?")
    print("- Is security vs complexity broken down?")
    
    assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
