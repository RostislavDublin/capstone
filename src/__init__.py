"""Repository Quality Guardian.

Multi-agent system for independent quality auditing using Google ADK and Gemini.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import vertexai

# Load .env on module import (critical for Vertex AI configuration)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
    # Initialize Vertex AI with location from .env
    vertexai.init(
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("VERTEX_LOCATION", "us-west1")
    )

__version__ = "0.2.0"
__author__ = "Rostislav Dublin"

from .config import AppConfig
from .models import (
    CodeIssue,
    CodeLocation,
    IssueType,
    Severity,
)

__all__ = [
    "AppConfig",
    "CodeIssue",
    "CodeLocation",
    "IssueType",
    "Severity",
]
