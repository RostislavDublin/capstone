"""Demo script to test Context Agent."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.context import ContextAgent

# Paths
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
TEST_REPO_PATH = str(FIXTURES_DIR / "test-app")


def main():
    """Run context agent on sample changes."""
    
    print("🚀 Initializing Context Agent...")
    agent = ContextAgent(model_name="gemini-2.0-flash-exp")
    
    print("\n" + "=" * 80)
    print("ANALYZING CODE CONTEXT")
    print("=" * 80 + "\n")
    
    # Simulate changed files (from our complex_pr.diff)
    changed_files = ["app/database.py"]
    
    # Run context analysis
    result = agent.analyze_context(
        repo_path=TEST_REPO_PATH,
        changed_files=changed_files
    )
    
    # Print summary
    print("\n" + result["summary"])
    
    # Print impact analysis
    from tools.dependency_analyzer import format_impact_report
    print("\n" + format_impact_report(result["impact_analysis"]))
    
    # Print dependency graph
    print("\n" + "=" * 80)
    print("DEPENDENCY DETAILS")
    print("=" * 80)
    for file_path, dep_info in result["dependency_graph"].items():
        print(f"\n📄 {file_path}")
        if dep_info.imports:
            print(f"   Imports: {', '.join(dep_info.imports)}")
        if dep_info.exports:
            print(f"   Exports: {', '.join(dep_info.exports[:5])}")
            if len(dep_info.exports) > 5:
                print(f"           ... and {len(dep_info.exports) - 5} more")
        if dep_info.external_deps:
            print(f"   External: {', '.join(dep_info.external_deps)}")
    
    # Print AI insights
    print("\n" + "=" * 80)
    print("AI CONTEXT INSIGHTS")
    print("=" * 80)
    print(result["ai_insights"])


if __name__ == "__main__":
    main()
