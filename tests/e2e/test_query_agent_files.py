"""E2E Test: Query Agent - Problematic Files Analysis.

Tests the query_agent's ability to identify files needing refactoring:
- Files with most issues (hotspots)
- Security vs complexity breakdown per file
- Refactoring priority ranking
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
async def test_problematic_files_identification(runner, test_repo):
    """Test: Find hotspot files with most issues (refactoring candidates).
    
    Expected output:
    - List of files with most issues
    - Issue counts per file
    - Types of issues per file (security/complexity)
    - Refactoring priority recommendations
    """
    question = f"Which files need refactoring in {test_repo}?"
    
    print(f"\n{'='*80}")
    print(f"TEST: Problematic Files Identification")
    print(f"{'='*80}\n")
    print(f"Question: {question}\n")
    print("Agent Response:")
    print("-" * 80)
    
    response = await runner.run_debug(question)
    
    print("-" * 80)
    print("\nValidation Points:")
    print("- Are specific file paths listed?")
    print("- Are issue counts per file shown?")
    print("- Are issue types categorized (security/complexity)?")
    print("- Is refactoring priority indicated?")
    print("- Are specific recommendations provided per file?")
    
    assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
