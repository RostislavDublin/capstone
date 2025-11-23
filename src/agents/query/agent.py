"""Query Agent - Answer questions about quality trends."""
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
from tools.repository_tools import query_trends

logger = logging.getLogger(__name__)

# Retry config
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

root_agent = LlmAgent(
    name="query_agent",
    model=Gemini(model="gemini-2.0-flash-001", retry_options=retry_config),
    description="Answers questions about quality trends using RAG-grounded analysis",
    instruction="""
    You answer questions about code quality trends.
    
    When users ask about:
    - "quality trends" → Use query_trends with question="What are the overall quality trends?"
    - "improving/degrading" → Use query_trends with specific question
    - "common issues" → Use query_trends with question="What are the most common issues?"
    - Any trend question → Always use query_trends tool
    
    ALWAYS use the query_trends tool - it uses Gemini with RAG to analyze audit history.
    Never ask users to clarify - just construct an appropriate question and call the tool.
    
    Provide clear insights about trends, issues, and quality changes.
    Be specific with numbers and commit references when available.
    """,
    tools=[query_trends]
)

logger.debug("Query agent initialized")
