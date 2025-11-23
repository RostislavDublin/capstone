"""Sync Agent - Check for new commits."""
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
from tools.repository_tools import check_new_commits

logger = logging.getLogger(__name__)

# Retry config
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

root_agent = LlmAgent(
    name="sync_agent",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="Checks for new commits since last analysis",
    instruction="""
    You check repositories for new commits that need analysis.
    
    Use check_new_commits tool to find and analyze commits since last audit.
    Report how many new commits found and their quality metrics.
    If repository is up-to-date, say so clearly.
    """,
    tools=[check_new_commits]
)

logger.debug("Sync agent initialized")
