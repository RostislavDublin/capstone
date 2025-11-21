"""Integration test for Analyzer agent with real PR."""

import pytest
from src.gh_integration import GitHubClient, PRContextLoader
from src.agents.analyzer import AnalyzerAgent
from src.agents.formatter import (
    format_inline_comment,
    format_summary_comment,
    group_findings_by_file,
)


@pytest.mark.integration
def test_analyzer_on_real_pr(github_token: str, test_repo: str, test_pr_number: int):
    """Test complete analyzer workflow with real PR."""
    # Load PR context
    client = GitHubClient(github_token)
    loader = PRContextLoader(client)
    pr_context = loader.load(test_repo, test_pr_number)

    # Run analyzer
    analyzer = AnalyzerAgent()
    result = analyzer.analyze(pr_context)

    # Validate result structure
    assert result.files_analyzed >= 0
    assert result.critical_count >= 0
    assert result.major_count >= 0
    assert result.minor_count >= 0
    assert isinstance(result.findings, list)

    # Validate findings structure
    for finding in result.findings:
        assert finding.severity in ["CRITICAL", "MAJOR", "MINOR"]
        assert finding.category
        assert finding.message
        assert finding.file_path

    print(f"\nAnalyzer Results:")
    print(f"  Files analyzed: {result.files_analyzed}")
    print(f"  Total findings: {len(result.findings)}")
    print(f"  Critical: {result.critical_count}")
    print(f"  Major: {result.major_count}")
    print(f"  Minor: {result.minor_count}")


@pytest.mark.integration
def test_format_and_post_comments(github_token: str, test_repo: str, test_pr_number: int):
    """Test formatting findings and posting as review comments."""
    # Load PR and analyze
    client = GitHubClient(github_token)
    loader = PRContextLoader(client)
    pr_context = loader.load(test_repo, test_pr_number)

    analyzer = AnalyzerAgent()
    result = analyzer.analyze(pr_context)

    if not result.findings:
        pytest.skip("No findings to post")

    # Test formatting
    first_finding = result.findings[0]
    comment_body = format_inline_comment(first_finding)
    assert "**" in comment_body  # Has markdown formatting
    assert first_finding.severity in comment_body

    # Test summary formatting
    summary = format_summary_comment(result.findings, result.files_analyzed)
    assert "Code Review Complete" in summary
    assert str(len(result.findings)) in summary

    # Post ONE test comment and clean it up
    if first_finding.line_number:
        try:
            comment = client.create_review_comment(
                test_repo,
                test_pr_number,
                comment_body,
                first_finding.file_path,
                first_finding.line_number,
            )
            print(f"\nPosted test comment: {comment.html_url}")
            # Cleanup immediately
            comment.delete()
            print("Cleaned up test comment")
        except Exception as e:
            print(f"Failed to post comment (non-fatal): {e}")


@pytest.mark.integration
def test_analyzer_handles_syntax_errors(github_token: str, test_repo: str):
    """Test that analyzer gracefully handles files with syntax errors."""
    from src.gh_integration.context import PRContext, FileChange
    from datetime import datetime

    # Create mock PR context with invalid Python code
    pr_context = PRContext(
        repo_full_name=test_repo,
        pr_number=999,
        title="Test PR",
        description="Test",
        author="test",
        base_branch="main",
        head_branch="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        files=[
            FileChange(
                filename="test.py",
                status="added",
                additions=5,
                deletions=0,
                changes=5,
                patch="""@@ -0,0 +1,5 @@
+def broken_function(
+    # Missing closing paren
+    x = 1
+    return x
+""",
            )
        ],
        diff="",
        review_comments=[],
        issue_comments=[],
        labels=[],
        is_draft=False,
        mergeable=True,
    )

    # Analyzer should not crash
    analyzer = AnalyzerAgent()
    result = analyzer.analyze(pr_context)

    # Should complete without raising exception
    assert result.files_analyzed == 1
    # Findings list may be empty due to syntax error
    assert isinstance(result.findings, list)
