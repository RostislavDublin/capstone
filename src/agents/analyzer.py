"""Analyzer Agent - intelligent code analysis agent using ADK.

This agent analyzes pull requests by:
1. Parsing git diffs to extract changes
2. Running security scans on added code
3. Analyzing code complexity
4. Using Gemini to synthesize findings and provide recommendations
"""

from google import genai
from google.genai import types

from tools.diff_parser import parse_git_diff, get_added_code_blocks, get_modified_files_content
from tools.security_scanner import detect_security_issues, format_security_report
from tools.complexity_analyzer import calculate_complexity, format_complexity_report


class AnalyzerAgent:
    """Intelligent code analysis agent using Google ADK."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """Initialize the analyzer agent.
        
        Args:
            model_name: Gemini model to use (flash for speed, pro for complexity)
        """
        self.client = genai.Client()
        self.model_name = model_name
        
    def analyze_pull_request(self, diff_text: str, base_repo_path: str = None) -> dict:
        """Analyze a pull request and provide intelligent recommendations.
        
        Args:
            diff_text: Git unified diff of the PR changes
            base_repo_path: Path to base repository for applying diffs (optional)
            
        Returns:
            dict with analysis results including:
                - diff_analysis: Parsed diff information
                - security_issues: Security vulnerabilities found
                - complexity_analysis: Code complexity metrics
                - ai_recommendations: Gemini's intelligent synthesis
                - summary: Human-readable summary
        """
        # Step 1: Parse the diff
        print("📊 Step 1: Parsing git diff...")
        diff_analysis = parse_git_diff(diff_text)
        print(f"   Found {diff_analysis.modified_files} modified files, "
              f"{diff_analysis.total_additions} additions, "
              f"{diff_analysis.total_deletions} deletions")
        
        # Step 2: Get full file contents after applying diff
        print("\n🔍 Step 2: Applying diff to get full file contents...")
        if base_repo_path:
            # Apply diff to base repository
            modified_files = get_modified_files_content(diff_text, base_repo_path)
            print(f"   Extracted {len(modified_files)} complete files")
        else:
            # Fallback: just extract added code
            added_code = get_added_code_blocks(diff_analysis)
            modified_files = {path: '\n'.join(lines) for path, lines in added_code.items()}
            print(f"   Extracted {len(modified_files)} files (added code only)")
        
        # Step 3: Security analysis
        print("\n🔒 Step 3: Running security analysis...")
        security_results = {}
        total_security_issues = 0
        
        for file_path, code in modified_files.items():
            if not code.strip():
                continue
            try:
                result = detect_security_issues(code, "python")
                security_results[file_path] = result
                total_security_issues += result.total_issues
                if result.total_issues > 0:
                    print(f"   ⚠️  {file_path}: {result.total_issues} issues "
                          f"(H:{result.high_severity_count} M:{result.medium_severity_count} L:{result.low_severity_count})")
            except Exception as e:
                print(f"   ⚠️  {file_path}: Security scan failed - {e}")
        
        if total_security_issues == 0:
            print("   ✅ No security issues detected")
        
        # Step 4: Complexity analysis
        print("\n📈 Step 4: Analyzing code complexity...")
        complexity_results = {}
        high_complexity_count = 0
        
        for file_path, code in modified_files.items():
            if not code.strip():
                continue
            try:
                result = calculate_complexity(code, "python")
                complexity_results[file_path] = result
                high_complexity_count += result.high_complexity_count
                if result.high_complexity_count > 0:
                    print(f"   ⚠️  {file_path}: {result.high_complexity_count} high-complexity functions "
                          f"(avg: {result.average_complexity})")
            except Exception as e:
                # Ignore syntax errors in complexity analysis (might be incomplete code in diff)
                pass
        
        if high_complexity_count == 0:
            print("   ✅ No high-complexity functions detected")
        
        # Step 5: AI synthesis with Gemini
        print("\n🤖 Step 5: Generating AI recommendations...")
        ai_recommendations = self._generate_recommendations(
            diff_analysis, security_results, complexity_results
        )
        
        # Step 6: Create summary
        summary = self._create_summary(
            diff_analysis, total_security_issues, high_complexity_count, ai_recommendations
        )
        
        return {
            "diff_analysis": diff_analysis,
            "security_issues": security_results,
            "complexity_analysis": complexity_results,
            "ai_recommendations": ai_recommendations,
            "summary": summary
        }
    
    def _generate_recommendations(
        self, 
        diff_analysis, 
        security_results: dict, 
        complexity_results: dict
    ) -> str:
        """Use Gemini to generate intelligent recommendations.
        
        Args:
            diff_analysis: Parsed diff information
            security_results: Security scan results
            complexity_results: Complexity analysis results
            
        Returns:
            AI-generated recommendations
        """
        # Prepare context for Gemini
        context_parts = []
        
        # Diff summary
        context_parts.append("Code Changes Summary:")
        context_parts.append(f"- Modified files: {diff_analysis.modified_files}")
        context_parts.append(f"- New files: {diff_analysis.new_files}")
        context_parts.append(f"- Lines added: {diff_analysis.total_additions}")
        context_parts.append(f"- Lines removed: {diff_analysis.total_deletions}")
        context_parts.append("")
        
        # Security issues
        total_security = sum(r.total_issues for r in security_results.values())
        if total_security > 0:
            context_parts.append("Security Issues Found:")
            for file_path, result in security_results.items():
                if result.total_issues > 0:
                    context_parts.append(f"\n{file_path}:")
                    for issue in result.issues[:3]:  # Top 3 issues per file
                        context_parts.append(
                            f"  - [{issue.issue_severity}] {issue.issue_text} "
                            f"(line {issue.line_number}, {issue.test_id})"
                        )
            context_parts.append("")
        
        # Complexity issues
        total_high_complexity = sum(r.high_complexity_count for r in complexity_results.values())
        if total_high_complexity > 0:
            context_parts.append("High Complexity Functions:")
            for file_path, result in complexity_results.items():
                high_funcs = [f for f in result.functions if f.complexity_rank in ('D', 'E', 'F')]
                if high_funcs:
                    context_parts.append(f"\n{file_path}:")
                    for func in high_funcs[:3]:  # Top 3 per file
                        context_parts.append(
                            f"  - {func.name}: complexity {func.cyclomatic_complexity} "
                            f"(rank {func.complexity_rank})"
                        )
            context_parts.append("")
        
        # If no issues found, add positive note
        if total_security == 0 and total_high_complexity == 0:
            context_parts.append("✅ No security issues or high-complexity functions detected.")
            context_parts.append("The code changes appear clean from automated analysis perspective.")
        
        context = "\n".join(context_parts)
        
        # Gemini prompt
        prompt = f"""You are an expert code reviewer. Analyze the following code review results and provide:

