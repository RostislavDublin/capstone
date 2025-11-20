"""Memory Bank schema and storage design.

Defines what to store, how to index, and retrieval patterns for the Memory Bank.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Types of memory stored."""
    REVIEW_PATTERN = "review_pattern"
    TEAM_STANDARD = "team_standard"
    AUTHOR_PREFERENCE = "author_preference"
    ISSUE_HISTORY = "issue_history"
    FEEDBACK = "feedback"


class StorageKey(BaseModel):
    """Key for storing and retrieving memories."""
    memory_type: MemoryType
    identifier: str = Field(description="Unique ID within type")
    repo: Optional[str] = Field(default=None, description="Repository scope")
    
    def to_string(self) -> str:
        """Convert to string key."""
        parts = [self.memory_type.value, self.identifier]
        if self.repo:
            parts.append(self.repo)
        return ":".join(parts)


class MemoryMetadata(BaseModel):
    """Metadata for all memory entries."""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    access_count: int = Field(default=0, description="Times accessed")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Current relevance")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")


class ReviewPatternMemory(BaseModel):
    """Memory entry for a learned review pattern.
    
    Stores patterns of issues that recur across reviews.
    Example: "Forgot to close file handles", "Missing null checks"
    """
    key: StorageKey = Field(description="Memory key")
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)
    
    # Pattern content
    pattern_type: str = Field(description="security, complexity, style, etc")
    description: str = Field(description="What this pattern catches")
    code_signature: str = Field(description="Code pattern to match")
    examples: List[str] = Field(description="Example code snippets")
    
    # Learning metrics
    occurrences: int = Field(default=1, description="Times this pattern appeared")
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=1.0, 
                                   description="% of times accepted by devs")
    false_positive_rate: float = Field(default=0.0, ge=0.0, le=1.0,
                                       description="% false positives")
    
    # Context
    common_files: List[str] = Field(default_factory=list, description="Files where it appears")
    related_patterns: List[str] = Field(default_factory=list, description="Related pattern IDs")


class TeamStandardMemory(BaseModel):
    """Memory entry for team coding standards.
    
    Stores rules and conventions specific to the team/repo.
    Example: "Use async/await instead of .then()", "Max line length 100"
    """
    key: StorageKey = Field(description="Memory key")
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)
    
    # Standard content
    category: str = Field(description="naming, architecture, testing, etc")
    rule: str = Field(description="The standard rule")
    rationale: Optional[str] = Field(default=None, description="Why this standard exists")
    examples_good: List[str] = Field(default_factory=list, description="Good examples")
    examples_bad: List[str] = Field(default_factory=list, description="Bad examples")
    
    # Enforcement
    is_strict: bool = Field(default=False, description="Must follow vs should follow")
    violations_count: int = Field(default=0, description="Times violated")
    exceptions: List[str] = Field(default_factory=list, description="Known exceptions")


class AuthorPreferenceMemory(BaseModel):
    """Memory entry for individual author preferences.
    
    Stores coding style and patterns preferred by specific authors.
    Example: "Alice prefers early returns", "Bob uses inline comments"
    """
    key: StorageKey = Field(description="Memory key")
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)
    
    # Author info
    username: str = Field(description="GitHub username")
    
    # Preferences
    style_preferences: Dict[str, Any] = Field(default_factory=dict,
                                              description="Coding style choices")
    common_patterns: List[str] = Field(default_factory=list,
                                       description="Patterns they use often")
    languages: List[str] = Field(default_factory=list, description="Languages they work in")
    
    # Feedback history
    accepted_suggestions: int = Field(default=0, description="Suggestions they accepted")
    rejected_suggestions: int = Field(default=0, description="Suggestions they rejected")
    sensitivity: str = Field(default="medium", description="How they respond to feedback")


class IssueHistoryMemory(BaseModel):
    """Memory entry for historical issue tracking.
    
    Stores past issues and their outcomes for learning.
    """
    key: StorageKey = Field(description="Memory key")
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)
    
    # Issue details
    issue_type: str = Field(description="Type of issue")
    severity: str = Field(description="Severity level")
    description: str = Field(description="What the issue was")
    file_path: str = Field(description="Where it occurred")
    
    # Resolution
    was_fixed: bool = Field(description="Was it fixed")
    resolution_time: Optional[int] = Field(default=None, description="Time to fix (minutes)")
    resolution_notes: Optional[str] = Field(default=None, description="How it was fixed")
    
    # Learning
    was_valid: bool = Field(default=True, description="Was detection correct")
    feedback_received: bool = Field(default=False, description="Did we get feedback")


