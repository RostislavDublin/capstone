"""Bootstrap Agent - Initial repository analysis."""
import logging
import sys
from pathlib import Path

# Add parent directories to path
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from tools.repository_tools import analyze_repository

logger = logging.getLogger(__name__)

# Retry config
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

root_agent = LlmAgent(
    name="bootstrap_agent",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="Analyzes repositories for the first time by scanning recent commits",
    instruction="""
    You analyze GitHub repositories for code quality.
    
    CRITICAL REQUIREMENT
    The analyze_repository tool requires TWO parameters:
    1. repo (string) - the repository name
    2. count (integer) - number of commits to analyze
    
    YOU MUST EXTRACT THE NUMBER from user's text:
    - "Bootstrap repo with 3 commits" → count=3
    - "Analyze 5 commits from repo" → count=5  
    - "Bootstrap repo with 15 commits" → count=15
    - If NO number mentioned → count=10 (default)
    
    WRONG: analyze_repository(repo="owner/repo")  # Missing count!
    RIGHT: analyze_repository(repo="owner/repo", count=5)
    
    Extract repo name (owner/repo format) and commit count, then call the tool.
    Report results clearly: commits analyzed, quality score, issues found.
    """,
    tools=[analyze_repository]
)

logger.debug("Bootstrap agent initialized")
