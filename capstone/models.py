"""Data models for agent communication and code review system.

Defines schemas for agent inputs/outputs, review findings, and memory storage.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
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


class AnalyzerInput(BaseModel):
    """Input for Analyzer Agent."""
    pr_url: str = Field(description="GitHub PR URL")
    pr_number: int = Field(description="PR number")
    repo_full_name: str = Field(description="Repository full name (owner/repo)")
    base_sha: str = Field(description="Base commit SHA")
    head_sha: str = Field(description="Head commit SHA")
    diff: str = Field(description="Git diff content")
    files_changed: List[str] = Field(description="List of changed files")


class AnalyzerOutput(BaseModel):
    """Output from Analyzer Agent."""
    issues: List[CodeIssue] = Field(description="Detected issues")
    metrics: Dict[str, Any] = Field(description="Code metrics (complexity, etc)")
    summary: str = Field(description="Analysis summary")
    processing_time: float = Field(description="Time taken in seconds")


class ReviewPattern(BaseModel):
    """A learned review pattern from Memory Bank."""
    pattern_id: str = Field(description="Pattern identifier")
    issue_type: IssueType = Field(description="Type of issue")
    description: str = Field(description="Pattern description")
    example: str = Field(description="Example code that matches")
    frequency: int = Field(default=1, description="Times seen")
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="How often accepted")
    last_seen: datetime = Field(default_factory=datetime.now, description="Last occurrence")


class TeamStandard(BaseModel):
    """Team coding standard."""
    standard_id: str = Field(description="Standard identifier")
    category: str = Field(description="Category (naming, architecture, etc)")
    rule: str = Field(description="The standard rule")
    examples: List[str] = Field(default_factory=list, description="Code examples")
    violations_count: int = Field(default=0, description="Times violated")


class ContextInput(BaseModel):
    """Input for Context Agent."""
    pr_url: str = Field(description="GitHub PR URL")
    repo_full_name: str = Field(description="Repository full name")
    files_changed: List[str] = Field(description="Changed files")
    author: str = Field(description="PR author username")
    issues_found: List[CodeIssue] = Field(description="Issues from Analyzer")


class ContextOutput(BaseModel):
    """Output from Context Agent."""
    patterns: List[ReviewPattern] = Field(description="Relevant patterns")
    standards: List[TeamStandard] = Field(description="Applicable standards")
    previous_reviews: List[str] = Field(description="Similar PR URLs")
    author_preferences: Dict[str, Any] = Field(default_factory=dict, description="Author coding style")
    processing_time: float = Field(description="Time taken in seconds")


class ReviewComment(BaseModel):
    """A formatted review comment."""
    file_path: str = Field(description="File to comment on")
    line: int = Field(description="Line number")
    body: str = Field(description="Comment text in Markdown")
    severity: Severity = Field(description="Comment severity")


class ReporterInput(BaseModel):
    """Input for Reporter Agent."""
    pr_url: str = Field(description="GitHub PR URL")
    issues: List[CodeIssue] = Field(description="All detected issues")
    context: ContextOutput = Field(description="Context from Context Agent")
    analyzer_summary: str = Field(description="Summary from Analyzer")


class ReporterOutput(BaseModel):
    """Output from Reporter Agent."""
    summary: str = Field(description="Overall review summary")
    comments: List[ReviewComment] = Field(description="Inline PR comments")
    priority_issues: List[CodeIssue] = Field(description="Top priority issues")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Review stats")
    processing_time: float = Field(description="Time taken in seconds")


class ReviewResult(BaseModel):
    """Complete review result from orchestrator."""
    pr_url: str = Field(description="GitHub PR URL")
    pr_number: int = Field(description="PR number")
    repo_full_name: str = Field(description="Repository")
    review_id: str = Field(description="Unique review ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Agent outputs
    analyzer_output: AnalyzerOutput
    context_output: ContextOutput
    reporter_output: ReporterOutput
    
    # Overall metrics
    total_issues: int = Field(description="Total issues found")
    critical_issues: int = Field(description="Critical severity count")
    total_time: float = Field(description="Total processing time")
    
    # Status
    status: str = Field(default="completed", description="Review status")
    error: Optional[str] = Field(default=None, description="Error if failed")


class WebhookEvent(BaseModel):
    """GitHub webhook event data."""
    event_type: str = Field(description="Event type (pull_request, etc)")
    action: str = Field(description="Action (opened, synchronize, etc)")
    pr_number: int = Field(description="PR number")
    pr_url: str = Field(description="PR URL")
    repo_full_name: str = Field(description="Repository full name")
    base_sha: str = Field(description="Base commit")
    head_sha: str = Field(description="Head commit")
    author: str = Field(description="PR author")
    timestamp: datetime = Field(default_factory=datetime.now)


class MemoryBankQuery(BaseModel):
    """Query to Memory Bank."""
    query_type: str = Field(description="Type: pattern, standard, history")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    limit: int = Field(default=10, description="Max results")


class MemoryBankResult(BaseModel):
    """Result from Memory Bank query."""
    patterns: List[ReviewPattern] = Field(default_factory=list)
    standards: List[TeamStandard] = Field(default_factory=list)
    total_count: int = Field(description="Total matching items")
