"""Audit engine that analyzes complete repository state at a commit."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from audit_models import CommitAudit, FileAudit
from connectors.base import CommitInfo, RepositoryConnector
from lib.complexity_analyzer import calculate_complexity
from lib.security_scanner import detect_security_issues


class AuditEngine:
    """Analyzes complete repository state at specific commits.
    
    Unlike PR reviewers that analyze diffs, this engine clones the repository
    at a specific commit SHA and analyzes the ENTIRE codebase to get
    comprehensive quality metrics.
    """

    def __init__(
        self,
        connector: RepositoryConnector,
        temp_dir: Optional[str] = None,
    ):
        """Initialize audit engine.

        Args:
            connector: Repository connector (GitHub, GitLab, etc.)
            temp_dir: Optional temporary directory for clones (default: system temp)
        """
        self.connector = connector
        self.temp_dir = temp_dir or tempfile.gettempdir()

    def audit_commit(
        self,
        repo_identifier: str,
        commit: CommitInfo,
    ) -> CommitAudit:
        """Audit repository state at a specific commit.

        Args:
            repo_identifier: Repository identifier (e.g., "owner/repo")
            commit: Commit information

        Returns:
            CommitAudit with security and complexity findings
        """
        # Create temporary directory for this audit
        with tempfile.TemporaryDirectory(dir=self.temp_dir) as clone_dir:
            # Clone repository at specific commit
            repo_path = self.connector.clone_repository(
                repo_identifier, clone_dir, sha=commit.sha
            )

            # Find all Python files in repository
            python_files = self._find_python_files(repo_path)

            # Analyze each file separately (NEW: per-file audits)
            file_audits = []
            for py_file in python_files:
                file_audit = self._audit_single_file(py_file, repo_path)
                if file_audit:  # Skip files that failed to analyze
                    file_audits.append(file_audit)

            # Aggregate metrics from file audits
            all_security_issues = []
            all_complexity_issues = []
            total_complexity = 0.0
            max_complexity = 0.0
            total_function_count = 0

            for file_audit in file_audits:
                all_security_issues.extend(file_audit.security_issues)
                all_complexity_issues.extend(file_audit.complexity_issues)
                total_complexity += file_audit.avg_complexity * file_audit.function_count
                max_complexity = max(max_complexity, file_audit.max_complexity)
                total_function_count += file_audit.function_count

            # Calculate commit-level metrics
            avg_complexity = (
                total_complexity / total_function_count if total_function_count > 0 else 0.0
            )
            security_score = self._calculate_security_score(all_security_issues)
            quality_score = self._calculate_quality_score(
                security_score, avg_complexity, len(all_complexity_issues)
            )

            # Count issues by severity
            critical_count = sum(
                1 for issue in all_security_issues if issue["severity"] == "critical"
            )
            high_count = sum(
                1 for issue in all_security_issues if issue["severity"] == "high"
            ) + sum(1 for issue in all_complexity_issues if issue["severity"] == "high")
            medium_count = sum(
                1 for issue in all_security_issues if issue["severity"] == "medium"
            ) + sum(1 for issue in all_complexity_issues if issue["severity"] == "medium")
            low_count = sum(
                1 for issue in all_security_issues if issue["severity"] == "low"
            ) + sum(1 for issue in all_complexity_issues if issue["severity"] == "low")

            return CommitAudit(
                repository=repo_identifier,
                commit_sha=commit.sha,
                commit_message=commit.message,
                author=commit.author,
                author_email=commit.author_email,
                date=commit.date,
                files_changed=commit.files_changed,
                files=file_audits,  # NEW: per-file audits
                security_issues=all_security_issues,
                security_score=security_score,
                complexity_issues=all_complexity_issues,
                avg_complexity=avg_complexity,
                max_complexity=max_complexity,
                total_issues=len(all_security_issues) + len(all_complexity_issues),
                critical_issues=critical_count,
                high_issues=high_count,
                medium_issues=medium_count,
                low_issues=low_count,
                quality_score=quality_score,
            )

    def _audit_single_file(self, file_path: Path, repo_root: str) -> Optional[FileAudit]:
        """Audit a single file.

        Args:
            file_path: Path to Python file
            repo_root: Root of repository (for relative path calculation)

        Returns:
            FileAudit object or None if file couldn't be analyzed
        """
        try:
            code = file_path.read_text()
            
            # Get relative path from repo root
            relative_path = str(file_path.relative_to(repo_root))
            
            # Analyze security
            security_result = detect_security_issues(code)
            security_issues = []
            for issue in security_result.issues:
                security_issues.append({
                    "type": "security",
                    "severity": issue.issue_severity.lower(),
                    "message": issue.issue_text,
                    "line": issue.line_number,
                    "file": relative_path,
                    "test_id": issue.test_id,
                    "cwe_id": issue.cwe_id,
                })
            
            # Analyze complexity
            complexity_result = calculate_complexity(code)
            complexity_issues = []
            total_complexity = 0.0
            max_complexity_val = 0.0
            function_count = len(complexity_result.functions)
            
            for func in complexity_result.functions:
                complexity = func.cyclomatic_complexity
                total_complexity += complexity
                max_complexity_val = max(max_complexity_val, complexity)
                
                # Flag high complexity
                if complexity > 10:
                    severity = self._get_complexity_severity(complexity)
                    complexity_issues.append({
                        "type": "complexity",
                        "severity": severity,
                        "message": f"High complexity function '{func.name}' (complexity: {complexity})",
                        "line": func.lineno,
                        "file": relative_path,
                    })
            
            # Calculate file metrics
            avg_complexity_val = total_complexity / function_count if function_count > 0 else 0.0
            lines_of_code = len(code.splitlines())
            
            # Count issues by severity
            critical_count = sum(1 for i in security_issues if i["severity"] == "critical")
            high_count = sum(1 for i in security_issues if i["severity"] == "high") + \
                        sum(1 for i in complexity_issues if i["severity"] == "high")
            medium_count = sum(1 for i in security_issues if i["severity"] == "medium") + \
                          sum(1 for i in complexity_issues if i["severity"] == "medium")
            low_count = sum(1 for i in security_issues if i["severity"] == "low") + \
                       sum(1 for i in complexity_issues if i["severity"] == "low")
            
            # Calculate scores
            security_score = self._calculate_security_score(security_issues)
            quality_score = self._calculate_quality_score(
                security_score, avg_complexity_val, len(complexity_issues)
            )
            
            return FileAudit(
                file_path=relative_path,
                security_issues=security_issues,
                security_score=security_score,
                complexity_issues=complexity_issues,
                avg_complexity=avg_complexity_val,
                max_complexity=max_complexity_val,
                function_count=function_count,
                lines_of_code=lines_of_code,
                total_issues=len(security_issues) + len(complexity_issues),
                critical_issues=critical_count,
                high_issues=high_count,
                medium_issues=medium_count,
                low_issues=low_count,
                quality_score=quality_score,
            )
        except Exception:
            # Skip files that can't be analyzed
            return None

    def _get_complexity_severity(self, complexity: float) -> str:
        """Determine severity based on complexity value.

        Args:
            complexity: Cyclomatic complexity value

        Returns:
            Severity string
        """
        if complexity > 20:
            return "critical"
        elif complexity > 15:
            return "high"
        elif complexity > 10:
            return "medium"
        else:
            return "low"

    def _find_python_files(self, repo_path: str) -> List[Path]:
        """Find all Python files in repository.

        Args:
            repo_path: Path to cloned repository

        Returns:
            List of Python file paths
        """
        repo = Path(repo_path)
        python_files = []

        # Exclude common non-source directories
        exclude_dirs = {
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            "env",
            "node_modules",
            ".tox",
            "build",
            "dist",
            ".eggs",
        }

        for py_file in repo.rglob("*.py"):
            # Skip excluded directories
            if any(excluded in py_file.parts for excluded in exclude_dirs):
                continue
            python_files.append(py_file)

        return python_files

    def _create_complexity_issue(self, func_data, file_path: Path) -> dict:
        """Create CodeIssue from complexity analysis result.

        Args:
            func_data: FunctionComplexity object
            file_path: Path to source file

        Returns:
            CodeIssue dict
        """
        complexity = func_data.cyclomatic_complexity

        # Determine severity based on complexity
        if complexity > 20:
            severity = "critical"
        elif complexity > 15:
            severity = "high"
        elif complexity > 10:
            severity = "medium"
        else:
            severity = "low"

        return {
            "type": "complexity",
            "severity": severity,
            "message": f"High complexity function '{func_data.name}' (complexity: {complexity})",
            "line": func_data.lineno,
            "file": str(file_path),
        }

    def _calculate_security_score(self, issues: List) -> float:
        """Calculate security score (100 = perfect, 0 = terrible).

        Args:
            issues: List of issue dicts with severity field

        Returns:
            Security score between 0 and 100
        """
        if not issues:
            return 100.0

        # Weight issues by severity
        penalty = 0.0
        for issue in issues:
            severity = issue["severity"]
            if severity == "critical":
                penalty += 20.0
            elif severity == "high":
                penalty += 10.0
            elif severity == "medium":
                penalty += 5.0
            elif severity == "low":
                penalty += 1.0

        return max(0.0, 100.0 - penalty)

    def _calculate_quality_score(
        self, security_score: float, avg_complexity: float, high_complexity_count: int
    ) -> float:
        """Calculate overall quality score.

        Args:
            security_score: Security score (0-100)
            avg_complexity: Average cyclomatic complexity
            high_complexity_count: Number of high complexity functions

        Returns:
            Quality score between 0 and 100
        """
        # Start with security score (weighted 60%)
        score = security_score * 0.6

        # Add complexity score (weighted 40%)
        complexity_penalty = 0.0
        if avg_complexity > 10:
            complexity_penalty += (avg_complexity - 10) * 2
        complexity_penalty += high_complexity_count * 3

        complexity_score = max(0.0, 100.0 - complexity_penalty)
        score += complexity_score * 0.4

        return round(score, 2)
