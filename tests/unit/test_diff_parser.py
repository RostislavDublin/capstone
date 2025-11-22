"""Unit tests for diff parser tool."""

import pytest
from lib.diff_parser import (
    parse_git_diff,
    get_added_code_blocks,
    DiffAnalysis,
    FileChange
)


def test_parse_simple_diff():
    """Test parsing a simple one-file diff."""
    diff = """diff --git a/app.py b/app.py
index 1234567..abcdefg 100644
--- a/app.py
+++ b/app.py
@@ -1,4 +1,4 @@
 def query_database(user_id):
     connection = get_db_connection()
-    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
+    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
     return cursor.fetchall()
"""
    
    result = parse_git_diff(diff)
    
    assert isinstance(result, DiffAnalysis)
    assert result.modified_files == 1
    assert result.total_additions == 1
    assert result.total_deletions == 1
    assert result.new_files == 0
    assert result.deleted_files == 0
    
    assert len(result.files_changed) == 1
    file_change = result.files_changed[0]
    assert file_change.path == "app.py"
    assert file_change.added_lines == 1
    assert file_change.removed_lines == 1
    assert not file_change.is_new_file
    assert not file_change.is_deleted_file


def test_parse_new_file():
    """Test parsing diff with new file creation."""
    diff = """diff --git a/new_module.py b/new_module.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/new_module.py
@@ -0,0 +1,3 @@
+def hello():
+    print("Hello, World!")
+    return True
"""
    
    result = parse_git_diff(diff)
    
    assert result.new_files == 1
    assert result.modified_files == 1
    assert result.total_additions == 3
    
    file_change = result.files_changed[0]
    assert file_change.is_new_file
    assert file_change.path == "new_module.py"


def test_parse_empty_diff_raises_error():
    """Test that empty diff raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_git_diff("")
    
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_git_diff("   \n  \n")


def test_parse_invalid_diff_returns_empty_analysis():
    """Test that invalid diff format returns empty analysis (unidiff behavior)."""
    result = parse_git_diff("This is not a valid diff format")
    assert result.modified_files == 0
    assert result.total_additions == 0
    assert result.total_deletions == 0
    assert len(result.files_changed) == 0


def test_get_added_code_blocks():
    """Test extraction of added code blocks."""
    diff = """diff --git a/api.py b/api.py
index 1234567..abcdefg 100644
--- a/api.py
+++ b/api.py
@@ -1,3 +1,6 @@
 def process_data():
     pass
 
+def new_function(x):
+    return x * 2
+
"""
    
    result = parse_git_diff(diff)
    code_blocks = get_added_code_blocks(result)
    
    assert "api.py" in code_blocks
    added_lines = code_blocks["api.py"]
    assert len(added_lines) == 3
    assert any("def new_function" in line for line in added_lines)


def test_parse_multiple_files():
    """Test parsing diff with multiple files."""
    diff = """diff --git a/file1.py b/file1.py
index 1234567..abcdefg 100644
--- a/file1.py
+++ b/file1.py
@@ -1,1 +1,2 @@
 print("file1")
+print("added line")
diff --git a/file2.py b/file2.py
index 7654321..gfedcba 100644
--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,2 @@
 print("file2")
+print("another addition")
"""
    
    result = parse_git_diff(diff)
    
    assert result.modified_files == 2
    assert result.total_additions == 2
    assert len(result.files_changed) == 2
    
    paths = [f.path for f in result.files_changed]
    assert "file1.py" in paths
    assert "file2.py" in paths


def test_parse_with_context_lines():
    """Test that context lines are captured correctly."""
    diff = """diff --git a/utils.py b/utils.py
index 1234567..abcdefg 100644
--- a/utils.py
+++ b/utils.py
@@ -1,5 +1,6 @@
 def calculate(x, y):
     # This is context
     result = x + y
+    result = result * 2
     # More context
     return result
"""
    
    result = parse_git_diff(diff)
    file_change = result.files_changed[0]
    
    assert len(file_change.hunks) == 1
    hunk = file_change.hunks[0]
    
    assert len(hunk['added_lines']) == 1
    assert len(hunk['context_lines']) > 0
    assert hunk['added_lines'][0]['content'] == "    result = result * 2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
