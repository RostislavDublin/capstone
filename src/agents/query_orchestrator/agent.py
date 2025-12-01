"""Query Orchestrator Agent - Routes query questions to specialized peer agents.

This orchestrator delegates to specialized agents (all at same directory level):
- query_trends: Quality trend analysis
- query_patterns: Issue pattern detection (TODO)
- query_authors: Author quality stats (TODO)
- query_files: Problematic files hotspots (TODO)
- query_metrics: Specific numeric metrics (TODO)
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
from tools.repository_tools import list_analyzed_repositories

# Import sub-agents (only trends for now)
from agents.query_trends.agent import root_agent as trends_agent

logger = logging.getLogger(__name__)

# Retry config
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

root_agent = LlmAgent(
    name="query_orchestrator",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="Routes quality analytics questions to specialized expert agents",
    instruction="""
    You are the Query Orchestrator - you route quality analytics questions to expert sub-agents.
    
    AVAILABLE EXPERTS:
    1. trends_agent - Quality trend analysis (improving/stable/degrading)
       Keywords: "trends", "improving", "degrading", "quality direction", "getting better", "getting worse"
    
    TODO - Coming soon:
    2. patterns_agent - Issue pattern detection
    3. authors_agent - Author quality statistics
    4. files_agent - Problematic files (hotspots)
    5. metrics_agent - Specific numeric metrics
    
    ROUTING RULES:
    - If question mentions trends/improving/degrading → delegate to trends_agent
    - For "what repos" or "list repositories" → call list_analyzed_repositories() tool
    - For all other questions → respond: "This type of analysis is not yet implemented. 
      Currently available: quality trends analysis. Coming soon: patterns, authors, files, metrics."
    
    OUTPUT RULES:
    - Preserve sub-agent response structure and format - DO NOT reformat or rephrase
    - Sub-agents are domain experts with optimized output formats (don't break them)
    - Your role: routing and optional contextual wrapper (not reformatting)
    - You MAY add brief context/intro if it helps clarify what sub-agent provides
    - You MAY NOT change metrics format, rephrase findings, or lose structure
    - Exception: combining multiple sub-agent responses (future feature)
    
    IMPORTANT:
    - Extract repo name from user's question
    - Pass it to the sub-agent
    - Don't try to answer yourself - delegate to experts
    - Be polite about unimplemented features
    """,
    tools=[
        AgentTool(agent=trends_agent),
        list_analyzed_repositories,
    ]
)

logger.info("✅ Query Orchestrator initialized")
logger.info("   Current sub-agents: trends_agent")
logger.info("   TODO: patterns_agent, authors_agent, files_agent, metrics_agent")
