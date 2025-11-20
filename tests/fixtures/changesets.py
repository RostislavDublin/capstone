"""Unified changeset definitions for local and remote testing.

Each changeset represents a specific code change that introduces documented issues.
Changesets are used for:
- Local unit/integration testing (synthetic diffs)
- Remote E2E testing (actual PRs on GitHub)
- Sequential learning tests (Memory Bank evaluation)
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class IssueCategory(str, Enum):
    """Issue categories for changesets."""
    SECURITY = "security"
    COMPLEXITY = "complexity"
    STYLE = "style"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    CLEAN = "clean"  # Control - no issues


class ExpectedIssue(BaseModel):
    """Expected issue to be detected in changeset."""
    type: str = Field(description="Issue type (sql_injection, high_complexity, etc)")
    severity: str = Field(description="critical, high, medium, low")
    file_path: str = Field(description="File where issue appears")
    line_start: Optional[int] = Field(default=None, description="Starting line")
    line_end: Optional[int] = Field(default=None, description="Ending line")
    description: str = Field(description="What the issue is")
    must_detect: bool = Field(default=True, description="Critical for test to pass")


class Changeset(BaseModel):
    """Definition of a code change with expected issues.
    
    Used across all testing modes:
    - Local: generates synthetic diff
    - Remote: creates PR branch
    - Sequential: applies in order for learning tests
    """
    
    id: str = Field(description="Unique changeset identifier")
    name: str = Field(description="Human-readable name")
    category: IssueCategory = Field(description="Primary category")
    difficulty: str = Field(description="easy, medium, hard, critical")
    
    # What changes
    target_file: str = Field(description="File to modify (relative to test-fixture/)")
    operation: str = Field(description="add, modify, replace")
    new_content: Optional[str] = Field(default=None, description="New file content (for add/replace)")
    patch: Optional[str] = Field(default=None, description="Diff patch (for modify)")
    
    # Expected outcomes
    expected_issues: List[ExpectedIssue] = Field(description="Issues that should be detected")
    
    # PR metadata (for remote testing)
    pr_title: str = Field(description="PR title when deployed")
    pr_body: str = Field(description="PR description")
    branch_name: str = Field(description="Branch name for PR")
    
    # Test criteria
    min_issues_to_detect: int = Field(description="Minimum issues agent must find")
    max_false_positives: int = Field(description="Maximum allowed false positives")
    target_processing_time: float = Field(default=15.0, description="Target time in seconds")


# =============================================================================
# CHANGESET DEFINITIONS
# =============================================================================

CHANGESET_01_SQL_INJECTION = Changeset(
    id="cs-01-sql-injection",
    name="Add SQL Injection Vulnerability",
    category=IssueCategory.SECURITY,
    difficulty="critical",
    target_file="app/auth.py",
    operation="add",
    new_content='''"""User authentication with security issues."""

from app.database import get_connection


def login(username: str, password: str) -> bool:
    """🚨 CRITICAL: SQL injection + plaintext password storage!"""
    conn = get_connection()
    
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor = conn.cursor()
    cursor.execute(query)
    user = cursor.fetchone()
    
    return user is not None


def create_user(username: str, password: str, email: str):
    """🚨 CRITICAL: Stores password in plaintext!"""
    conn = get_connection()
    # No password hashing!
    query = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password}', '{email}')"
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
''',
    expected_issues=[
        ExpectedIssue(
            type="sql_injection",
            severity="critical",
            file_path="app/auth.py",
            line_start=10,
            line_end=10,
            description="SQL injection via f-string in login query",
            must_detect=True
        ),
        ExpectedIssue(
            type="plaintext_credentials",
            severity="critical",
            file_path="app/auth.py",
            line_start=22,
            line_end=22,
            description="Password stored in plaintext without hashing",
            must_detect=True
        )
    ],
    pr_title="Add user authentication",
    pr_body="""## Changes
- Added login functionality
- Added user registration

## Expected Issues (for testing)
🚨 **CRITICAL (2):**
- SQL injection in `login()` function (line 10)
- Password stored in plaintext (line 22)
""",
    branch_name="feature/user-authentication",
    min_issues_to_detect=2,
    max_false_positives=0
)


CHANGESET_02_HIGH_COMPLEXITY = Changeset(
    id="cs-02-high-complexity",
    name="Add Highly Complex Function",
    category=IssueCategory.COMPLEXITY,
    difficulty="high",
    target_file="app/utils.py",
    operation="modify",
    patch='''@@ -100,0 +101,40 @@ def calculateTotalPrice(items: List[Dict]) -> float:
+
+
+def transform_and_aggregate(records: List[Dict], filters: Dict) -> Dict:
+    """⚠️ HIGH COMPLEXITY: Cyclomatic complexity = 25
+    
+    Duplicate logic from process_data but with more nesting.
+    """
+    output = {"processed": [], "errors": []}
+    
+    if records:
+        for record in records:
+            if record.get("type") == "transaction":
+                if "amount" in record:
+                    amount = record["amount"]
+                    if amount > 0:
+                        if filters.get("min_amount"):
+                            if amount >= filters["min_amount"]:
+                                if filters.get("max_amount"):
+                                    if amount <= filters["max_amount"]:
+                                        if filters.get("currency_filter"):
+                                            if record.get("currency") == filters["currency_filter"]:
+                                                output["processed"].append(record)
+                                        else:
+                                            output["processed"].append(record)
+                                else:
+                                    output["processed"].append(record)
+                        else:
+                            output["processed"].append(record)
+                    else:
+                        output["errors"].append({"record": record, "error": "negative amount"})
+                else:
+                    output["errors"].append({"record": record, "error": "missing amount"})
+            elif record.get("type") == "refund":
+                if "amount" in record:
+                    amount = abs(record["amount"])
+                    if filters.get("include_refunds", True):
+                        output["processed"].append(record)
+    
+    return output
''',
    expected_issues=[
        ExpectedIssue(
            type="high_complexity",
            severity="high",
            file_path="app/utils.py",
            line_start=104,
            line_end=140,
            description="Cyclomatic complexity 25 exceeds threshold of 10",
            must_detect=True
        ),
        ExpectedIssue(
            type="deep_nesting",
            severity="high",
            file_path="app/utils.py",
            description="7 levels of nested conditionals",
            must_detect=True
        ),
        ExpectedIssue(
            type="duplicate_code",
            severity="medium",
            file_path="app/utils.py",
            description="Logic duplicates existing process_data function",
            must_detect=False
        )
    ],
    pr_title="Add advanced data processing",
    pr_body="""## Changes
