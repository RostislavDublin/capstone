"""Fixture commits for deterministic testing.

Each module defines:
- COMMIT_MESSAGE: Git commit message
- AUTHOR, AUTHOR_EMAIL: Commit author
- DIFF: Git unified diff
- FILES_CHANGED: List of changed files
- ADDITIONS, DELETIONS: Change stats
"""

__all__ = [
    "commit_01_add_logging",
    "commit_02_fix_sql_injection",
    "commit_03_add_password_validation",
    "commit_04_refactor_config",
    "commit_05_add_validation",
]