1. Key findings (2-3 sentences)
2. Critical issues that must be addressed (if any)
3. Recommendations for improvement (3-5 specific, actionable items)
4. Overall assessment (APPROVE / REQUEST_CHANGES / COMMENT)

Be concise, specific, and focus on the most important issues.

{context}

Provide your analysis:"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,  # Lower temperature for consistent, factual analysis
                    max_output_tokens=800
                )
            )
            return response.text
        except Exception as e:
            return f"AI recommendation generation failed: {e}"
    
    def _create_summary(
        self,
        diff_analysis,
        total_security_issues: int,
        high_complexity_count: int,
        ai_recommendations: str
    ) -> str:
        """Create human-readable summary of analysis.
        
        Args:
            diff_analysis: Parsed diff information
            total_security_issues: Total number of security issues
            high_complexity_count: Number of high-complexity functions
            ai_recommendations: AI-generated recommendations
            
        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 80,
            "CODE REVIEW ANALYSIS",
            "=" * 80,
            "",
            "📊 Changes:",
            f"   • {diff_analysis.modified_files} files modified",
            f"   • {diff_analysis.new_files} new files",
            f"   • +{diff_analysis.total_additions} / -{diff_analysis.total_deletions} lines",
            "",
            f"🔒 Security: {total_security_issues} issues found",
            f"📈 Complexity: {high_complexity_count} high-complexity functions",
            "",
            "🤖 AI Recommendations:",
            "─" * 80,
            ai_recommendations,
            "",
            "=" * 80,
        ]
        
        return "\n".join(lines)
