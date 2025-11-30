"""Root Agent - Quality Guardian Orchestrator.

Orchestrates specialized sub-agents via ADK AgentTool composition.
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
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

# Import sub-agents from sibling directories
from agents.bootstrap.agent import root_agent as bootstrap_agent
from agents.sync.agent import root_agent as sync_agent
from agents.query_orchestrator.agent import root_agent as query_agent  # NEW: orchestrator

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
    You are Quality Guardian, an AI assistant for monitoring code quality.
    
    You have three specialist agents:
    1. bootstrap_agent - Analyze a repository for the first time (initial analysis)
    2. sync_agent - Check for new commits since last analysis
    3. query_agent - Answer questions about quality trends AND list analyzed repositories
    
    Routing rules (check user's keywords):
    - "Bootstrap X" or "Analyze X" or "Audit X" → delegate to bootstrap_agent
    - "Sync X" or "Check X for updates" or "New commits in X" → delegate to sync_agent
    - "Trends" or "Quality of X" or "Issues in X" → delegate to query_agent
    - "What repos" or "Which repositories" or "List repos" → delegate to query_agent
    
    IMPORTANT: 
    - "Bootstrap" means initial analysis (can be run multiple times on same repo)
    - query_agent can list ALL analyzed repositories (no repo parameter needed)
    - When delegating to bootstrap_agent, preserve ALL parameters from user's request
    
    Always use proper repository format: owner/repo (e.g., 'facebook/react')
    Provide clear, actionable insights about code quality.
    """,
    tools=[
        AgentTool(agent=bootstrap_agent),
        AgentTool(agent=sync_agent),
        AgentTool(agent=query_agent)
    ]
)

logger.info("✅ Quality Guardian Agent initialized (Multi-Agent Composition)")
logger.info("   Root: quality_guardian → 3 sub-agents")
logger.info("   Sub-agents: bootstrap_agent, sync_agent, query_agent")
logger.info("   Pattern: ADK AgentTool composition (from reference notebooks)")
