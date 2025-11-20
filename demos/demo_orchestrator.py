#!/usr/bin/env python3
"""Demonstration of Orchestrator Agent - complete end-to-end workflow.

This script shows the Orchestrator coordinating all agents:
1. Repository Merger: Creates merged state (base + PR)
2. Analyzer Agent: Security + complexity analysis (parallel)
3. Context Agent: Dependency + impact analysis (parallel)
4. Reporter Agent: Final GitHub-ready review

It demonstrates:
- Complete workflow orchestration
- Parallel execution of Analyzer + Context
- Error handling and graceful degradation
- Performance timing for each stage
- Final GitHub comment generation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.orchestrator import OrchestratorAgent

# Load test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
TEST_APP_DIR = FIXTURES_DIR / "test-app"
DIFF_FILE = FIXTURES_DIR / "diffs" / "complex_pr.diff"


def print_separator(title: str = ""):
    """Print section separator."""
    if title:
        print()
        print("=" * 80)
        print(title.center(80))
        print("=" * 80)
    else:
        print("-" * 80)


def print_timing(result):
    """Print execution timing breakdown."""
    print()
    print_separator("EXECUTION TIMING")
    print()
    print(f"Total Time:      {result.execution_time:.2f}s")
    print(f"  ├─ Analyzer:   {result.analyzer_time:.2f}s")
    print(f"  ├─ Context:    {result.context_time:.2f}s")
    print(f"  └─ Reporter:   {result.reporter_time:.2f}s")
    print()
    
    # Calculate parallel efficiency
    sequential_time = result.analyzer_time + result.context_time + result.reporter_time
    parallel_savings = sequential_time - result.execution_time
    if sequential_time > 0:
        efficiency = (parallel_savings / sequential_time) * 100
        print(f"Sequential would take: {sequential_time:.2f}s")
        print(f"Parallel savings:      {parallel_savings:.2f}s ({efficiency:.1f}% faster)")


def main():
    """Run complete orchestrator demonstration."""
    print_separator("ORCHESTRATOR AGENT DEMONSTRATION")
    print()
    print("This demo shows the complete end-to-end code review workflow:")
    print("  1. Create merged repository (base + PR changes)")
    print("  2. Run Analyzer + Context agents in parallel")
    print("  3. Generate final GitHub review comment")
    print()
    
    # Load test diff
    print("📁 Loading test diff...")
    if not DIFF_FILE.exists():
        print(f"❌ Error: Diff file not found: {DIFF_FILE}")
        print("   Run: python scripts/generate_demo_diff.py")
        sys.exit(1)
    
    with open(DIFF_FILE, 'r') as f:
        diff_text = f.read()
    
    print(f"   ✓ Loaded: {DIFF_FILE.name} ({len(diff_text)} bytes)")
    
    # Verify test-app exists
    if not TEST_APP_DIR.exists():
        print(f"❌ Error: Test app not found: {TEST_APP_DIR}")
        sys.exit(1)
    
    print(f"   ✓ Base repo: {TEST_APP_DIR}")
    print()
    
    # Initialize orchestrator
    print_separator("INITIALIZING ORCHESTRATOR")
    print()
    print("Configuration:")
    print("  - Model: gemini-2.0-flash-exp")
    print("  - Max Retries: 2")
    print("  - Timeout: 120s")
    print()
    
    orchestrator = OrchestratorAgent(
        model_name="gemini-2.0-flash-exp",
        max_retries=2,
        timeout=120
    )
    
    # PR metadata
    pr_metadata = {
        "pr_number": 123,
        "author": "developer",
        "title": "Add database query improvements",
        "files_changed": 2,
        "additions": 45,
        "deletions": 12
    }
    
    print_separator("EXECUTING CODE REVIEW WORKFLOW")
    print()
    
    # Execute orchestrated review
    result = orchestrator.review_pull_request(
        diff_text=diff_text,
        base_repo_path=str(TEST_APP_DIR),
        pr_metadata=pr_metadata
    )
    
    print()
    
    # Check result
    if not result.success:
        print_separator("❌ REVIEW FAILED")
        print()
        print(f"Error: {result.error}")
        print()
        print_timing(result)
        sys.exit(1)
    
    # Display timing
    print_timing(result)
    
    # Display final report
    print()
    print_separator("FINAL GITHUB REVIEW COMMENT")
    print()
    
    github_comment = orchestrator.reporter.format_as_github_comment(result.report)
    print(github_comment)
    
    # Display verdict details
    print()
    print_separator("REVIEW VERDICT")
    print()
    print(f"Overall Verdict: {result.report.overall_verdict}")
    print()
    
    verdict_emoji = {
        "APPROVE": "✅",
        "COMMENT": "💬",
        "REQUEST_CHANGES": "🚫"
    }
    
    emoji = verdict_emoji.get(result.report.overall_verdict, "❓")
    print(f"{emoji} {result.report.overall_verdict}")
    print()
    
    if result.report.overall_verdict == "REQUEST_CHANGES":
        print("Critical issues detected - changes required before merge")
    elif result.report.overall_verdict == "COMMENT":
        print("Medium-priority issues - review recommended")
    else:
        print("No issues detected - ready to merge")
    
    # Architecture summary
    print()
    print_separator("ARCHITECTURE SUMMARY")
    print()
    print("Workflow:")
    print("  1. Repository Merger    → Created merged state for analysis")
    print("  2. Analyzer Agent       → Security + Complexity (parallel)")
    print("  3. Context Agent        → Dependencies + Impact (parallel)")
    print("  4. Reporter Agent       → Combined findings + verdict")
    print()
    print("Key Features:")
    print("  ✓ Parallel execution (Analyzer + Context)")
    print("  ✓ Automatic retry on failures")
    print("  ✓ Graceful degradation (agents can fail independently)")
    print("  ✓ GitHub-ready markdown output")
    print("  ✓ Verdict-based recommendations")
    print()
    
    # Test with different scenarios
    print_separator("TESTING ERROR HANDLING")
    print()
    print("Scenario: Invalid diff")
    
    orchestrator_test = OrchestratorAgent(max_retries=1)
    test_result = orchestrator_test.review_pull_request(
        diff_text="invalid diff",
        base_repo_path=str(TEST_APP_DIR)
    )
    
    if not test_result.success:
        print(f"  ✓ Handled gracefully: {test_result.error[:80]}...")
    else:
        print("  ⚠️  Unexpectedly succeeded")
    
    print()
    print_separator("DEMONSTRATION COMPLETE")
    print()
    print("Summary:")
    print(f"  • Total execution: {result.execution_time:.2f}s")
    print(f"  • Verdict: {result.report.overall_verdict}")
    print(f"  • All agents coordinated successfully")
    print()
    print("Next Steps:")
    print("  • Add Memory Bank for pattern recognition")
    print("  • Integrate GitHub API for live PR reviews")
    print("  • Deploy as production service")
    print()


if __name__ == "__main__":
    main()
