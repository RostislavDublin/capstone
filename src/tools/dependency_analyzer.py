"""Dependency analyzer - builds dependency graph from code changes.

Analyzes code to understand:
- Import dependencies (what modules does this code use)
- Export surface (what functions/classes are exposed)
- Affected modules (what could break if this changes)
"""

import ast
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass


@dataclass
class DependencyInfo:
    """Information about a module's dependencies."""
    
    module_path: str
    imports: List[str]  # Modules this file imports
    exports: List[str]  # Functions/classes this file exports
    external_deps: List[str]  # Third-party dependencies
    


@dataclass
class ImpactAnalysis:
    """Analysis of how changes affect the codebase."""
    
    changed_modules: List[str]
    affected_modules: List[str]  # Modules that import changed modules
    breaking_changes: List[str]  # Detected signature changes
    risk_level: str  # "low", "medium", "high"


def analyze_dependencies(code: str, file_path: str) -> DependencyInfo:
    """Analyze dependencies in Python code using AST.
    
    Args:
        code: Source code to analyze
        file_path: Path to the file (for context)
        
    Returns:
        DependencyInfo with imports and exports
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Invalid Python syntax in {file_path}: {e}")
    
    imports = []
    exports = []
    external_deps = []
    
    # Extract imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                imports.append(module_name)
                if not module_name.startswith('.'):
                    external_deps.append(module_name)
                    
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
                # External deps: not relative (level=0) and not standard lib
                if node.level == 0:  # Absolute import
                    external_deps.append(node.module)
    
    # Extract exports (top-level functions and classes)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith('_'):  # Public functions
                exports.append(f"function:{node.name}")
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith('_'):  # Public classes
                exports.append(f"class:{node.name}")
    
    return DependencyInfo(
        module_path=file_path,
        imports=sorted(set(imports)),
        exports=sorted(set(exports)),
        external_deps=sorted(set(external_deps))
    )


def build_dependency_graph(repo_path: str, changed_files: List[str]) -> Dict[str, DependencyInfo]:
    """Build dependency graph for changed files.
    
    Args:
        repo_path: Path to repository root
        changed_files: List of changed file paths (relative to repo)
        
    Returns:
        Dict mapping file paths to their dependency info
    """
    repo = Path(repo_path)
    dependency_graph = {}
    
    for file_path in changed_files:
        if not file_path.endswith('.py'):
            continue
            
        full_path = repo / file_path
        if not full_path.exists():
            continue
            
        try:
            code = full_path.read_text(encoding='utf-8')
            dep_info = analyze_dependencies(code, file_path)
            dependency_graph[file_path] = dep_info
        except Exception as e:
            # Skip files that can't be analyzed
            print(f"Warning: Could not analyze {file_path}: {e}")
            continue
    
    return dependency_graph


def detect_breaking_changes(
    old_code: str,
    new_code: str,
    file_path: str
) -> List[str]:
    """Detect potential breaking changes between old and new code.
    
    Args:
        old_code: Original code
        new_code: Modified code
        file_path: Path to file (for context)
        
    Returns:
        List of detected breaking changes
    """
    breaking_changes = []
    
    try:
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
    except SyntaxError:
        return ["Syntax error - unable to parse code"]
    
    # Extract function signatures from old code
    old_functions = {}
    for node in ast.walk(old_tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            old_functions[node.name] = len(node.args.args)
    
    # Check for removed or modified functions
    new_functions = {}
    for node in ast.walk(new_tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            new_functions[node.name] = len(node.args.args)
    
    # Detect removed functions
    for func_name in old_functions:
        if func_name not in new_functions:
            breaking_changes.append(f"Removed public function: {func_name}")
    
    # Detect signature changes
    for func_name, old_arg_count in old_functions.items():
        if func_name in new_functions:
            new_arg_count = new_functions[func_name]
            if old_arg_count != new_arg_count:
                breaking_changes.append(
                    f"Changed function signature: {func_name} "
                    f"({old_arg_count} → {new_arg_count} args)"
                )
    
    return breaking_changes


def analyze_impact(
    repo_path: str,
    changed_files: List[str],
    old_versions: Optional[Dict[str, str]] = None
) -> ImpactAnalysis:
    """Analyze impact of changes on the codebase.
    
    Args:
        repo_path: Path to repository
        changed_files: List of changed file paths
        old_versions: Optional dict of old file contents for breaking change detection
        
    Returns:
        ImpactAnalysis with affected modules and risk assessment
    """
    # Build dependency graph
    dep_graph = build_dependency_graph(repo_path, changed_files)
    
    # Detect breaking changes if old versions provided
    breaking_changes = []
    if old_versions:
        repo = Path(repo_path)
        for file_path in changed_files:
            if file_path not in old_versions:
                continue
            if not file_path.endswith('.py'):
                continue
                
            full_path = repo / file_path
            if not full_path.exists():
                continue
                
            old_code = old_versions[file_path]
            new_code = full_path.read_text(encoding='utf-8')
            
            changes = detect_breaking_changes(old_code, new_code, file_path)
            breaking_changes.extend(changes)
    
    # Find affected modules (simplistic - would need full repo scan for real implementation)
    affected_modules = []
    for file_path, dep_info in dep_graph.items():
        # Any module that imports from changed files is affected
        for import_name in dep_info.imports:
            if any(import_name in cf for cf in changed_files):
                affected_modules.append(file_path)
    
    # Assess risk level
    if breaking_changes:
        risk_level = "high"
    elif len(affected_modules) > 5:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return ImpactAnalysis(
        changed_modules=changed_files,
        affected_modules=sorted(set(affected_modules)),
        breaking_changes=breaking_changes,
        risk_level=risk_level
    )


def format_impact_report(impact: ImpactAnalysis) -> str:
    """Format impact analysis as human-readable report.
    
    Args:
        impact: ImpactAnalysis object
        
    Returns:
        Formatted report string
    """
    lines = [
        "Impact Analysis Report",
        "=" * 80,
        f"\nRisk Level: {impact.risk_level.upper()}",
        f"\nChanged Modules: {len(impact.changed_modules)}",
    ]
    
    for module in impact.changed_modules:
        lines.append(f"  - {module}")
    
    if impact.affected_modules:
        lines.append(f"\nAffected Modules: {len(impact.affected_modules)}")
        for module in impact.affected_modules[:10]:  # Show first 10
            lines.append(f"  - {module}")
        if len(impact.affected_modules) > 10:
            lines.append(f"  ... and {len(impact.affected_modules) - 10} more")
    
    if impact.breaking_changes:
        lines.append(f"\nBreaking Changes Detected: {len(impact.breaking_changes)}")
        for change in impact.breaking_changes:
            lines.append(f"  ⚠️  {change}")
    else:
        lines.append("\nNo breaking changes detected")
    
    return "\n".join(lines)
