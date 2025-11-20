"""Demo script to test Analyzer Agent with a real diff."""

import sys
from pathlib import Path

# Add src to path to import directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.analyzer import AnalyzerAgent

# Paths
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
TEST_REPO_PATH = str(FIXTURES_DIR / "test-app")
SAMPLE_DIFF_PATH = FIXTURES_DIR / "diffs" / "complex_pr.diff"


def main():
    """Run analyzer agent on a sample diff with security and complexity issues."""
    
    # Load diff from fixture
    if not SAMPLE_DIFF_PATH.exists():
        print(f"Error: Diff fixture not found: {SAMPLE_DIFF_PATH}")
        print("Run: python tests/fixtures/_generate_diffs.py")
        sys.exit(1)
    
    sample_diff = SAMPLE_DIFF_PATH.read_text()
    
    print("🚀 Initializing Analyzer Agent...")
    agent = AnalyzerAgent(model_name="gemini-2.0-flash-exp")
    
    print("\n" + "=" * 80)
    print("ANALYZING PULL REQUEST")
    print("=" * 80 + "\n")
    
    # Run analysis with base repository
    result = agent.analyze_pull_request(sample_diff, base_repo_path=TEST_REPO_PATH)
    
    # Print summary
    print("\n" + result["summary"])
    
    # Print detailed security report (if issues found)
    if result["security_issues"]:
        print("\n\nDETAILED SECURITY REPORT:")
        print("=" * 80)
        for file_path, sec_result in result["security_issues"].items():
            if sec_result.total_issues > 0:
                from tools.security_scanner import format_security_report
                print(f"\n{file_path}:")
                print(format_security_report(sec_result))
    
    # Print detailed complexity report (if issues found)
    if result["complexity_analysis"]:
        print("\n\nDETAILED COMPLEXITY REPORT:")
        print("=" * 80)
        for file_path, comp_result in result["complexity_analysis"].items():
            if comp_result.high_complexity_count > 0:
                from tools.complexity_analyzer import format_complexity_report
                print(f"\n{file_path}:")
                print(format_complexity_report(comp_result))


if __name__ == "__main__":
    main()
