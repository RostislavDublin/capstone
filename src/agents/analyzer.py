"""Analyzer agent for code review on PRs."""

from dataclasses import dataclass
from typing import List, Dict, Optional

from src.github.context import PRContext, FileChange
from src.tools.security_scanner import detect_security_issues, SecurityIssue
from src.tools.complexity_analyzer import calculate_complexity, FunctionComplexity


@dataclass
class ReviewFinding:
    """A single code review finding."""

    severity: str  # CRITICAL, MAJOR, MINOR
    category: str  # security, complexity, style, etc.
    message: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class AnalyzerResult:
    """Result from Analyzer agent."""

    findings: List[ReviewFinding]
    files_analyzed: int
    critical_count: int
    major_count: int
    minor_count: int


class AnalyzerAgent:
    """Analyzes PR code changes for security and complexity issues."""

    def __init__(self):
        """Initialize Analyzer agent."""
        pass

    def analyze(self, pr_context: PRContext) -> AnalyzerResult:
        """Analyze PR for code quality issues.

        Args:
            pr_context: Complete PR context with files and diffs

        Returns:
            AnalyzerResult with all findings
        """
        findings = []

        # Analyze each Python file
        python_files = [f for f in pr_context.files if f.filename.endswith(".py")]

        for file in python_files:
            # Skip deleted files
            if file.status == "removed":
                continue

            # Extract full file content from patch
            full_code = self._extract_file_content(file)
            if not full_code:
                continue

            # Run security scan
            try:
                security_findings = self._analyze_security(file.filename, full_code)
                findings.extend(security_findings)
            except Exception as e:
                # Log error but continue
                print(f"Security scan failed for {file.filename}: {e}")

            # Run complexity analysis
            try:
                complexity_findings = self._analyze_complexity(file.filename, full_code)
                findings.extend(complexity_findings)
            except Exception as e:
                # Log error but continue
                print(f"Complexity analysis failed for {file.filename}: {e}")

        # Count by severity
        critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
        major_count = sum(1 for f in findings if f.severity == "MAJOR")
        minor_count = sum(1 for f in findings if f.severity == "MINOR")

        return AnalyzerResult(
            findings=findings,
            files_analyzed=len(python_files),
            critical_count=critical_count,
            major_count=major_count,
            minor_count=minor_count,
        )

    def _extract_file_content(self, file: FileChange) -> Optional[str]:
        """Extract full file content from patch.

        For new files: reconstruct from added lines
        For modified files: reconstruct from patch (added + context lines)
        """
        if not file.patch:
            return None

        lines = []
        for line in file.patch.split("\n"):
            # Skip diff headers
            if line.startswith("@@") or line.startswith("+++") or line.startswith("---"):
                continue
            # Include added and context lines (not removed)
            if not line.startswith("-"):
                # Remove leading + if present
                clean_line = line[1:] if line.startswith("+") else line
                lines.append(clean_line)

        return "\n".join(lines)

    def _analyze_security(self, file_path: str, code: str) -> List[ReviewFinding]:
        """Analyze code for security vulnerabilities."""
        findings = []

        result = detect_security_issues(code, language="python")

        for issue in result.issues:
            # Map bandit severity to our severity levels
            if issue.issue_severity == "HIGH":
                severity = "CRITICAL"
            elif issue.issue_severity == "MEDIUM":
                severity = "MAJOR"
            else:
                severity = "MINOR"

            finding = ReviewFinding(
                severity=severity,
                category="security",
                message=f"{issue.test_name}: {issue.issue_text}",
                file_path=file_path,
                line_number=issue.line_number,
                code_snippet=issue.code,
                suggestion=f"Review security issue: {issue.test_id}",
            )
            findings.append(finding)

        return findings

    def _analyze_complexity(self, file_path: str, code: str) -> List[ReviewFinding]:
        """Analyze code for complexity issues."""
        findings = []

        result = calculate_complexity(code, language="python")

        # Report high complexity functions (D, E, F ranks)
        for func in result.functions:
            if func.complexity_rank in ("D", "E", "F"):
                # Map complexity rank to severity
                if func.complexity_rank == "F":
                    severity = "MAJOR"
                elif func.complexity_rank == "E":
                    severity = "MAJOR"
                else:  # D
                    severity = "MINOR"

                message = (
                    f"Function `{func.name}` has high cyclomatic complexity "
                    f"({func.cyclomatic_complexity}, rank {func.complexity_rank})"
                )

                suggestion = (
                    "Consider refactoring to reduce complexity. "
                    "Break down into smaller functions or simplify control flow."
                )

                finding = ReviewFinding(
                    severity=severity,
                    category="complexity",
                    message=message,
                    file_path=file_path,
                    line_number=func.lineno,
                    code_snippet=None,
                    suggestion=suggestion,
                )
                findings.append(finding)

        return findings
