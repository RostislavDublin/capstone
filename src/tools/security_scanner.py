"""Security vulnerability scanner using bandit library."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from bandit.core import manager as bandit_manager
from bandit.core import config as bandit_config


@dataclass
class SecurityIssue:
    """Represents a detected security vulnerability."""

    issue_severity: str  # HIGH, MEDIUM, LOW
    issue_confidence: str  # HIGH, MEDIUM, LOW
    issue_text: str
    test_id: str  # Bandit test ID (e.g., B201)
    test_name: str
    line_number: int
    line_range: List[int]
    code: str
    cwe_id: Optional[str] = None
    more_info: Optional[str] = None


@dataclass
class SecurityScanResult:
    """Results from security scan."""

    issues: List[SecurityIssue]
    high_severity_count: int
    medium_severity_count: int
    low_severity_count: int
    total_issues: int


def detect_security_issues(code: str, language: str = "python") -> SecurityScanResult:
    """Detect security vulnerabilities in code using bandit.

    Args:
        code: Source code to analyze
        language: Programming language (currently only 'python' supported)

    Returns:
        SecurityScanResult with detected issues

    Raises:
        ValueError: If code is empty or language not supported
    """
    if not code or not code.strip():
        raise ValueError("code cannot be empty")

    if language.lower() != "python":
        raise ValueError(f"Language '{language}' not supported. Only 'python' is supported.")

    # Create temporary file for bandit to analyze
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    try:
        # Initialize bandit manager with default config
        config = bandit_config.BanditConfig()
        bandit_mgr = bandit_manager.BanditManager(
            config=config, agg_type="file", debug=False, verbose=False
        )

        # Discover and run tests on the temporary file
        bandit_mgr.discover_files([tmp_file_path])
        bandit_mgr.run_tests()

        # Extract results
        issues = []
        high_count = 0
        medium_count = 0
        low_count = 0

        for result in bandit_mgr.results:
            severity = result.severity

            # Count by severity
            if severity == "HIGH":
                high_count += 1
            elif severity == "MEDIUM":
                medium_count += 1
            elif severity == "LOW":
                low_count += 1

            # Create SecurityIssue
            issue = SecurityIssue(
                issue_severity=severity,
                issue_confidence=result.confidence,
                issue_text=result.text,
                test_id=result.test_id,
                test_name=result.test,
                line_number=result.lineno,
                line_range=result.linerange,
                code=result.get_code(),
                cwe_id=result.cwe.id if hasattr(result, "cwe") and result.cwe else None,
                more_info=None,
            )
            issues.append(issue)

        return SecurityScanResult(
            issues=issues,
            high_severity_count=high_count,
            medium_severity_count=medium_count,
            low_severity_count=low_count,
            total_issues=len(issues),
        )

    finally:
        # Clean up temporary file
        Path(tmp_file_path).unlink(missing_ok=True)
