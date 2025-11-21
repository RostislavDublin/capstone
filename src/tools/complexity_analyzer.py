"""Code complexity analyzer using radon library."""

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


@dataclass
class CodeComplexityResult:
    """Overall code complexity analysis results."""

    functions: List[FunctionComplexity]
    average_complexity: float
    total_complexity: int
    high_complexity_count: int  # Functions with rank D, E, or F
    maintainability_index: Optional[float] = None  # 0-100 (higher is better)


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
        raise SyntaxError(f"Code has syntax errors: {e}") from e

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
            complexity_rank=rank,
        )
        functions.append(func)
        total_complexity += block.complexity

        # Count high complexity functions (D, E, F)
        if rank in ("D", "E", "F"):
            high_complexity_count += 1

    # Calculate average complexity
    average_complexity = total_complexity / len(functions) if functions else 0.0

    # Calculate maintainability index (optional, requires valid Python module)
    maintainability_index = None
    try:
        mi_result = mi_visit(code, multi=True)
        if mi_result:
            maintainability_index = mi_result
    except Exception:
        # If MI calculation fails, leave it as None
        pass

    return CodeComplexityResult(
        functions=functions,
        average_complexity=round(average_complexity, 2),
        total_complexity=total_complexity,
        high_complexity_count=high_complexity_count,
        maintainability_index=(
            round(maintainability_index, 2) if maintainability_index else None
        ),
    )