- Added `transform_and_aggregate()` function for financial data

## Expected Issues (for testing)
⚠️ **HIGH (3):**
- Cyclomatic complexity 25 (threshold: 10)
- Nested conditionals 7 levels deep
- Duplicate logic with existing `process_data()`
""",
    branch_name="feature/data-processing",
    min_issues_to_detect=2,
    max_false_positives=1
)


CHANGESET_03_STYLE_VIOLATIONS = Changeset(
    id="cs-03-style-violations",
    name="Add Code with Style Issues",
    category=IssueCategory.STYLE,
    difficulty="medium",
    target_file="app/api_helpers.py",
    operation="add",
    new_content='''"""API helper functions with style violations."""

def ValidateUserInput(userInput, validationRules):  # Wrong naming convention
    """Missing docstring details, no type hints"""
    if userInput==None: return False  # Bad formatting, multiple statements
    # Line too long - exceeds 120 characters by a lot for no good reason and could be split
    isValid=True;resultMessages=[];errorCount=0  # Multiple statements, semicolons, bad names
    
    for ruleName in validationRules:
        if ruleName=="required": isValid=isValid and userInput!=""
        elif ruleName=="email": isValid=isValid and "@" in userInput
        
    return isValid


class APIresponseFormatter:  # Wrong naming
    def FormatJSON(self,data,includeMetadata=True,includeTimestamp=True):  # Bad spacing
        import datetime  # Import inside function
        response={"data":data}
        if includeMetadata:response["metadata"]={"version":"1.0"}
        if includeTimestamp:response["timestamp"]=str(datetime.datetime.now())
        return response
''',
    expected_issues=[
        ExpectedIssue(
            type="naming_convention",
            severity="medium",
            file_path="app/api_helpers.py",
            line_start=3,
            description="PascalCase function name (should be snake_case)",
            must_detect=True
        ),
        ExpectedIssue(
            type="missing_type_hints",
            severity="low",
            file_path="app/api_helpers.py",
            description="No type hints on function parameters",
            must_detect=False
        ),
        ExpectedIssue(
            type="line_length",
            severity="low",
            file_path="app/api_helpers.py",
            line_start=6,
            description="Line exceeds 120 character limit",
            must_detect=False
        )
    ],
    pr_title="Refactor API helper utilities",
    pr_body="""## Changes
- Added input validation helpers
- Added response formatting class

## Expected Issues (for testing)
💡 **MEDIUM (8):**
- PascalCase function names (should be snake_case)
- Missing docstrings
- No type hints
- Lines > 120 characters
""",
    branch_name="feature/api-refactor",
    min_issues_to_detect=3,
    max_false_positives=2
)


CHANGESET_04_CLEAN_CODE = Changeset(
    id="cs-04-clean-code",
    name="Add Clean, Well-Written Code",
    category=IssueCategory.CLEAN,
    difficulty="easy",
    target_file="app/logger.py",
    operation="add",
    new_content='''"""Logging configuration and utilities.

This module provides centralized logging setup for the application.
All functions follow best practices and coding standards.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None
) -> logging.Logger:
    """Configure and return a logger instance.
    
    Args:
        name: Logger name, typically __name__
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Format with timestamp and level
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
''',
    expected_issues=[],  # Control - should find NO issues
    pr_title="Add logging infrastructure",
    pr_body="""## Changes
- Added centralized logging configuration
- Well-documented functions with type hints
- Follows Python best practices

## Expected Issues (for testing)
✅ **NONE** - This is a control PR to validate false positive rate.
""",
    branch_name="feature/logging",
    min_issues_to_detect=0,
    max_false_positives=0
)


# =============================================================================
# CHANGESET REGISTRY
# =============================================================================

ALL_CHANGESETS = [
    CHANGESET_01_SQL_INJECTION,
    CHANGESET_02_HIGH_COMPLEXITY,
    CHANGESET_03_STYLE_VIOLATIONS,
    CHANGESET_04_CLEAN_CODE,
]

CHANGESETS_BY_ID = {cs.id: cs for cs in ALL_CHANGESETS}

CHANGESETS_BY_CATEGORY = {
    IssueCategory.SECURITY: [CHANGESET_01_SQL_INJECTION],
    IssueCategory.COMPLEXITY: [CHANGESET_02_HIGH_COMPLEXITY],
    IssueCategory.STYLE: [CHANGESET_03_STYLE_VIOLATIONS],
    IssueCategory.CLEAN: [CHANGESET_04_CLEAN_CODE],
}


def get_changeset(changeset_id: str) -> Changeset:
    """Get changeset by ID."""
    if changeset_id not in CHANGESETS_BY_ID:
        raise ValueError(f"Unknown changeset: {changeset_id}")
    return CHANGESETS_BY_ID[changeset_id]


def get_changesets_by_category(category: IssueCategory) -> List[Changeset]:
    """Get all changesets in category."""
    return CHANGESETS_BY_CATEGORY.get(category, [])
