"""Agent interfaces and orchestration contracts.

Defines the public API for each agent and orchestrator.
"""

from abc import ABC, abstractmethod
from typing import Optional

from .models import (
    AnalyzerInput, AnalyzerOutput,
    ContextInput, ContextOutput,
    ReporterInput, ReporterOutput,
    ReviewResult, WebhookEvent
)


class BaseAgent(ABC):
    """Base interface for all agents."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging and identification."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Gemini model to use for this agent."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize agent resources (connections, models, etc)."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        pass


class AnalyzerAgentInterface(BaseAgent):
    """Interface for Analyzer Agent.
    
    Responsibilities:
    - Parse git diffs and extract code changes
    - Run static analysis (complexity, security, style)
    - Detect code issues with confidence scores
    - Generate analysis metrics
    
    Model: Gemini 2.5 Flash (fast analysis)
    Tools: git_parser, complexity_analyzer, security_scanner
    """
    
    @abstractmethod
    async def analyze_pr(self, input_data: AnalyzerInput) -> AnalyzerOutput:
        """Analyze a pull request for code issues.
        
        Args:
            input_data: PR metadata and diff content
            
        Returns:
            Analysis output with issues and metrics
            
        Raises:
            AnalysisError: If analysis fails
        """
        pass


class ContextAgentInterface(BaseAgent):
    """Interface for Context Agent.
    
    Responsibilities:
    - Query Memory Bank for relevant patterns
    - Retrieve team coding standards
    - Find similar historical reviews
    - Analyze author preferences
    
    Model: Gemini 2.5 Pro (complex reasoning)
    Memory: ADK Memory Bank with vector search
    """
    
    @abstractmethod
    async def get_context(self, input_data: ContextInput) -> ContextOutput:
        """Retrieve relevant context for review.
        
        Args:
            input_data: PR metadata and detected issues
            
        Returns:
            Context output with patterns, standards, history
            
        Raises:
            ContextError: If context retrieval fails
        """
        pass
    
    @abstractmethod
    async def update_memory(self, review_result: ReviewResult) -> None:
        """Update Memory Bank with review outcome.
        
        Args:
            review_result: Completed review with user feedback
        """
        pass


class ReporterAgentInterface(BaseAgent):
    """Interface for Reporter Agent.
    
    Responsibilities:
    - Generate human-readable review summary
    - Format inline PR comments with context
    - Prioritize issues by severity and relevance
    - Post comments to GitHub
    
    Model: Gemini 2.5 Flash (fast formatting)
    Tools: github_commenter, markdown_formatter
    """
    
    @abstractmethod
    async def generate_report(self, input_data: ReporterInput) -> ReporterOutput:
        """Generate formatted review report.
        
        Args:
            input_data: Issues, context, and analysis summary
            
        Returns:
            Report output with comments and summary
            
        Raises:
            ReportingError: If report generation fails
        """
        pass
    
    @abstractmethod
    async def post_to_github(self, output: ReporterOutput, pr_url: str) -> bool:
        """Post review comments to GitHub PR.
        
        Args:
            output: Generated report
            pr_url: Target PR URL
            
        Returns:
            True if successful, False otherwise
        """
        pass


class OrchestratorInterface(ABC):
    """Interface for review orchestrator.
    
    Responsibilities:
    - Process webhook events
    - Coordinate agent execution (Analyzer -> Context -> Reporter)
    - Handle errors and retries
    - Track review progress
    - Manage agent sessions
    """
    
    def __init__(
        self,
        analyzer: AnalyzerAgentInterface,
        context: ContextAgentInterface,
        reporter: ReporterAgentInterface
    ):
        """Initialize orchestrator with agents.
        
        Args:
            analyzer: Analyzer agent instance
            context: Context agent instance
            reporter: Reporter agent instance
        """
        self.analyzer = analyzer
        self.context = context
        self.reporter = reporter
    
    @abstractmethod
    async def process_webhook(self, event: WebhookEvent) -> ReviewResult:
        """Process GitHub webhook and orchestrate review.
        
        Args:
            event: Webhook event data
            
        Returns:
            Complete review result
            
        Raises:
            OrchestrationError: If review fails
        """
        pass
    
    @abstractmethod
    async def get_review_status(self, review_id: str) -> Optional[ReviewResult]:
        """Get status of ongoing or completed review.
        
        Args:
            review_id: Review identifier
            
        Returns:
            Review result if found, None otherwise
        """
        pass
