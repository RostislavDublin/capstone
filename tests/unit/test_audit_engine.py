"""Tests for audit engine."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.audit.engine import AuditEngine
from src.connectors.base import CommitInfo, RepositoryInfo


@pytest.fixture
def mock_connector():
    """Create mock repository connector."""
    connector = Mock()
    connector.get_repository_info.return_value = RepositoryInfo(
        full_name="test-owner/test-repo",
        owner="test-owner",
        name="test-repo",
        description="Test repository",
        default_branch="main",
        created_at=datetime(2024, 1, 1),
        language="Python",
        topics=["testing"],
    )
    return connector


@pytest.fixture
def audit_engine(mock_connector):
    """Create AuditEngine instance."""
    return AuditEngine(connector=mock_connector)


@pytest.fixture
def sample_commit():
    """Create sample commit info."""
    return CommitInfo(
        sha="abc123",
        message="Add new feature",
        author="Test Author",
        author_email="test@example.com",
        date=datetime(2024, 11, 20),
        files_changed=["file1.py", "file2.py"],
        additions=10,
        deletions=5,
    )


@pytest.fixture
def sample_repo_with_code(tmp_path):
    """Create temporary repository with Python files."""
    # Create structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".git").mkdir()  # Should be excluded

    # File with security issue (SQL injection)
    (tmp_path / "src" / "database.py").write_text(
        '''
def get_user(username):
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return execute_query(query)
'''
    )

    # File with high complexity (complexity > 10)
    (tmp_path / "src" / "complex.py").write_text(
        '''
def complex_function(a, b, c, d):
    if a > 10:
        if b > 10:
            if c > 10:
                if d > 10:
                    return "all very high"
                elif d > 5:
                    return "d medium"
                else:
                    return "d low"
            elif c > 5:
                return "c medium"
            else:
                return "c low"
        elif b > 5:
            if c > 5:
                return "b and c medium"
            else:
                return "b medium"
        else:
            return "b low"
    elif a > 5:
        if b > 5:
            if c > 5:
                return "all medium"
            else:
                return "a and b medium"
        else:
            return "a medium"
    else:
        return "all low"
'''
    )

    # Clean file
    (tmp_path / "src" / "utils.py").write_text(
        '''
def simple_function():
    return "Hello"
'''
    )

    # Test file (should be analyzed too)
    (tmp_path / "tests" / "test_utils.py").write_text(
        '''
def test_simple():
    assert True
'''
    )

    return tmp_path


def test_find_python_files(audit_engine, sample_repo_with_code):
    """Test Python file discovery."""
    files = audit_engine._find_python_files(str(sample_repo_with_code))

    # Should find all .py files except those in excluded dirs
    filenames = {f.name for f in files}
    assert "database.py" in filenames
    assert "complex.py" in filenames
    assert "utils.py" in filenames
    assert "test_utils.py" in filenames

    # Should exclude .git directory
    assert not any(".git" in str(f) for f in files)


def test_find_python_files_excludes_common_dirs(audit_engine, tmp_path):
    """Test that common directories are excluded."""
    # Create directories that should be excluded
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "venv").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "node_modules").mkdir()

    # Add Python files in excluded dirs
    (tmp_path / "__pycache__" / "cache.py").write_text("# cached")
    (tmp_path / "venv" / "site.py").write_text("# venv")

    # Add valid Python file
    (tmp_path / "main.py").write_text("# main")

    files = audit_engine._find_python_files(str(tmp_path))

    assert len(files) == 1
    assert files[0].name == "main.py"


def test_calculate_security_score_no_issues(audit_engine):
    """Test security score with no issues."""
    score = audit_engine._calculate_security_score([])
    assert abs(score - 100.0) < 0.01


def test_calculate_security_score_with_issues(audit_engine):
    """Test security score with various severity issues."""
    issues = [
        {"severity": "critical"},
        {"severity": "high"},
        {"severity": "medium"},
        {"severity": "low"},
    ]

    score = audit_engine._calculate_security_score(issues)

    # critical=20, high=10, medium=5, low=1 -> 100 - 36 = 64
    assert abs(score - 64.0) < 0.01


def test_calculate_quality_score_perfect(audit_engine):
    """Test quality score calculation with perfect metrics."""
    score = audit_engine._calculate_quality_score(
        security_score=100.0, avg_complexity=5.0, high_complexity_count=0
    )

    # Perfect security (60%) + perfect complexity (40%) = 100
    assert abs(score - 100.0) < 0.01


def test_calculate_quality_score_mixed(audit_engine):
    """Test quality score with mixed metrics."""
    score = audit_engine._calculate_quality_score(
        security_score=80.0, avg_complexity=12.0, high_complexity_count=3
    )

    # Security: 80 * 0.6 = 48
    # Complexity: (100 - (2*2 + 3*3)) * 0.4 = (100 - 13) * 0.4 = 34.8
    # Total: 48 + 34.8 = 82.8
    assert abs(score - 82.8) < 0.01


def test_create_complexity_issue(audit_engine, tmp_path):
    """Test complexity issue creation."""
    from src.tools.complexity_analyzer import FunctionComplexity

    func_data = FunctionComplexity(
        name="test_func",
        lineno=10,
        col_offset=0,
        endline=15,
        cyclomatic_complexity=25,
        complexity_rank="F",
    )
    file_path = tmp_path / "test.py"

    issue = audit_engine._create_complexity_issue(func_data, file_path)

    assert issue["type"] == "complexity"
    assert issue["severity"] == "critical"  # > 20
    assert "test_func" in issue["message"]
    assert issue["line"] == 10


def test_create_complexity_issue_severities(audit_engine, tmp_path):
    """Test complexity severity levels."""
    from src.tools.complexity_analyzer import FunctionComplexity

    file_path = tmp_path / "test.py"

    # Critical: > 20
    issue_critical = audit_engine._create_complexity_issue(
        FunctionComplexity("f1", 1, 0, 5, 25, "F"), file_path
    )
    assert issue_critical["severity"] == "critical"

    # High: 15-20
    issue_high = audit_engine._create_complexity_issue(
        FunctionComplexity("f2", 2, 0, 6, 18, "E"), file_path
    )
    assert issue_high["severity"] == "high"

    # Medium: 10-15
    issue_medium = audit_engine._create_complexity_issue(
        FunctionComplexity("f3", 3, 0, 7, 12, "C"), file_path
    )
    assert issue_medium["severity"] == "medium"


@patch("src.audit.engine.tempfile.TemporaryDirectory")
def test_audit_commit_integration(
    mock_temp_dir, audit_engine, mock_connector, sample_commit, sample_repo_with_code
):
    """Test complete commit audit."""
    # Mock temporary directory to use our sample repo
    mock_temp_dir.return_value.__enter__.return_value = str(sample_repo_with_code)
    mock_connector.clone_repository.return_value = str(sample_repo_with_code)

    audit = audit_engine.audit_commit("test-owner/test-repo", sample_commit)

    # Verify commit info
    assert audit.commit_sha == "abc123"
    assert audit.author == "Test Author"
    assert audit.commit_message == "Add new feature"

    # Should detect security issue (SQL injection in database.py)
    assert len(audit.security_issues) > 0
    assert audit.security_score < 100.0

    # Should detect complexity issue (complex_function has complexity > 10)
    assert len(audit.complexity_issues) > 0
    assert audit.max_complexity > 10

    # Should have overall quality score
    assert 0.0 <= audit.quality_score <= 100.0

    # Should count issues
    assert audit.total_issues > 0


def test_audit_repository_multiple_commits(
    audit_engine, mock_connector, sample_commit, sample_repo_with_code
):
    """Test repository audit with multiple commits."""
    with patch("src.audit.engine.tempfile.TemporaryDirectory") as mock_temp_dir:
        mock_temp_dir.return_value.__enter__.return_value = str(sample_repo_with_code)
        mock_connector.clone_repository.return_value = str(sample_repo_with_code)

        # Create multiple commits
        commits = [
            CommitInfo(
                sha=f"commit{i}",
                message=f"Commit {i}",
                author="Test Author",
                author_email="test@example.com",
                date=datetime(2024, 11, i + 1),
                files_changed=[f"file{i}.py"],
                additions=10,
                deletions=5,
            )
            for i in range(3)
        ]

        repo_audit = audit_engine.audit_repository(
            "test-owner/test-repo", commits, scan_type="bootstrap_tags"
        )

        # Verify repository info
        assert repo_audit.repo_identifier == "test-owner/test-repo"
        assert repo_audit.repo_name == "test-repo"
        assert repo_audit.scan_type == "bootstrap_tags"
        assert repo_audit.commits_scanned == 3

        # Should have commit audits
        assert len(repo_audit.commit_audits) == 3

        # Should have aggregated metrics
        assert repo_audit.total_issues >= 0
        assert 0.0 <= repo_audit.avg_quality_score <= 100.0

        # Should have date range
        assert repo_audit.date_range_start is not None
        assert repo_audit.date_range_end is not None

        # Should have processing time
        assert repo_audit.processing_time > 0


def test_audit_repository_quality_trend(
    audit_engine, mock_connector, sample_repo_with_code
):
    """Test quality trend calculation."""
    with patch("src.audit.engine.tempfile.TemporaryDirectory") as mock_temp_dir:
        mock_temp_dir.return_value.__enter__.return_value = str(sample_repo_with_code)
        mock_connector.clone_repository.return_value = str(sample_repo_with_code)

        # Create commits (would need different repos for different trends)
        commits = [
            CommitInfo(
                sha=f"commit{i}",
                message=f"Commit {i}",
                author="Test Author",
                author_email="test@example.com",
                date=datetime(2024, 11, i + 1),
                files_changed=[f"file{i}.py"],
                additions=10,
                deletions=5,
            )
            for i in range(5)
        ]

        repo_audit = audit_engine.audit_repository(
            "test-owner/test-repo", commits
        )

        # Should calculate trend (insufficient data, improving, stable, or declining)
        assert repo_audit.quality_trend in [
            "improving",
            "stable",
            "declining",
            "insufficient_data",
        ]


def test_audit_repository_issues_by_type(
    audit_engine, mock_connector, sample_repo_with_code
):
    """Test issue breakdown by type."""
    with patch("src.audit.engine.tempfile.TemporaryDirectory") as mock_temp_dir:
        mock_temp_dir.return_value.__enter__.return_value = str(sample_repo_with_code)
        mock_connector.clone_repository.return_value = str(sample_repo_with_code)

        commits = [
            CommitInfo(
                sha="abc123",
                message="Test commit",
                author="Test Author",
                author_email="test@example.com",
                date=datetime(2024, 11, 20),
                files_changed=["file.py"],
                additions=10,
                deletions=5,
            )
        ]

        repo_audit = audit_engine.audit_repository("test-owner/test-repo", commits)

        # Should have issues categorized by type
        assert isinstance(repo_audit.issues_by_type, dict)
        # Should have complexity issues from complex.py
        assert repo_audit.issues_by_type.get("complexity", 0) > 0
