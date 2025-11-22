"""Tests for repository merger tool."""

import pytest
import tempfile
from pathlib import Path
from lib.repo_merger import (
    create_merged_repository,
    cleanup_merged_repository,
    get_changed_files_from_diff
)


@pytest.fixture
def base_repo():
    """Fixture providing path to test-app base repository."""
    return str(Path(__file__).parent.parent / "fixtures" / "test-app")


def test_create_merged_repository_with_new_file(base_repo):
    """Test creating merged repo with a new file added."""
    diff = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,3 @@
+# New file
+def hello():
+    return "world"
"""
    
    merged_path = create_merged_repository(base_repo, diff)
    
    try:
        # Verify merged repo exists
        assert Path(merged_path).exists()
        assert Path(merged_path).is_dir()
        
        # Verify new file was created
        new_file = Path(merged_path) / "new_file.py"
        assert new_file.exists()
        
        content = new_file.read_text()
        assert "def hello():" in content
        assert 'return "world"' in content
        
    finally:
        cleanup_merged_repository(merged_path)
    
    # Verify cleanup worked
    assert not Path(merged_path).exists()


def test_create_merged_repository_with_modification(base_repo):
    """Test creating merged repo with file modification."""
    diff = """diff --git a/README.md b/README.md
index abc1234..def5678 100644
--- a/README.md
+++ b/README.md
@@ -1,4 +1,5 @@
 # Code Review Test Fixture
 
+This line was added by PR.
 **Purpose:** Template repository with intentionally bad code for testing AI Code Review Orchestration System.
 
"""

    merged_path = create_merged_repository(base_repo, diff)
    try:
        readme = Path(merged_path) / "README.md"
        assert readme.exists()
        
        content = readme.read_text()
        assert "This line was added by PR." in content
        assert "Code Review Test Fixture" in content  # Original content preserved
        
    finally:
        cleanup_merged_repository(merged_path)


def test_create_merged_repository_preserves_structure(base_repo):
    """Test that merged repo preserves original directory structure."""
    diff = """diff --git a/new_file.py b/new_file.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,2 @@
+# Test
+pass
"""
    
    merged_path = create_merged_repository(base_repo, diff)
    
    try:
        # Check original directories still exist
        assert (Path(merged_path) / "app").exists()
        assert (Path(merged_path) / "tests").exists()
        assert (Path(merged_path) / "app" / "main.py").exists()
        
    finally:
        cleanup_merged_repository(merged_path)


def test_create_merged_repository_invalid_base_path():
    """Test error handling for non-existent base path."""
    diff = "diff --git a/test.py b/test.py\n"
    
    with pytest.raises(ValueError, match="Base repository not found"):
        create_merged_repository("/nonexistent/path", diff)


def test_create_merged_repository_invalid_diff(base_repo):
    """Test error handling for invalid diff that can't be applied."""
    # Diff references non-existent file context
    invalid_diff = """diff --git a/nonexistent.py b/nonexistent.py
index abc1234..def5678 100644
--- a/nonexistent.py
+++ b/nonexistent.py
@@ -100,3 +100,4 @@ def some_function():
     return "value"
+    # Added line
"""
    
    with pytest.raises(RuntimeError, match="Failed to apply patch"):
        create_merged_repository(base_repo, invalid_diff)


def test_cleanup_merged_repository_safety():
    """Test that cleanup only removes temp directories."""
    # Try to cleanup a non-temp path (should be safe no-op)
    cleanup_merged_repository("/usr/bin")
    
    # Verify /usr/bin still exists (wasn't deleted)
    assert Path("/usr/bin").exists()


def test_cleanup_merged_repository_with_none():
    """Test cleanup handles None gracefully."""
    cleanup_merged_repository(None)
    cleanup_merged_repository("")


def test_get_changed_files_from_diff_single_file():
    """Test extracting changed files from diff."""
    diff = """diff --git a/app/main.py b/app/main.py
index abc1234..def5678 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@
+# Modified
 import os
 import sys
 
"""
    
    files = get_changed_files_from_diff(diff)
    assert files == ["app/main.py"]


def test_get_changed_files_from_diff_multiple_files():
    """Test extracting multiple changed files."""
    diff = """diff --git a/app/main.py b/app/main.py
index abc1234..def5678 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,2 +1,3 @@
 import os
+import sys
 
diff --git a/tests/test_main.py b/tests/test_main.py
new file mode 100644
index 0000000..9876543
--- /dev/null
+++ b/tests/test_main.py
@@ -0,0 +1,3 @@
+def test_example():
+    assert True
+
"""

    files = get_changed_files_from_diff(diff)
    assert len(files) == 2
    assert "app/main.py" in files
    assert "tests/test_main.py" in files


def test_merged_repository_is_in_temp_dir(base_repo):
    """Test that merged repo is created in system temp directory."""
    diff = """diff --git a/test.py b/test.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/test.py
@@ -0,0 +1 @@
+# test
"""
    
    merged_path = create_merged_repository(base_repo, diff)
    
    try:
        # Verify it's in temp directory
        assert str(merged_path).startswith(tempfile.gettempdir())
        
    finally:
        cleanup_merged_repository(merged_path)
