#!/bin/bash
# Run code quality checks

set -e

echo "🔍 Running code quality checks..."
echo ""

# Run black (formatting)
echo "1. Checking code formatting with black..."
black --check src/ tests/ || {
    echo "❌ Code formatting issues found. Run: black src/ tests/"
    exit 1
}
echo "✅ Code formatting OK"
echo ""

# Run ruff (linting)
echo "2. Running linter with ruff..."
ruff check src/ tests/ || {
    echo "❌ Linting issues found. Run: ruff check --fix src/ tests/"
    exit 1
}
echo "✅ Linting OK"
echo ""

# Run mypy (type checking)
echo "3. Running type checker with mypy..."
mypy src/capstone || {
    echo "⚠️  Type checking issues found (non-blocking)"
}
echo ""

echo "✅ All quality checks passed!"
