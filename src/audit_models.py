"""Models for Quality Guardian - audit reports and metrics."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FileAudit(BaseModel):
    """Audit result for a single file within a commit."""

    file_path: str = Field(description="File path relative to repo root")

    # Security findings for this file
    security_issues: List[Dict[str, Any]] = Field(
        default_factory=list, description="Security vulnerabilities in this file"
    )
    security_score: float = Field(
        default=100.0, ge=0.0, le=100.0, description="Security score (100 = perfect)"
    )

    # Complexity findings for this file
    complexity_issues: List[Dict[str, Any]] = Field(
        default_factory=list, description="High complexity functions in this file"
    )
    avg_complexity: float = Field(
        default=0.0, ge=0.0, description="Average cyclomatic complexity"
    )
    max_complexity: float = Field(
        default=0.0, ge=0.0, description="Maximum complexity in this file"
    )
    function_count: int = Field(default=0, description="Number of functions analyzed")

    # File-level metrics
    lines_of_code: int = Field(default=0, description="Lines of code")
    total_issues: int = Field(default=0, description="Total issues in this file")
    critical_issues: int = Field(default=0, description="Critical severity count")
    high_issues: int = Field(default=0, description="High severity count")
    medium_issues: int = Field(default=0, description="Medium severity count")
    low_issues: int = Field(default=0, description="Low severity count")

    # File quality score
    quality_score: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="File quality score (100 = perfect)",
    )


class CommitAudit(BaseModel):
    """Audit result for a single commit."""

    repository: str = Field(description="Repository identifier (owner/repo)")
    commit_sha: str = Field(description="Commit SHA")
    commit_message: str = Field(description="Commit message")
    author: str = Field(description="Commit author")
    author_email: str = Field(description="Author email")
    date: datetime = Field(description="Commit date")
    files_changed: List[str] = Field(description="List of changed files")

    # Per-file audits (NEW!)
    files: List[FileAudit] = Field(
        default_factory=list, description="Per-file audit details"
    )

    # Security findings
    security_issues: List[Dict[str, Any]] = Field(
        default_factory=list, description="Security vulnerabilities"
    )
    security_score: float = Field(
        default=100.0, ge=0.0, le=100.0, description="Security score (100 = perfect)"
    )

    # Complexity findings
    complexity_issues: List[Dict[str, Any]] = Field(
        default_factory=list, description="High complexity functions/classes"
    )
    avg_complexity: float = Field(
        default=0.0, ge=0.0, description="Average cyclomatic complexity"
    )
    max_complexity: float = Field(
        default=0.0, ge=0.0, description="Maximum complexity found"
    )

    # Overall metrics
    total_issues: int = Field(default=0, description="Total issues found")
    critical_issues: int = Field(default=0, description="Critical severity count")
    high_issues: int = Field(default=0, description="High severity count")
    medium_issues: int = Field(default=0, description="Medium severity count")
    low_issues: int = Field(default=0, description="Low severity count")

    # Quality score
    quality_score: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Overall quality score (100 = perfect)",
    )


class RepositoryAudit(BaseModel):
    """Audit result for an entire repository scan."""

    repo_identifier: str = Field(description="Repository identifier (owner/repo)")
    repo_name: str = Field(description="Repository name")
    default_branch: str = Field(description="Default branch")
    audit_id: str = Field(description="Unique audit identifier")
    audit_date: datetime = Field(
        default_factory=datetime.now, description="When audit was performed"
    )

    # Scan parameters
    scan_type: str = Field(
        description="Type of scan: bootstrap_full, bootstrap_tags, bootstrap_weekly, bootstrap_monthly, sync"
    )
    commits_scanned: int = Field(description="Number of commits analyzed")
    date_range_start: Optional[datetime] = Field(
        default=None, description="Earliest commit in scan"
    )
    date_range_end: Optional[datetime] = Field(
        default=None, description="Latest commit in scan"
    )

    # Commit audits
    commit_audits: List[CommitAudit] = Field(
        default_factory=list, description="Individual commit audits"
    )

    # Aggregated metrics
    total_issues: int = Field(default=0, description="Total issues across all commits")
    critical_issues: int = Field(
        default=0, description="Critical severity count across all commits"
    )
    high_issues: int = Field(default=0, description="High severity count")
    medium_issues: int = Field(default=0, description="Medium severity count")
    low_issues: int = Field(default=0, description="Low severity count")

    # Issue breakdown by type
    issues_by_type: Dict[str, int] = Field(
        default_factory=dict, description="Count by issue type"
    )

    # Quality trends
    avg_quality_score: float = Field(
        default=100.0, ge=0.0, le=100.0, description="Average quality across commits"
    )
    quality_trend: str = Field(
        default="stable", description="Trend: improving, stable, declining"
    )

    # Performance
    processing_time: float = Field(description="Total time taken in seconds")


class QualityQuery(BaseModel):
    """Natural language query about repository quality."""

    query_text: str = Field(description="User's natural language question")
    repo_identifier: str = Field(description="Target repository")
    filters: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional filters: date_range, issue_type, severity, author",
    )


class QualityInsight(BaseModel):
    """Insight from analyzing audit history."""

    insight_id: str = Field(description="Unique insight identifier")
    insight_type: str = Field(
        description="Type: trend, pattern, anomaly, recommendation"
    )
    title: str = Field(description="Short insight title")
    description: str = Field(description="Detailed explanation")
    severity: str = Field(description="Importance level: critical, high, medium, low")
    evidence: List[str] = Field(
        description="Supporting evidence (commit SHAs, dates, metrics)"
    )
    recommendation: Optional[str] = Field(
        default=None, description="Actionable recommendation"
    )


class QueryResponse(BaseModel):
    """Response to quality query."""

    query: QualityQuery = Field(description="Original query")
    response_text: str = Field(description="Natural language answer")
    insights: List[QualityInsight] = Field(
        default_factory=list, description="Key insights"
    )
    metrics: Dict[str, float] = Field(
        default_factory=dict, description="Relevant metrics"
    )
    visualizations: Optional[Dict[str, List]] = Field(
        default=None, description="Data for charts/graphs"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )


class BootstrapCommand(BaseModel):
    """Bootstrap command to scan historical commits."""

    repo_identifier: str = Field(description="Repository to scan (owner/repo)")
    strategy: str = Field(
        description="Sampling: full, tags, weekly, monthly",
        pattern="^(full|tags|weekly|monthly)$",
    )
    date_range_start: Optional[datetime] = Field(
        default=None, description="Optional start date for filtering"
    )
    date_range_end: Optional[datetime] = Field(
        default=None, description="Optional end date for filtering"
    )
    branch: Optional[str] = Field(
        default=None, description="Branch to scan (defaults to default branch)"
    )


class SyncCommand(BaseModel):
    """Sync command to check for new commits."""

    repo_identifier: str = Field(description="Repository to sync (owner/repo)")
    since_audit_id: Optional[str] = Field(
        default=None, description="Continue from specific audit ID"
    )
    branch: Optional[str] = Field(
        default=None, description="Branch to check (defaults to default branch)"
    )


class CommandResult(BaseModel):
    """Result from executing a command."""

    command_type: str = Field(description="Command: bootstrap, sync, query")
    status: str = Field(description="Status: success, error, in_progress")
    message: str = Field(description="Human-readable result message")
    audit: Optional[RepositoryAudit] = Field(
        default=None, description="Audit result if applicable"
    )
    query_response: Optional[QueryResponse] = Field(
        default=None, description="Query response if applicable"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")
    processing_time: float = Field(description="Time taken in seconds")
