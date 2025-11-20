#!/usr/bin/env python3
"""Demonstration of Reporter Agent capabilities.

This script shows how the Reporter Agent combines findings from the Analyzer
and Context agents to generate a comprehensive code review report with an
overall verdict.

It demonstrates:
- Combining security, complexity, and context findings
- Verdict determination logic (APPROVE/COMMENT/REQUEST_CHANGES)
- GitHub-compatible markdown formatting
- Prioritization by severity
"""

import sys
from pathlib import Path
from pprint import pprint

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.reporter import ReporterAgent
from tools.security_scanner import SecurityScanResult, SecurityIssue
from tools.complexity_analyzer import CodeComplexityResult, FunctionComplexity
from tools.dependency_analyzer import ImpactAnalysis


def create_sample_findings():
    """Create sample findings from Analyzer and Context agents."""
    
    # Sample security findings (from Analyzer Agent)
    security_issues = {
        "app/database.py": SecurityScanResult(
            issues=[
                SecurityIssue(
                    issue_severity="HIGH",
                    issue_confidence="HIGH",
                    issue_text="Possible SQL injection vulnerability - parameterize this query using placeholders",
                    test_id="B608",
                    test_name="hardcoded_sql_expressions",
                    line_number=47,
                    line_range=[47, 47],
                    code="query = f\"SELECT * FROM users WHERE id={user_id}\"",
                    cwe_id="CWE-89"
                ),
                SecurityIssue(
                    issue_severity="HIGH",
                    issue_confidence="HIGH",
                    issue_text="SQL injection - string interpolation used in raw SQL query",
                    test_id="B608",
                    test_name="hardcoded_sql_expressions",
                    line_number=52,
                    line_range=[52, 52],
                    code="query = \"DELETE FROM sessions WHERE user_id = %s\" % user_id",
                    cwe_id="CWE-89"
                ),
                SecurityIssue(
                    issue_severity="MEDIUM",
                    issue_confidence="MEDIUM",
                    issue_text="Use of assert detected. The enclosed code will be removed when compiling to optimized byte code",
                    test_id="B101",
                    test_name="assert_used",
                    line_number=61,
                    line_range=[61, 61],
                    code="assert user_id is not None"
                )
            ],
            high_severity_count=2,
            medium_severity_count=1,
            low_severity_count=0,
            total_issues=3
        ),
        "app/auth.py": SecurityScanResult(
            issues=[
                SecurityIssue(
                    issue_severity="MEDIUM",
                    issue_confidence="HIGH",
                    issue_text="Standard pseudo-random generators are not suitable for security/cryptographic purposes",
                    test_id="B311",
                    test_name="blacklist",
                    line_number=23,
                    line_range=[23, 23],
                    code="token = random.randint(100000, 999999)",
                    cwe_id="CWE-330"
                )
            ],
            high_severity_count=0,
            medium_severity_count=1,
            low_severity_count=0,
            total_issues=1
        )
    }
    
    # Sample complexity findings (from Analyzer Agent)
    complexity_analysis = {
        "app/database.py": CodeComplexityResult(
            functions=[
                FunctionComplexity(
                    name="process_user_action",
                    lineno=75,
                    col_offset=0,
                    endline=120,
                    cyclomatic_complexity=23,
                    complexity_rank="D"
                ),
                FunctionComplexity(
                    name="execute_raw_query",
                    lineno=45,
                    col_offset=0,
                    endline=65,
                    cyclomatic_complexity=8,
                    complexity_rank="B"
                )
            ],
            average_complexity=15.5,
            total_complexity=31,
            high_complexity_count=1,
            maintainability_index=48.2
        )
    }
    
    # Sample context/impact analysis (from Context Agent)
    impact_analysis = ImpactAnalysis(
        changed_modules=["app/database.py"],
        affected_modules=["app.services.user_service", "app.api.users", "app.tasks.cleanup"],
        breaking_changes=[
            "Function signature changed: execute_raw_query() now requires 'params' argument"
        ],
        risk_level="medium"
    )
    
    # AI recommendations from Context Agent
    ai_insights = """Based on the dependency analysis:

1. The changes to execute_raw_query() will affect 3 modules that import this function
2. Breaking change detected: new required parameter may break existing callers
3. Consider adding deprecation warnings before removing old signature
4. High-complexity function process_user_action() should be refactored into smaller units
5. SQL injection vulnerabilities need immediate attention - use parameterized queries
6. Recommend adding integration tests for database.py changes"""
    
    return security_issues, complexity_analysis, impact_analysis, ai_insights


