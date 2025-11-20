"""Context Agent - analyzes code context and dependencies.

This agent provides:
- Dependency analysis (what modules are affected)
- Breaking change detection
- Integration risk assessment
- Memory-based pattern recognition
"""

from google import genai
from google.genai import types

from tools.dependency_analyzer import (
    analyze_impact,
    build_dependency_graph,
    format_impact_report,
    ImpactAnalysis
)


class ContextAgent:
    """Agent for analyzing code context and dependencies."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """Initialize context agent.
        
        Args:
            model_name: Gemini model to use
        """
        self.client = genai.Client()
        self.model_name = model_name
        
    def analyze_context(
        self,
        repo_path: str,
        changed_files: list[str],
        old_versions: dict[str, str] | None = None
    ) -> dict:
        """Analyze code context and dependencies.
        
        Args:
            repo_path: Path to repository (merged state)
            changed_files: List of changed file paths
            old_versions: Optional dict of old file contents
            
        Returns:
            dict with:
                - impact_analysis: ImpactAnalysis object
                - dependency_graph: Dict of file dependencies
                - ai_insights: Gemini's context analysis
                - summary: Human-readable summary
        """
        print("📊 Step 1: Analyzing dependencies...")
        
        # Build dependency graph
        dep_graph = build_dependency_graph(repo_path, changed_files)
        print(f"   Found {len(dep_graph)} Python modules with dependencies")
        
        # Analyze impact
        print("🔍 Step 2: Assessing impact and risk...")
        impact = analyze_impact(repo_path, changed_files, old_versions)
        
        print(f"   Risk Level: {impact.risk_level.upper()}")
        print(f"   Affected Modules: {len(impact.affected_modules)}")
        if impact.breaking_changes:
            print(f"   ⚠️  Breaking Changes: {len(impact.breaking_changes)}")
        
        # Generate AI insights about context
        print("🤖 Step 3: Generating AI context insights...")
        ai_insights = self._generate_context_insights(impact, dep_graph)
        
        # Create summary
        summary = self._create_summary(impact, dep_graph)
        
        return {
            "impact_analysis": impact,
            "dependency_graph": dep_graph,
            "ai_insights": ai_insights,
            "summary": summary
        }
    
    def _generate_context_insights(
        self,
        impact: ImpactAnalysis,
        dep_graph: dict
    ) -> str:
        """Generate AI insights about code context using Gemini.
        
        Args:
            impact: Impact analysis results
            dep_graph: Dependency graph
            
        Returns:
            AI-generated context insights
        """
        # Prepare context for Gemini
        context_info = f"""
Analyze the following code change context:

Risk Level: {impact.risk_level}
Changed Modules: {len(impact.changed_modules)}
Affected Modules: {len(impact.affected_modules)}
Breaking Changes: {len(impact.breaking_changes)}

Changed Files:
{chr(10).join(f"- {f}" for f in impact.changed_modules)}

"""
        
        if impact.affected_modules:
            context_info += f"\nAffected Modules:\n"
            context_info += "\n".join(f"- {m}" for m in impact.affected_modules[:5])
            if len(impact.affected_modules) > 5:
                context_info += f"\n... and {len(impact.affected_modules) - 5} more"
        
        if impact.breaking_changes:
            context_info += f"\n\nBreaking Changes:\n"
            context_info += "\n".join(f"- {c}" for c in impact.breaking_changes)
        
        # Add dependency information
        if dep_graph:
            context_info += f"\n\nDependency Summary:\n"
            for file_path, dep_info in dep_graph.items():
                if dep_info.external_deps:
                    context_info += f"\n{file_path} depends on:\n"
                    context_info += "\n".join(f"  - {d}" for d in dep_info.external_deps[:5])
        
        prompt = f"""You are a senior code reviewer analyzing the impact of code changes.

{context_info}

Provide insights about:
1. Integration Risks: What could break when these changes are deployed?
2. Dependencies: Are the dependency changes reasonable? Any concerns?
3. Testing Strategy: What should be tested given these changes?
4. Deployment Considerations: Any special considerations for deployment?

Focus on practical, actionable insights."""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1000
                )
            )
            return response.text
        except Exception as e:
            return f"Error generating AI insights: {e}"
    
    def _create_summary(
        self,
        impact: ImpactAnalysis,
        dep_graph: dict
    ) -> str:
        """Create human-readable summary of context analysis.
        
        Args:
            impact: Impact analysis
            dep_graph: Dependency graph
            
        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 80,
            "CONTEXT ANALYSIS",
            "=" * 80,
            "",
            f"📊 Changes Overview:",
            f"   • {len(impact.changed_modules)} files modified",
            f"   • {len(impact.affected_modules)} modules potentially affected",
            f"   • Risk Level: {impact.risk_level.upper()}",
            ""
        ]
        
        if impact.breaking_changes:
            lines.append(f"⚠️  Breaking Changes: {len(impact.breaking_changes)} detected")
            for change in impact.breaking_changes[:3]:
                lines.append(f"   • {change}")
            if len(impact.breaking_changes) > 3:
                lines.append(f"   ... and {len(impact.breaking_changes) - 3} more")
            lines.append("")
        
        # Dependency summary
        if dep_graph:
            total_imports = sum(len(d.imports) for d in dep_graph.values())
            total_external = sum(len(d.external_deps) for d in dep_graph.values())
            lines.append(f"📦 Dependencies:")
            lines.append(f"   • {total_imports} total imports")
            lines.append(f"   • {total_external} external dependencies")
            lines.append("")
        
        return "\n".join(lines)
