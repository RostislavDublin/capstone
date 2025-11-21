"""Unit tests for GitHub connector."""

import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.connectors.github import GitHubConnector


@pytest.fixture
def mock_github_client():
    """Mock PyGithub client."""
    with patch("src.connectors.github.Github") as mock:
        yield mock


@pytest.fixture
def connector(mock_github_client):
    """Create GitHubConnector with mocked client."""
    return GitHubConnector(token="test_token")


def test_get_repository_info(connector, mock_github_client):
    """Test repository metadata retrieval."""
    mock_repo = Mock()
    mock_repo.full_name = "test-owner/test-repo"
    mock_repo.owner.login = "test-owner"
    mock_repo.name = "test-repo"
    mock_repo.description = "Test repository"
    mock_repo.default_branch = "main"
    mock_repo.created_at = datetime(2024, 1, 1)
    mock_repo.language = "Python"
    mock_repo.get_topics.return_value = ["testing", "quality"]

    connector._client.get_repo.return_value = mock_repo

    info = connector.get_repository_info("test-owner/test-repo")

    assert info.full_name == "test-owner/test-repo"
    assert info.owner == "test-owner"
    assert info.name == "test-repo"
    assert info.description == "Test repository"
    assert info.default_branch == "main"
    assert info.language == "Python"
    assert info.topics == ["testing", "quality"]


def test_list_commits(connector, mock_github_client):
    """Test commit listing with date filtering."""
    mock_repo = Mock()
    mock_repo.default_branch = "main"

    # Mock commit objects
    mock_commit1 = Mock()
    mock_commit1.sha = "abc123"
    mock_commit1.commit.message = "Fix bug"
    mock_commit1.commit.author.name = "Alice"
    mock_commit1.commit.author.email = "alice@example.com"
    mock_commit1.commit.author.date = datetime(2024, 11, 20)
    mock_commit1.stats.additions = 10
    mock_commit1.stats.deletions = 5
    mock_commit1.files = [Mock(filename="file1.py"), Mock(filename="file2.py")]

    mock_commit2 = Mock()
    mock_commit2.sha = "def456"
    mock_commit2.commit.message = "Add feature"
    mock_commit2.commit.author.name = "Bob"
    mock_commit2.commit.author.email = "bob@example.com"
    mock_commit2.commit.author.date = datetime(2024, 11, 19)
    mock_commit2.stats.additions = 20
    mock_commit2.stats.deletions = 2
    mock_commit2.files = [Mock(filename="file3.py")]

    mock_repo.get_commits.return_value = [mock_commit1, mock_commit2]
    connector._client.get_repo.return_value = mock_repo

    commits = connector.list_commits("test-owner/test-repo")

    assert len(commits) == 2
    assert commits[0].sha == "abc123"
    assert commits[0].message == "Fix bug"
    assert commits[0].author == "Alice"
    assert commits[0].files_changed == ["file1.py", "file2.py"]
    assert commits[0].additions == 10
    assert commits[0].deletions == 5

    assert commits[1].sha == "def456"
    assert commits[1].author == "Bob"


def test_list_commits_with_date_filter(connector, mock_github_client):
    """Test commit listing with since/until dates."""
    mock_repo = Mock()
    mock_repo.default_branch = "main"
    mock_repo.get_commits.return_value = []
    connector._client.get_repo.return_value = mock_repo

    since = datetime(2024, 11, 1)
    until = datetime(2024, 11, 20)

    connector.list_commits("test-owner/test-repo", since=since, until=until)

    mock_repo.get_commits.assert_called_once_with(
        sha="main", since=since, until=until
    )


def test_list_tags(connector, mock_github_client):
    """Test tag/release listing."""
    mock_repo = Mock()

    # Mock tag objects
    mock_tag1 = Mock()
    mock_tag1.name = "v2.0.0"
    mock_tag1.commit.sha = "xyz789"

    mock_tag2 = Mock()
    mock_tag2.name = "v1.0.0"
    mock_tag2.commit.sha = "uvw456"

    mock_repo.get_tags.return_value = [mock_tag1, mock_tag2]

    # Mock commit details for dates
    mock_commit1 = Mock()
    mock_commit1.commit.author.date = datetime(2024, 11, 15)
    mock_commit1.commit.message = "Release 2.0.0"

    mock_commit2 = Mock()
    mock_commit2.commit.author.date = datetime(2024, 10, 1)
    mock_commit2.commit.message = "Release 1.0.0"

    mock_repo.get_commit.side_effect = [mock_commit1, mock_commit2]
    connector._client.get_repo.return_value = mock_repo

    tags = connector.list_tags("test-owner/test-repo")

    assert len(tags) == 2
    # Should be sorted newest first
    assert tags[0].name == "v2.0.0"
    assert tags[0].sha == "xyz789"
    assert tags[0].date == datetime(2024, 11, 15)
    assert tags[0].message == "Release 2.0.0"

    assert tags[1].name == "v1.0.0"
    assert tags[1].date == datetime(2024, 10, 1)


@patch("src.connectors.github.requests")
def test_get_commit_diff(mock_requests, connector, mock_github_client):
    """Test commit diff retrieval."""
    mock_response = Mock()
    mock_response.text = "diff --git a/file.py b/file.py\n..."
    mock_requests.get.return_value = mock_response

    diff = connector.get_commit_diff("test-owner/test-repo", "abc123")

    assert diff == "diff --git a/file.py b/file.py\n..."
    mock_response.raise_for_status.assert_called_once()


@patch("src.connectors.github.subprocess")
@patch("src.connectors.github.Path")
def test_clone_repository(mock_path, mock_subprocess, connector, mock_github_client):
    """Test repository cloning."""
    mock_repo = Mock()
    mock_repo.clone_url = "https://github.com/test-owner/test-repo.git"
    connector._client.get_repo.return_value = mock_repo

    mock_target = Mock()
    mock_target.absolute.return_value = "/tmp/test-repo"
    mock_path.return_value = mock_target

    path = connector.clone_repository("test-owner/test-repo", "/tmp/test-repo")

    assert path == "/tmp/test-repo"
    mock_target.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    assert mock_subprocess.run.call_count == 1  # Only clone, no checkout


@patch("src.connectors.github.subprocess")
@patch("src.connectors.github.Path")
def test_clone_repository_with_sha(
    mock_path, mock_subprocess, connector, mock_github_client
):
    """Test repository cloning at specific commit."""
    mock_repo = Mock()
    mock_repo.clone_url = "https://github.com/test-owner/test-repo.git"
    connector._client.get_repo.return_value = mock_repo

    mock_target = Mock()
    mock_target.absolute.return_value = "/tmp/test-repo"
    mock_path.return_value = mock_target

    path = connector.clone_repository(
        "test-owner/test-repo", "/tmp/test-repo", sha="abc123"
    )

    assert path == "/tmp/test-repo"
    assert mock_subprocess.run.call_count == 2  # Clone + checkout