class FeedbackMemory(BaseModel):
    """Memory entry for explicit user feedback.
    
    Stores feedback on review quality for continuous improvement.
    """
    key: StorageKey = Field(description="Memory key")
    metadata: MemoryMetadata = Field(default_factory=MemoryMetadata)
    
    # Feedback content
    review_id: str = Field(description="Which review this is about")
    feedback_type: str = Field(description="positive, negative, correction")
    rating: Optional[int] = Field(default=None, ge=1, le=5, description="1-5 star rating")
    comment: Optional[str] = Field(default=None, description="Feedback text")
    
    # Specific corrections
    false_positives: List[str] = Field(default_factory=list, description="Wrong detections")
    missed_issues: List[str] = Field(default_factory=list, description="What we missed")
    improvement_areas: List[str] = Field(default_factory=list, description="What to improve")


class MemoryBankIndex(BaseModel):
    """Index structure for efficient memory retrieval.
    
    Supports multiple access patterns:
    - By type (all patterns, all standards, etc)
    - By repo (repo-specific knowledge)
    - By tags (cross-cutting concerns)
    - By relevance (most useful memories)
    """
    
    # Type indexes
    patterns: Dict[str, ReviewPatternMemory] = Field(default_factory=dict)
    standards: Dict[str, TeamStandardMemory] = Field(default_factory=dict)
    preferences: Dict[str, AuthorPreferenceMemory] = Field(default_factory=dict)
    history: Dict[str, IssueHistoryMemory] = Field(default_factory=dict)
    feedback: Dict[str, FeedbackMemory] = Field(default_factory=dict)
    
    # Secondary indexes
    by_repo: Dict[str, List[str]] = Field(default_factory=dict,
                                          description="Repo -> memory IDs")
    by_tag: Dict[str, List[str]] = Field(default_factory=dict,
                                         description="Tag -> memory IDs")
    by_relevance: List[str] = Field(default_factory=list,
                                    description="Memory IDs sorted by relevance")
    
    # Statistics
    total_memories: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.now)


class MemoryQuery(BaseModel):
    """Query specification for Memory Bank retrieval."""
    
    # What to retrieve
    memory_types: List[MemoryType] = Field(description="Types to query")
    
    # Filters
    repo: Optional[str] = Field(default=None, description="Scope to repo")
    tags: List[str] = Field(default_factory=list, description="Must have these tags")
    min_relevance: float = Field(default=0.0, description="Minimum relevance score")
    
    # Search
    text_query: Optional[str] = Field(default=None, description="Text search")
    code_query: Optional[str] = Field(default=None, description="Code pattern search")
    
    # Pagination
    limit: int = Field(default=10, description="Max results")
    offset: int = Field(default=0, description="Skip first N")
    
    # Sorting
    sort_by: str = Field(default="relevance", description="Sort field")
    descending: bool = Field(default=True, description="Sort order")


class MemoryStorageConfig(BaseModel):
    """Configuration for Memory Bank storage backend.
    
    ADK Memory Bank uses JSON storage by default.
    Can be extended to use vector databases for similarity search.
    """
    
    # Storage path
    storage_path: str = Field(default="./memory_bank", description="Where to store")
    
    # Persistence
    auto_save: bool = Field(default=True, description="Auto-save changes")
    save_interval: int = Field(default=300, description="Auto-save interval (seconds)")
    
    # Pruning
    enable_pruning: bool = Field(default=True, description="Prune old memories")
    max_age_days: int = Field(default=90, description="Max memory age")
    min_relevance_threshold: float = Field(default=0.1, description="Prune below this")
    
    # Performance
    cache_size: int = Field(default=1000, description="In-memory cache size")
    index_rebuild_interval: int = Field(default=3600, description="Rebuild index (seconds)")


# Query examples for common use cases
def create_pattern_query(repo: str, issue_types: List[str]) -> MemoryQuery:
    """Create query for review patterns in repo."""
    return MemoryQuery(
        memory_types=[MemoryType.REVIEW_PATTERN],
        repo=repo,
        tags=issue_types,
        limit=20,
        sort_by="acceptance_rate"
    )


def create_standards_query(repo: str, categories: List[str]) -> MemoryQuery:
    """Create query for team standards."""
    return MemoryQuery(
        memory_types=[MemoryType.TEAM_STANDARD],
        repo=repo,
        tags=categories,
        limit=10,
        sort_by="relevance"
    )


def create_author_query(username: str) -> MemoryQuery:
    """Create query for author preferences."""
    return MemoryQuery(
        memory_types=[MemoryType.AUTHOR_PREFERENCE],
        text_query=username,
        limit=1
    )


def create_history_query(repo: str, file_paths: List[str]) -> MemoryQuery:
    """Create query for issue history in files."""
    return MemoryQuery(
        memory_types=[MemoryType.ISSUE_HISTORY],
        repo=repo,
        tags=file_paths,
        limit=50,
        sort_by="metadata.updated_at"
    )
