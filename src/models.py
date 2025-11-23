"""Data models for Quality Guardian.

Defines core schemas for code issue detection and analysis.
"""

from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(str, Enum):
    """Types of code issues."""
    SECURITY = "security"
    COMPLEXITY = "complexity"
    STYLE = "style"
    PERFORMANCE = "performance"
    BUG = "bug"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"


class CodeLocation(BaseModel):
    """Location of code in a file."""
    file_path: str = Field(description="Path to file relative to repo root")
    line_start: int = Field(description="Starting line number (1-indexed)")
    line_end: int = Field(description="Ending line number (inclusive)")
    snippet: Optional[str] = Field(default=None, description="Code snippet")


class CodeIssue(BaseModel):
    """A detected code issue."""
    issue_id: str = Field(description="Unique issue identifier")
    type: IssueType = Field(description="Type of issue")
    severity: Severity = Field(description="Issue severity")
    title: str = Field(description="Short issue title")
    description: str = Field(description="Detailed description")
    location: CodeLocation = Field(description="Where issue occurs")
    suggestion: Optional[str] = Field(default=None, description="How to fix")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Detection confidence")
