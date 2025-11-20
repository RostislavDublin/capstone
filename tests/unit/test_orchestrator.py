"""Unit tests for Orchestrator Agent."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import TimeoutError

from agents.orchestrator import OrchestratorAgent, OrchestrationResult
from agents.reporter import ReviewReport
from tools.dependency_analyzer import ImpactAnalysis


@pytest.fixture
def sample_diff():
    """Sample git diff for testing."""
    return """diff --git a/test.py b/test.py
index 123..456 789
--- a/test.py
+++ b/test.py
@@ -1,3 +1,5 @@
 def hello():
-    pass
+    # SQL injection
+    query = f"SELECT * FROM users WHERE id={user_id}"
+    return query
"""


@pytest.fixture
def sample_analyzer_results():
    """Sample analyzer results."""
    return {
        "security_issues": {
            "test.py": Mock(
                total_issues=1,
                high_severity_count=1,
                medium_severity_count=0,
                low_severity_count=0
            )
        },
        "complexity_analysis": {},
        "ai_recommendations": "Fix SQL injection"
    }


@pytest.fixture
def sample_context_results():
    """Sample context results."""
    return {
        "impact_analysis": ImpactAnalysis(
            changed_modules=["test.py"],
            affected_modules=[],
            breaking_changes=[],
            risk_level="low"
        ),
        "dependency_graph": {},
        "ai_insights": "Low risk change"
    }


def test_orchestrator_initialization():
    """Test orchestrator initialization."""
    orchestrator = OrchestratorAgent()
    
    assert orchestrator.analyzer is not None
    assert orchestrator.context is not None
    assert orchestrator.reporter is not None
    assert orchestrator.max_retries == 2
    assert orchestrator.timeout == 120


def test_orchestrator_custom_config():
    """Test orchestrator with custom configuration."""
    orchestrator = OrchestratorAgent(
        model_name="gemini-2.0-flash-exp",
        max_retries=3,
        timeout=60
    )
    
    assert orchestrator.max_retries == 3
    assert orchestrator.timeout == 60


@patch('agents.orchestrator.create_merged_repository')
@patch('agents.orchestrator.cleanup_merged_repository')
@patch('agents.orchestrator.get_changed_files_from_diff')
def test_successful_review(
    mock_get_files,
    mock_cleanup,
    mock_merge,
    sample_diff,
    sample_analyzer_results,
    sample_context_results
):
    """Test successful end-to-end review."""
    # Setup mocks
    mock_merge.return_value = "/tmp/merged_repo"
    mock_get_files.return_value = ["test.py"]
    
    orchestrator = OrchestratorAgent()
    
    # Mock agent methods
    orchestrator.analyzer.analyze_pull_request = Mock(return_value=sample_analyzer_results)
    orchestrator.context.analyze_context = Mock(return_value=sample_context_results)
    
    mock_report = ReviewReport(
        summary="Test summary",
        security_section="Security issues",
        complexity_section="No complexity issues",
        context_section="Low risk",
        ai_recommendations="Fix issues",
        overall_verdict="REQUEST_CHANGES"
    )
    orchestrator.reporter.generate_report = Mock(return_value=mock_report)
    
    # Execute
    result = orchestrator.review_pull_request(
        diff_text=sample_diff,
        base_repo_path="/tmp/base_repo",
        pr_metadata={"pr_number": 123}
    )
    
    # Assertions
    assert result.success is True
    assert result.report is not None
    assert result.error is None
    assert result.execution_time > 0
    assert result.analyzer_time >= 0
    assert result.context_time >= 0
    assert result.reporter_time >= 0
    
    # Verify agent calls
    orchestrator.analyzer.analyze_pull_request.assert_called_once()
    orchestrator.context.analyze_context.assert_called_once()
    orchestrator.reporter.generate_report.assert_called_once()
    
    # Verify cleanup
    mock_cleanup.assert_called_once_with("/tmp/merged_repo")


@patch('agents.orchestrator.create_merged_repository')
@patch('agents.orchestrator.cleanup_merged_repository')
def test_merge_failure(mock_cleanup, mock_merge, sample_diff):
    """Test handling of merge failure."""
    # Setup mock to fail
    mock_merge.side_effect = Exception("Merge failed")
    
    orchestrator = OrchestratorAgent(max_retries=1)
    
    # Execute
    result = orchestrator.review_pull_request(
        diff_text=sample_diff,
        base_repo_path="/tmp/base_repo"
    )
    
    # Assertions
    assert result.success is False
    assert result.report is None
    assert "Merge failed" in result.error or "Failed to create merged state" in result.error
    assert result.execution_time > 0


@patch('agents.orchestrator.create_merged_repository')
@patch('agents.orchestrator.cleanup_merged_repository')
@patch('agents.orchestrator.get_changed_files_from_diff')
def test_analyzer_failure_graceful_degradation(
    mock_get_files,
    mock_cleanup,
    mock_merge,
    sample_diff,
    sample_context_results
):
    """Test graceful degradation when Analyzer fails."""
    # Setup mocks
    mock_merge.return_value = "/tmp/merged_repo"
    mock_get_files.return_value = ["test.py"]
    
    orchestrator = OrchestratorAgent(max_retries=1)
    
    # Mock analyzer to fail, context to succeed
    orchestrator.analyzer.analyze_pull_request = Mock(side_effect=Exception("Analyzer error"))
    orchestrator.context.analyze_context = Mock(return_value=sample_context_results)
    
    mock_report = ReviewReport(
        summary="Test summary",
        security_section="",
        complexity_section="",
        context_section="Low risk",
        ai_recommendations="Manual review needed",
        overall_verdict="COMMENT"
    )
    orchestrator.reporter.generate_report = Mock(return_value=mock_report)
    
    # Execute
    result = orchestrator.review_pull_request(
        diff_text=sample_diff,
        base_repo_path="/tmp/base_repo"
    )
    
    # Should still succeed with degraded results
    assert result.success is True
    assert result.report is not None
    assert result.analyzer_time >= 0  # Failed but tracked


@patch('agents.orchestrator.create_merged_repository')
@patch('agents.orchestrator.cleanup_merged_repository')
@patch('agents.orchestrator.get_changed_files_from_diff')
def test_parallel_execution(
    mock_get_files,
    mock_cleanup,
    mock_merge,
    sample_diff,
    sample_analyzer_results,
    sample_context_results
):
    """Test that Analyzer and Context run in parallel."""
    # Setup mocks
    mock_merge.return_value = "/tmp/merged_repo"
    mock_get_files.return_value = ["test.py"]
    
    orchestrator = OrchestratorAgent()
    
    # Track call order
    call_order = []
    
    def analyzer_mock(*args, **kwargs):
        call_order.append('analyzer_start')
        import time
        time.sleep(0.1)  # Simulate work
        call_order.append('analyzer_end')
        return sample_analyzer_results
    
    def context_mock(*args, **kwargs):
        call_order.append('context_start')
        import time
        time.sleep(0.1)  # Simulate work
        call_order.append('context_end')
        return sample_context_results
    
    orchestrator.analyzer.analyze_pull_request = Mock(side_effect=analyzer_mock)
    orchestrator.context.analyze_context = Mock(side_effect=context_mock)
    
    mock_report = ReviewReport(
        summary="Test",
        security_section="",
        complexity_section="",
        context_section="",
        ai_recommendations="",
        overall_verdict="APPROVE"
    )
    orchestrator.reporter.generate_report = Mock(return_value=mock_report)
    
    # Execute
    result = orchestrator.review_pull_request(
        diff_text=sample_diff,
        base_repo_path="/tmp/base_repo"
    )
    
    # Verify both agents ran
    assert result.success is True
    assert 'analyzer_start' in call_order or 'context_start' in call_order
    assert len(call_order) == 4  # Both start and end


def test_empty_analyzer_results():
    """Test empty analyzer results generation."""
    orchestrator = OrchestratorAgent()
    
    empty = orchestrator._get_empty_analyzer_results()
    
    assert "security_issues" in empty
    assert "complexity_analysis" in empty
    assert "ai_recommendations" in empty
    assert "unavailable" in empty["ai_recommendations"].lower()


def test_empty_context_results():
    """Test empty context results generation."""
    orchestrator = OrchestratorAgent()
    
    empty = orchestrator._get_empty_context_results()
    
    assert "impact_analysis" in empty
    assert "dependency_graph" in empty
    assert "ai_insights" in empty
    assert isinstance(empty["impact_analysis"], ImpactAnalysis)
    assert empty["impact_analysis"].risk_level == "unknown"


@patch('agents.orchestrator.create_merged_repository')
@patch('agents.orchestrator.cleanup_merged_repository')
@patch('agents.orchestrator.get_changed_files_from_diff')
def test_retry_logic_success_on_second_attempt(
    mock_get_files,
    mock_cleanup,
    mock_merge,
    sample_diff,
    sample_analyzer_results,
    sample_context_results
):
    """Test retry logic succeeds on second attempt."""
    # Setup mocks
    mock_merge.return_value = "/tmp/merged_repo"
    mock_get_files.return_value = ["test.py"]
    
    orchestrator = OrchestratorAgent(max_retries=2)
    
    # Mock analyzer to fail once, then succeed
    call_count = {'count': 0}
    
    def analyzer_with_retry(*args, **kwargs):
        call_count['count'] += 1
        if call_count['count'] == 1:
            raise Exception("Temporary failure")
        return sample_analyzer_results
    
    orchestrator.analyzer.analyze_pull_request = Mock(side_effect=analyzer_with_retry)
    orchestrator.context.analyze_context = Mock(return_value=sample_context_results)
    
    mock_report = ReviewReport(
        summary="Test",
        security_section="",
        complexity_section="",
        context_section="",
        ai_recommendations="",
        overall_verdict="APPROVE"
    )
    orchestrator.reporter.generate_report = Mock(return_value=mock_report)
    
    # Execute
    result = orchestrator.review_pull_request(
        diff_text=sample_diff,
        base_repo_path="/tmp/base_repo"
    )
    
    # Should succeed after retry
    assert result.success is True
    assert call_count['count'] == 2  # Called twice


@patch('agents.orchestrator.create_merged_repository')
@patch('agents.orchestrator.cleanup_merged_repository')
def test_cleanup_on_error(mock_cleanup, mock_merge, sample_diff):
    """Test cleanup happens even on error."""
    # Setup mock
    mock_merge.return_value = "/tmp/merged_repo"
    
    orchestrator = OrchestratorAgent(max_retries=1)
    
    # Mock get_changed_files to fail
    with patch('agents.orchestrator.get_changed_files_from_diff', side_effect=Exception("Parse error")):
        result = orchestrator.review_pull_request(
            diff_text=sample_diff,
            base_repo_path="/tmp/base_repo"
        )
    
    # Should fail but still cleanup
    assert result.success is False
    mock_cleanup.assert_called_once_with("/tmp/merged_repo")
