"""Demo script to test Analyzer Agent with a real diff."""

import sys
from pathlib import Path

# Add src to path to import directly
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.analyzer import AnalyzerAgent

# Path to test repository
TEST_REPO_PATH = str(Path(__file__).parent / "tests" / "fixtures" / "test-app")


def main():
    """Run analyzer agent on a sample diff with security and complexity issues."""
    
    # Sample diff modifying existing file from test-app
    sample_diff = """diff --git a/app/database.py b/app/database.py
index abc1234..def5678 100644
--- a/app/database.py
+++ b/app/database.py
@@ -50,6 +50,17 @@ def search_users(username: str) -> list:
     return results
 
 
+def execute_raw_query(query: str):
+    \"\"\"🚨 CRITICAL: Execute arbitrary SQL - massive security hole!\"\"\"
+    conn = get_connection()
+    cursor = conn.cursor()
+    # DANGEROUS: Execute user-provided SQL directly
+    cursor.execute(query)
+    conn.commit()
+    results = cursor.fetchall()
+    return results
+
+
 def delete_user(user_id):
     \"\"\"🚨 CRITICAL: SQL injection in DELETE.\"\"\"
     conn = get_connection()
"""
    
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
        print("\n\n📋 DETAILED SECURITY REPORT:")
        print("=" * 80)
        for file_path, sec_result in result["security_issues"].items():
            if sec_result.total_issues > 0:
                from tools.security_scanner import format_security_report
                print(f"\n{file_path}:")
                print(format_security_report(sec_result))
    
    # Print detailed complexity report (if issues found)
    if result["complexity_analysis"]:
        print("\n\n📋 DETAILED COMPLEXITY REPORT:")
        print("=" * 80)
        for file_path, comp_result in result["complexity_analysis"].items():
            if comp_result.high_complexity_count > 0:
                from tools.complexity_analyzer import format_complexity_report
                print(f"\n{file_path}:")
                print(format_complexity_report(comp_result))


if __name__ == "__main__":
    main()
