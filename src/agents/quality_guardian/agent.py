"""Root Agent - Quality Guardian Orchestrator.

Coordinates specialized sub-agents via LLM-Driven Delegation (transfer_to_agent).
Implements Coordinator/Dispatcher pattern from ADK documentation.
"""
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

# Import sub-agents from sibling directories
from agents.bootstrap.agent import root_agent as bootstrap_agent
from agents.sync.agent import root_agent as sync_agent
from agents.query_orchestrator.agent import root_agent as query_agent

logger = logging.getLogger(__name__)

# Retry config
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

root_agent = LlmAgent(
    name="quality_guardian",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="AI agent that monitors code quality trends across GitHub repositories",
    instruction="""
    You are Quality Guardian, a coordinator for code quality monitoring.
    
    You have three specialized sub-agents:
    1. bootstrap_agent - Analyze a repository for the first time (initial analysis)
    2. sync_agent - Check for new commits since last analysis
    3. query_agent - Answer questions about quality trends AND list analyzed repositories
    
    Routing rules (analyze user's request and transfer):
    - "Bootstrap X" or "Analyze X" or "Audit X" → transfer to bootstrap_agent
    - "Sync X" or "Check X for updates" or "New commits in X" → transfer to sync_agent
    - "Trends" or "Quality of X" or "Issues in X" or "Why" → transfer to query_agent
    - "What repos" or "Which repositories" or "List repos" → transfer to query_agent
    
    CRITICAL: You are a DISPATCHER, not an executor.
    - Your job: Identify which sub-agent should handle the request
    - Then: Use transfer_to_agent() to route the request
    - The sub-agent will respond DIRECTLY to the user
    - You do NOT need to see or process the sub-agent's response
    
    Always use proper repository format: owner/repo (e.g., 'facebook/react')
    """,
    sub_agents=[bootstrap_agent, sync_agent, query_agent],
)

logger.info("✅ Quality Guardian Agent initialized (Coordinator/Dispatcher)")
logger.info("   Root: quality_guardian → 3 sub-agents")
logger.info("   Sub-agents: bootstrap_agent, sync_agent, query_agent")
logger.info("   Pattern: LLM-Driven Delegation (transfer_to_agent)")
