"""Example unit tests using changeset-based test infrastructure.

Demonstrates how to write tests that use unified changeset definitions
for fast, deterministic testing without GitHub API.
"""

import pytest
from pathlib import Path

from capstone.changesets import (
    ALL_CHANGESETS,
    CHANGESET_01_SQL_INJECTION,
    CHANGESET_04_CLEAN_CODE,
    get_changeset
)
from capstone.tools.diff_generator import generate_diff_from_changeset, generate_all_diffs
from capstone.tools.mock_pr_context import (
    create_mock_pr_from_changeset,
    create_all_mock_prs,
    create_mock_pr_context_dict
)


class TestChangesetInfrastructure:
    """Test the changeset infrastructure itself."""
    
    def test_all_changesets_defined(self):
        """Verify all expected changesets are defined."""
        assert len(ALL_CHANGESETS) >= 4, "Should have at least 4 changesets"
        
        changeset_ids = [cs.id for cs in ALL_CHANGESETS]
        assert "cs-01-sql-injection" in changeset_ids
        assert "cs-02-high-complexity" in changeset_ids
        assert "cs-03-style-violations" in changeset_ids
        assert "cs-04-clean-code" in changeset_ids
    
    def test_changeset_structure(self):
        """Verify changeset has required fields."""
        cs = CHANGESET_01_SQL_INJECTION
        
        assert cs.id
        assert cs.name
        assert cs.target_file
        assert cs.operation in ["add", "modify", "replace"]
        assert cs.pr_title
        assert cs.pr_body
        assert cs.branch_name
        assert len(cs.expected_issues) > 0
    
    def test_expected_issues_structure(self):
        """Verify expected issues have required fields."""
        cs = CHANGESET_01_SQL_INJECTION
        
        for issue in cs.expected_issues:
            assert issue.type
            assert issue.severity in ["critical", "high", "medium", "low"]
            assert issue.description
            assert issue.file_path == cs.target_file


class TestDiffGeneration:
    """Test synthetic diff generation from changesets."""
    
    def test_generate_add_diff(self):
        """Test generating diff for file addition."""
        diff = generate_diff_from_changeset(CHANGESET_01_SQL_INJECTION)
        
        # Check git diff format
        assert "diff --git" in diff
        assert "new file mode" in diff
        assert CHANGESET_01_SQL_INJECTION.target_file in diff
        
        # Check content is present
        assert "def login" in diff or "login" in diff
        assert "++" in diff  # Lines added
    
    def test_generate_all_diffs(self):
        """Test generating diffs for all changesets."""
        diffs = generate_all_diffs()
        
        assert len(diffs) == len(ALL_CHANGESETS)
        assert "cs-01-sql-injection" in diffs
        
        # Each diff should be valid git format
        for changeset_id, diff in diffs.items():
            assert "diff --git" in diff
            assert len(diff) > 0
    
    def test_diff_contains_changeset_code(self):
        """Test that generated diff contains code from changeset."""
        cs = CHANGESET_01_SQL_INJECTION
        diff = generate_diff_from_changeset(cs)
        
        # Check that code content appears in diff
        if cs.new_content:
            # At least some lines from new_content should appear
            sample_line = cs.new_content.split("\n")[5]  # Grab a middle line
            sample_text = sample_line.strip()[:20]  # First 20 chars
            if sample_text:
                assert sample_text in diff


class TestMockPRCreation:
    """Test mock PR object creation from changesets."""
    
    def test_create_mock_pr(self):
        """Test creating mock PR from changeset."""
        pr = create_mock_pr_from_changeset(CHANGESET_01_SQL_INJECTION)
        
        assert pr.metadata.title == CHANGESET_01_SQL_INJECTION.pr_title
        assert pr.metadata.base_branch == "main"
        assert pr.metadata.head_branch == CHANGESET_01_SQL_INJECTION.branch_name
        assert len(pr.diff.files) == 1
        assert pr.diff.files[0].filename == CHANGESET_01_SQL_INJECTION.target_file
    
    def test_create_all_mock_prs(self):
        """Test creating mock PRs for all changesets."""
        prs = create_all_mock_prs()
        
        assert len(prs) == len(ALL_CHANGESETS)
        
        # Each PR should be properly formed
        for pr in prs:
            assert pr.url
            assert pr.repo_name
            assert pr.author
            assert pr.metadata
            assert pr.diff
            assert len(pr.diff.files) > 0
    
    def test_mock_pr_has_diff_stats(self):
        """Test that mock PR has realistic diff statistics."""
        pr = create_mock_pr_from_changeset(CHANGESET_01_SQL_INJECTION)
        
        assert pr.diff.total_additions > 0
        assert pr.diff.changed_files_count == 1
        assert pr.diff.files[0].additions > 0
    
    def test_mock_pr_context_dict(self):
        """Test simple dict context creation."""
        context = create_mock_pr_context_dict(CHANGESET_01_SQL_INJECTION)
        
        assert "title" in context
        assert "branch" in context
        assert "file" in context
        assert "expected_issues" in context
        assert context["expected_issues"] > 0


