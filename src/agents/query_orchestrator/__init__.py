"""query_orchestrator agent for ADK web."""
import os
from pathlib import Path
from dotenv import load_dotenv
import vertexai

# Load .env from project root (ensures configuration for ADK eval and direct usage)
env_file = Path(__file__).parent.parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Initialize Vertex AI with location from .env
project = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("VERTEX_LOCATION", "us-west1")
if project:
    vertexai.init(project=project, location=location)

from .agent import root_agent

__all__ = ["root_agent"]
