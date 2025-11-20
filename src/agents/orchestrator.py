"""Orchestrator Agent - coordinates multi-agent code review workflow.

This agent orchestrates the complete code review process:
1. Repository Merger: Create merged state (base + PR changes)
2. Parallel Analysis: Run Analyzer + Context agents simultaneously
3. Report Generation: Combine findings into final review
4. Error Handling: Graceful degradation if any agent fails
5. Retry Logic: Automatic retry for transient failures
"""

import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from agents.analyzer import AnalyzerAgent
from agents.context import ContextAgent
from agents.reporter import ReporterAgent, ReviewReport
from tools.repo_merger import (
    create_merged_repository,
    cleanup_merged_repository,
    get_changed_files_from_diff
)
from memory.review_memory import MemoryBank


@dataclass
class OrchestrationResult:
    """Result from orchestrated code review."""
    
    success: bool
    report: Optional[ReviewReport]
    error: Optional[str]
    execution_time: float
    analyzer_time: float
    context_time: float
    reporter_time: float


class OrchestratorAgent:
    """Orchestrates multi-agent code review workflow."""
    
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash-exp",
        max_retries: int = 2,
        timeout: int = 120,
        memory_bank: Optional[MemoryBank] = None
    ):
        """Initialize orchestrator.
        
        Args:
            model_name: Gemini model to use for all agents
            max_retries: Maximum retry attempts for failed operations
            timeout: Timeout in seconds for agent operations
            memory_bank: Optional shared Memory Bank for all agents
        """
        self.memory = memory_bank or MemoryBank()
        self.analyzer = AnalyzerAgent(model_name=model_name)
        self.context = ContextAgent(model_name=model_name, memory_bank=self.memory)
        self.reporter = ReporterAgent()
        self.max_retries = max_retries
        self.timeout = timeout
        
    def review_pull_request(
        self,
        diff_text: str,
        base_repo_path: str,
        pr_metadata: Optional[Dict] = None
    ) -> OrchestrationResult:
        """Execute complete code review workflow.
        
        Args:
            diff_text: Git unified diff of PR changes
            base_repo_path: Path to base repository
            pr_metadata: Optional PR metadata (number, author, title, etc.)
            
        Returns:
            OrchestrationResult with report and timing info
        """
        start_time = time.time()
        merged_repo_path = None
        
        try:
            # Step 1: Create merged repository
            print("🔄 Step 1: Creating merged repository state...")
            merged_repo_path = self._create_merged_state(diff_text, base_repo_path)
            changed_files = get_changed_files_from_diff(diff_text)
            
            # Step 2: Run Analyzer + Context in parallel
            print("🔍 Step 2: Running parallel analysis (Analyzer + Context)...")
            analyzer_results, context_results, analyzer_time, context_time = (
                self._run_parallel_analysis(diff_text, merged_repo_path, changed_files)
            )
            
            # Step 3: Generate report
            print("📝 Step 3: Generating final report...")
            report_start = time.time()
            report = self.reporter.generate_report(
                analyzer_results=analyzer_results,
                context_results=context_results,
                pr_metadata=pr_metadata
            )
            reporter_time = time.time() - report_start
            
            execution_time = time.time() - start_time
            
            return OrchestrationResult(
                success=True,
                report=report,
                error=None,
                execution_time=execution_time,
                analyzer_time=analyzer_time,
                context_time=context_time,
                reporter_time=reporter_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Orchestration failed: {str(e)}"
            print(f"❌ Error: {error_msg}")
            
            return OrchestrationResult(
                success=False,
                report=None,
                error=error_msg,
                execution_time=execution_time,
                analyzer_time=0.0,
                context_time=0.0,
                reporter_time=0.0
            )
            
        finally:
            # Cleanup merged repository
            if merged_repo_path:
                print("🧹 Cleaning up merged repository...")
                cleanup_merged_repository(merged_repo_path)
    
    def _create_merged_state(
        self,
        diff_text: str,
        base_repo_path: str
    ) -> str:
        """Create merged repository with retry logic.
        
        Args:
            diff_text: Git diff
            base_repo_path: Base repository path
            
        Returns:
            Path to merged repository
            
        Raises:
            Exception: If merge fails after retries
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                merged_path = create_merged_repository(base_repo_path, diff_text)
                return merged_path
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    print(f"⚠️  Merge attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
        
        raise Exception(f"Failed to create merged state after {self.max_retries} attempts: {last_error}")
    
    def _run_parallel_analysis(
        self,
        diff_text: str,
        merged_repo_path: str,
        changed_files: list
    ) -> Tuple[Dict, Dict, float, float]:
        """Run Analyzer and Context agents in parallel.
        
        Args:
            diff_text: Git diff
            merged_repo_path: Path to merged repository
            changed_files: List of changed files
            
        Returns:
            Tuple of (analyzer_results, context_results, analyzer_time, context_time)
        """
        analyzer_results = None
        context_results = None
        analyzer_time = 0.0
        context_time = 0.0
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks
            analyzer_future = executor.submit(
                self._run_analyzer_with_retry,
                diff_text,
                merged_repo_path
            )
            context_future = executor.submit(
                self._run_context_with_retry,
                merged_repo_path,
                changed_files
            )
            
            # Collect results as they complete
            futures = {
                analyzer_future: 'analyzer',
                context_future: 'context'
            }
            
            for future in as_completed(futures, timeout=self.timeout):
                agent_name = futures[future]
                try:
                    result, exec_time = future.result()
                    if agent_name == 'analyzer':
                        analyzer_results = result
                        analyzer_time = exec_time
                        print(f"  ✓ Analyzer completed in {exec_time:.2f}s")
                    else:
                        context_results = result
                        context_time = exec_time
                        print(f"  ✓ Context completed in {exec_time:.2f}s")
                except Exception as e:
                    print(f"  ✗ {agent_name.capitalize()} failed: {str(e)}")
                    # Set empty results for failed agent
                    if agent_name == 'analyzer':
                        analyzer_results = self._get_empty_analyzer_results()
                    else:
                        context_results = self._get_empty_context_results()
        
        # Ensure we have results (even if empty)
        if analyzer_results is None:
            analyzer_results = self._get_empty_analyzer_results()
        if context_results is None:
            context_results = self._get_empty_context_results()
            
        return analyzer_results, context_results, analyzer_time, context_time
    
    def _run_analyzer_with_retry(
        self,
        diff_text: str,
        merged_repo_path: str
    ) -> Tuple[Dict, float]:
        """Run Analyzer agent with retry logic.
        
        Args:
            diff_text: Git diff
            merged_repo_path: Path to merged repository
            
        Returns:
            Tuple of (results, execution_time)
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                results = self.analyzer.analyze_pull_request(
                    diff_text=diff_text,
                    base_repo_path=merged_repo_path
                )
                execution_time = time.time() - start_time
                return results, execution_time
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    print(f"    ⚠️  Analyzer attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
        
        raise Exception(f"Analyzer failed after {self.max_retries} attempts: {last_error}")
    
    def _run_context_with_retry(
        self,
        merged_repo_path: str,
        changed_files: list
    ) -> Tuple[Dict, float]:
        """Run Context agent with retry logic.
        
        Args:
            merged_repo_path: Path to merged repository
            changed_files: List of changed files
            
        Returns:
            Tuple of (results, execution_time)
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                results = self.context.analyze_context(
                    repo_path=merged_repo_path,
                    changed_files=changed_files,
                    old_versions=None
                )
                execution_time = time.time() - start_time
                return results, execution_time
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    print(f"    ⚠️  Context attempt {attempt + 1} failed, retrying...")
                    time.sleep(1)
        
        raise Exception(f"Context failed after {self.max_retries} attempts: {last_error}")
    
    def _get_empty_analyzer_results(self) -> Dict:
        """Get empty analyzer results for graceful degradation."""
        return {
            "security_issues": {},
            "complexity_analysis": {},
            "ai_recommendations": "Analyzer agent unavailable - manual review recommended."
        }
    
    def _get_empty_context_results(self) -> Dict:
        """Get empty context results for graceful degradation."""
        from tools.dependency_analyzer import ImpactAnalysis
        
        return {
            "impact_analysis": ImpactAnalysis(
                changed_modules=[],
                affected_modules=[],
                breaking_changes=[],
                risk_level="unknown"
            ),
            "dependency_graph": {},
            "ai_insights": "Context agent unavailable - manual review recommended."
        }