class TestChangesetLookup:
    """Test changeset lookup utilities."""
    
    def test_get_changeset_by_id(self):
        """Test retrieving changeset by ID."""
        cs = get_changeset("cs-01-sql-injection")
        assert cs is not None
        assert cs.id == "cs-01-sql-injection"
    
    def test_get_nonexistent_changeset(self):
        """Test getting changeset that doesn't exist."""
        cs = get_changeset("nonexistent-id")
        assert cs is None


class TestChangesetExpectations:
    """Test changeset expected issues definitions."""
    
    def test_sql_injection_expectations(self):
        """Test SQL injection changeset has proper expectations."""
        cs = CHANGESET_01_SQL_INJECTION
        
        # Should have critical security issues
        critical = [i for i in cs.expected_issues if i.severity == "critical"]
        assert len(critical) > 0
        
        # At least one must be SQL injection
        sql_issues = [i for i in critical if "sql" in i.type.lower()]
        assert len(sql_issues) > 0
        
        # Should have at least one must-detect issue
        must_detect = [i for i in cs.expected_issues if i.must_detect]
        assert len(must_detect) > 0
    
    def test_clean_code_expectations(self):
        """Test clean code changeset expects no issues."""
        cs = CHANGESET_04_CLEAN_CODE
        
        # Clean code might have expected_issues empty, or all low severity
        if cs.expected_issues:
            # If there are expectations, none should be critical
            critical = [i for i in cs.expected_issues if i.severity == "critical"]
            assert len(critical) == 0
    
    def test_all_changesets_have_test_criteria(self):
        """Test all changesets have evaluation criteria."""
        for cs in ALL_CHANGESETS:
            assert hasattr(cs, "min_issues_to_detect")
            assert hasattr(cs, "max_false_positives")
            assert hasattr(cs, "target_processing_time")
            assert cs.target_processing_time > 0


# Example: How to use in actual agent tests
class TestAgentWithChangesets:
    """Example: Testing agents with changeset-based infrastructure."""
    
    @pytest.mark.skip(reason="Example - requires agent implementation")
    async def test_analyzer_detects_sql_injection(self):
        """Example test: Analyzer agent detects SQL injection from changeset."""
        from capstone.agents import AnalyzerAgent  # Not implemented yet
        
        # Get changeset
        cs = CHANGESET_01_SQL_INJECTION
        
        # Generate diff
        diff = generate_diff_from_changeset(cs)
        
        # Analyze
        agent = AnalyzerAgent()
        result = await agent.analyze_diff(diff)
        
        # Verify against changeset expectations
        critical_found = [i for i in result.issues if i.severity == "critical"]
        expected_critical = [i for i in cs.expected_issues if i.severity == "critical"]
        
        assert len(critical_found) >= len(expected_critical)
        
        # Verify must-detect issues found
        must_detect = [i for i in cs.expected_issues if i.must_detect]
        for expected in must_detect:
            found = any(i.type == expected.type for i in result.issues)
            assert found, f"Must detect {expected.type} but didn't find it"
    
    @pytest.mark.skip(reason="Example - requires agent implementation")
    async def test_full_review_with_mock_pr(self):
        """Example test: Full PR review with mock PR from changeset."""
        from capstone.orchestrator import ReviewOrchestrator  # Not implemented yet
        
        # Create mock PR
        pr = create_mock_pr_from_changeset(CHANGESET_01_SQL_INJECTION)
        
        # Review
        orchestrator = ReviewOrchestrator()
        result = await orchestrator.review_pr_object(pr)
        
        # Verify
        cs = CHANGESET_01_SQL_INJECTION
        assert result.total_issues >= cs.min_issues_to_detect
        assert len(result.false_positives) <= cs.max_false_positives
        assert result.processing_time < cs.target_processing_time
