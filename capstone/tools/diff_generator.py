"""Generate synthetic git diffs from changesets for local testing.

This module creates git-format diffs without requiring actual git operations,
enabling fast unit/integration tests with changeset definitions.
"""

from typing import Optional
from pathlib import Path


def generate_diff(
    operation: str,
    file_path: str,
    new_content: Optional[str] = None,
    patch: Optional[str] = None,
    old_content: Optional[str] = ""
) -> str:
    """Generate git diff format from changeset data.
    
    Args:
        operation: Type of change ("add", "modify", "replace")
        file_path: Path to file being changed
        new_content: Full new content for add/replace operations
        patch: Patch content for modify operations
        old_content: Original content for modify operations
        
    Returns:
        Git diff format string
        
    Example:
        >>> diff = generate_diff(
        ...     operation="add",
        ...     file_path="app/auth.py",
        ...     new_content="def login(): pass"
        ... )
        >>> print(diff)
        diff --git a/app/auth.py b/app/auth.py
        new file mode 100644
        index 0000000..1234567
        --- /dev/null
        +++ b/app/auth.py
        @@ -0,0 +1,1 @@
        +def login(): pass
    """
    if operation == "add":
        return _generate_add_diff(file_path, new_content)
    elif operation == "modify":
        return _generate_modify_diff(file_path, old_content, patch or new_content)
    elif operation == "replace":
        return _generate_replace_diff(file_path, old_content, new_content)
    else:
        raise ValueError(f"Unknown operation: {operation}")


def _generate_add_diff(file_path: str, content: str) -> str:
    """Generate diff for new file addition."""
    lines = content.split("\n")
    diff_lines = [
        f"diff --git a/{file_path} b/{file_path}",
        "new file mode 100644",
        "index 0000000..1234567",
        "--- /dev/null",
        f"+++ b/{file_path}",
        f"@@ -0,0 +1,{len(lines)} @@"
    ]
    
    # Add each line with + prefix
    for line in lines:
        diff_lines.append(f"+{line}")
    
    return "\n".join(diff_lines)


def _generate_modify_diff(
    file_path: str,
    old_content: str,
    new_content: str
) -> str:
    """Generate diff for file modification.
    
    Uses simple line-by-line comparison for synthetic diff.
    Real git diffs would use more sophisticated algorithms.
    """
    old_lines = old_content.split("\n") if old_content else []
    new_lines = new_content.split("\n")
    
    # Simple diff: show old lines as removed, new as added
    diff_lines = [
        f"diff --git a/{file_path} b/{file_path}",
        "index 1234567..abcdefg 100644",
        f"--- a/{file_path}",
        f"+++ b/{file_path}",
        f"@@ -1,{len(old_lines)} +1,{len(new_lines)} @@"
    ]
    
    # Show removed lines
    for line in old_lines:
        diff_lines.append(f"-{line}")
    
    # Show added lines
    for line in new_lines:
        diff_lines.append(f"+{line}")
    
    return "\n".join(diff_lines)


def _generate_replace_diff(
    file_path: str,
    old_content: str,
    new_content: str
) -> str:
    """Generate diff for complete file replacement."""
    return _generate_modify_diff(file_path, old_content, new_content)


def generate_diff_from_changeset(changeset, base_path: Optional[Path] = None) -> str:
    """Generate diff directly from Changeset object.
    
    Args:
        changeset: Changeset instance from changesets.py
        base_path: Optional path to test-fixture for reading old content
        
    Returns:
        Git diff format string
        
    Example:
        >>> from capstone.changesets import CHANGESET_01_SQL_INJECTION
        >>> diff = generate_diff_from_changeset(CHANGESET_01_SQL_INJECTION)
    """
    old_content = ""
    
    # If modifying existing file, try to read original
    if changeset.operation == "modify" and base_path:
        target = base_path / changeset.target_file
        if target.exists():
            old_content = target.read_text()
    
    return generate_diff(
        operation=changeset.operation,
        file_path=changeset.target_file,
        new_content=changeset.new_content,
        patch=changeset.patch,
        old_content=old_content
    )


def generate_all_diffs(base_path: Optional[Path] = None) -> dict[str, str]:
    """Generate diffs for all changesets.
    
    Args:
        base_path: Optional path to test-fixture directory
        
    Returns:
        Dict mapping changeset ID to diff string
        
    Example:
        >>> diffs = generate_all_diffs()
        >>> print(diffs["cs-01-sql-injection"])
    """
    from capstone.changesets import ALL_CHANGESETS
    
    return {
        changeset.id: generate_diff_from_changeset(changeset, base_path)
        for changeset in ALL_CHANGESETS
    }
