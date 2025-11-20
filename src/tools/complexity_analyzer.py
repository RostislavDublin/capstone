"""Code complexity analyzer using radon library.

This module provides functionality to calculate cyclomatic and cognitive complexity
metrics for Python code using radon's programmatic API.

Note: Currently supports Python only. Architecture allows extension to other languages
via additional analyzer implementations or LLM-based analysis.
"""

from dataclasses import dataclass
from typing import List, Optional

from radon.complexity import cc_visit, cc_rank
from radon.metrics import mi_visit


@dataclass
class FunctionComplexity:
    """Complexity metrics for a single function."""
    
    name: str
    lineno: int
    col_offset: int
    endline: int
    cyclomatic_complexity: int  # McCabe's cyclomatic complexity
    complexity_rank: str  # A, B, C, D, E, F (A=simple, F=very complex)
    
    # Complexity interpretation:
    # A: 1-5   (simple)
    # B: 6-10  (well structured)
    # C: 11-20 (slightly complex)
    # D: 21-30 (more complex)
    # E: 31-40 (complex)
    # F: 41+   (very complex, needs refactoring)


@dataclass
class CodeComplexityResult:
    """Overall code complexity analysis results."""
    
    functions: List[FunctionComplexity]
    average_complexity: float
    total_complexity: int
    high_complexity_count: int  # Functions with rank D, E, or F
    maintainability_index: Optional[float] = None  # 0-100 (higher is better)
    
    # Maintainability Index interpretation:
    # 0-9:   Difficult to maintain (red)
    # 10-19: Moderate maintenance (yellow)
    # 20+:   Easy to maintain (green)


def calculate_complexity(code: str, language: str = "python") -> CodeComplexityResult:
    """Calculate code complexity metrics using radon.
    
    Args:
        code: Source code to analyze
        language: Programming language (currently only 'python' supported)
        
    Returns:
        CodeComplexityResult with complexity metrics
        
    Raises:
        ValueError: If code is empty or language not supported
        SyntaxError: If code has syntax errors
    """
    if not code or not code.strip():
        raise ValueError("code cannot be empty")
    
    if language.lower() != "python":
        raise ValueError(f"Language '{language}' not supported. Only 'python' is supported.")
    
    # Calculate cyclomatic complexity for all functions/methods
    try:
        complexity_blocks = cc_visit(code)
    except SyntaxError as e:
        raise SyntaxError(f"Code has syntax errors: {e}")
    
    # Convert radon ComplexityVisitor blocks to our dataclass
    functions = []
    total_complexity = 0
    high_complexity_count = 0
    
    for block in complexity_blocks:
        # Calculate rank using cc_rank function
        rank = cc_rank(block.complexity)
        
        func = FunctionComplexity(
            name=block.name,
            lineno=block.lineno,
            col_offset=block.col_offset,
            endline=block.endline,
            cyclomatic_complexity=block.complexity,
            complexity_rank=rank
        )
        functions.append(func)
        total_complexity += block.complexity
        
        # Count high complexity functions (D, E, F)
        if rank in ('D', 'E', 'F'):
            high_complexity_count += 1
    
    # Calculate average complexity
    average_complexity = total_complexity / len(functions) if functions else 0.0
    
    # Calculate maintainability index (optional, requires valid Python module)
    maintainability_index = None
    try:
        mi_result = mi_visit(code, multi=True)
        if mi_result:
            # mi_visit returns average MI across all blocks
            maintainability_index = mi_result
    except Exception:
        # If MI calculation fails, leave it as None
        pass
    
    return CodeComplexityResult(
        functions=functions,
        average_complexity=round(average_complexity, 2),
        total_complexity=total_complexity,
        high_complexity_count=high_complexity_count,
        maintainability_index=round(maintainability_index, 2) if maintainability_index else None
    )


def format_complexity_report(result: CodeComplexityResult) -> str:
    """Format complexity analysis results as a human-readable report.
    
    Args:
        result: CodeComplexityResult to format
        
    Returns:
        Formatted string report
    """
    if not result.functions:
        return "No functions found to analyze."
    
    lines = [
        "Code Complexity Analysis:",
        f"  Total Functions: {len(result.functions)}",
        f"  Average Complexity: {result.average_complexity}",
        f"  High Complexity Functions: {result.high_complexity_count}",
    ]
    
    if result.maintainability_index is not None:
        mi = result.maintainability_index
        if mi >= 20:
            mi_status = "Easy"
        elif mi >= 10:
            mi_status = "Moderate"
        else:
            mi_status = "Difficult"
        lines.append(f"  Maintainability Index: {mi} ({mi_status})")
    
    lines.append("")
    
    # Sort functions by complexity (highest first)
    sorted_funcs = sorted(result.functions, key=lambda f: f.cyclomatic_complexity, reverse=True)
    
    for i, func in enumerate(sorted_funcs, 1):
        complexity_level = _get_complexity_level(func.complexity_rank)
        
        lines.extend([
            f"Function #{i}: {func.name}",
            f"  Lines: {func.lineno}-{func.endline}",
            f"  Cyclomatic Complexity: {func.cyclomatic_complexity} (Rank: {func.complexity_rank})",
            f"  Assessment: {complexity_level}",
        ])
        
        # Add recommendation for high complexity
        if func.complexity_rank in ('D', 'E', 'F'):
            lines.append("  ⚠️  Recommendation: Consider refactoring to reduce complexity")
        
        lines.append("")
    
    return "\n".join(lines)


def _get_complexity_level(rank: str) -> str:
    """Get human-readable complexity level description."""
    levels = {
        'A': 'Simple and easy to maintain',
        'B': 'Well-structured and maintainable',
        'C': 'Slightly complex, acceptable',
        'D': 'More complex, needs attention',
        'E': 'Complex, refactoring recommended',
        'F': 'Very complex, refactoring strongly recommended'
    }
    return levels.get(rank, 'Unknown')