def main():
    """Run Reporter Agent demonstration."""
    print("=" * 80)
    print("REPORTER AGENT DEMONSTRATION")
    print("=" * 80)
    print()
    
    # Create sample findings
    print("Creating sample findings from Analyzer and Context agents...")
    security_issues, complexity_analysis, impact_analysis, ai_insights = create_sample_findings()
    print()
    
    # Initialize Reporter Agent
    reporter = ReporterAgent()
    
    # Generate comprehensive report
    print("Generating comprehensive code review report...")
    print()
    
    analyzer_results = {
        "security_issues": security_issues,
        "complexity_analysis": complexity_analysis
    }
    
    context_results = {
        "impact_analysis": impact_analysis,
        "ai_insights": ai_insights
    }
    
    pr_metadata = {
        "pr_number": 123,
        "author": "developer",
        "title": "Add SQL query execution improvements",
        "files_changed": 2
    }
    
    report = reporter.generate_report(analyzer_results, context_results, pr_metadata)
    
    # Display report structure
    print("REPORT STRUCTURE:")
    print("-" * 80)
    print(f"Overall Verdict: {report.overall_verdict}")
    print(f"Summary: {report.summary}")
    print()
    
    # Format as GitHub comment
    print("=" * 80)
    print("FORMATTED GITHUB COMMENT:")
    print("=" * 80)
    print()
    github_comment = reporter.format_as_github_comment(report)
    print(github_comment)
    print()
    
    # Show verdict determination logic
    print("=" * 80)
    print("VERDICT DETERMINATION:")
    print("=" * 80)
    print()
    print(f"Verdict: {report.overall_verdict}")
    print()
    print("Logic:")
    print("- High severity issues: 2 (in security)")
    print("- Breaking changes: 1 (in context)")
    print("- Result: REQUEST_CHANGES (critical issues or breaking changes detected)")
    print()
    print("Verdict rules:")
    print("  REQUEST_CHANGES: high_severity_count > 0 OR breaking_changes detected")
    print("  COMMENT: medium_severity_count > 0 OR risk_level == 'high'")
    print("  APPROVE: otherwise")
    print()
    
    # Test different scenarios
    print("=" * 80)
    print("TESTING DIFFERENT SCENARIOS:")
    print("=" * 80)
    print()
    
    # Scenario 1: Clean code
    print("Scenario 1: Clean code (should APPROVE)")
    clean_analyzer = {
        "security_issues": {},
        "complexity_analysis": {}
    }
    clean_context = {
        "impact_analysis": ImpactAnalysis(
            changed_modules=[],
            affected_modules=[],
            breaking_changes=[],
            risk_level="low"
        ),
        "ai_insights": "No issues detected. Code looks good."
    }
    clean_report = reporter.generate_report(clean_analyzer, clean_context, pr_metadata)
    print(f"Verdict: {clean_report.overall_verdict}")
    print()
    
    # Scenario 2: Medium issues only
    print("Scenario 2: Medium severity issues only (should COMMENT)")
    medium_security = {
        "app/test.py": SecurityScanResult(
            issues=[
                SecurityIssue(
                    issue_severity="MEDIUM",
                    issue_confidence="MEDIUM",
                    issue_text="Medium issue",
                    test_id="B201",
                    test_name="test",
                    line_number=10,
                    line_range=[10, 10],
                    code="code()"
                )
            ],
            high_severity_count=0,
            medium_severity_count=1,
            low_severity_count=0,
            total_issues=1
        )
    }
    medium_analyzer = {
        "security_issues": medium_security,
        "complexity_analysis": {}
    }
    medium_context = {
        "impact_analysis": ImpactAnalysis(
            changed_modules=[],
            affected_modules=[],
            breaking_changes=[],
            risk_level="low"
        ),
        "ai_insights": "Minor concerns only."
    }
    medium_report = reporter.generate_report(medium_analyzer, medium_context, pr_metadata)
    print(f"Verdict: {medium_report.overall_verdict}")
    print()
    
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
