"""Format review findings as inline GitHub review comments."""

from typing import List, Dict
from src.agents.analyzer import ReviewFinding


def format_inline_comment(finding: ReviewFinding) -> str:
    """Format a single finding as markdown comment.

    Args:
        finding: ReviewFinding to format

    Returns:
        Markdown-formatted comment text
    """
    # Severity emoji
    emoji_map = {
        "CRITICAL": "🚨",
        "MAJOR": "⚠️",
        "MINOR": "ℹ️",
    }
    emoji = emoji_map.get(finding.severity, "💡")

    lines = [
        f"{emoji} **{finding.severity}** ({finding.category})",
        "",
        finding.message,
    ]

    if finding.code_snippet:
        lines.extend(["", "```python", finding.code_snippet.strip(), "```"])

    if finding.suggestion:
        lines.extend(["", f"**Suggestion:** {finding.suggestion}"])

    return "\n".join(lines)


def group_findings_by_file(findings: List[ReviewFinding]) -> Dict[str, List[ReviewFinding]]:
    """Group findings by file path.

    Args:
        findings: List of review findings

    Returns:
        Dict mapping file paths to list of findings
    """
    grouped: Dict[str, List[ReviewFinding]] = {}

    for finding in findings:
        if finding.file_path not in grouped:
            grouped[finding.file_path] = []
        grouped[finding.file_path].append(finding)

    return grouped


def format_summary_comment(
    findings: List[ReviewFinding], files_analyzed: int
) -> str:
    """Format overall review summary as PR comment.

    Args:
        findings: All review findings
        files_analyzed: Number of files analyzed

    Returns:
        Markdown-formatted summary
    """
    if not findings:
        return (
            "## ✅ Code Review Complete\n\n"
            f"Analyzed {files_analyzed} file(s). No issues found!"
        )

    # Count by severity
    critical = sum(1 for f in findings if f.severity == "CRITICAL")
    major = sum(1 for f in findings if f.severity == "MAJOR")
    minor = sum(1 for f in findings if f.severity == "MINOR")

    # Group by category
    by_category: Dict[str, int] = {}
    for finding in findings:
        by_category[finding.category] = by_category.get(finding.category, 0) + 1

    lines = [
        "## 🤖 Code Review Complete",
        "",
        f"**Files Analyzed:** {files_analyzed}",
        f"**Total Issues:** {len(findings)}",
        "",
        "### Issues by Severity",
        f"- 🚨 Critical: {critical}",
        f"- ⚠️ Major: {major}",
        f"- ℹ️ Minor: {minor}",
        "",
        "### Issues by Category",
    ]

    for category, count in sorted(by_category.items()):
        lines.append(f"- {category.capitalize()}: {count}")

    lines.extend(
        [
            "",
            "---",
            "*Review comments posted inline on affected lines.*",
        ]
    )

    return "\n".join(lines)
