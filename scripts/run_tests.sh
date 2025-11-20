#!/bin/bash
# Run tests with different modes

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default: run all tests
TEST_TYPE=${1:-all}

echo -e "${YELLOW}🧪 Running tests: $TEST_TYPE${NC}"
echo ""

case $TEST_TYPE in
    unit)
        echo "Running unit tests (fast)..."
        pytest tests/unit/ -v -m "unit" --cov=src/capstone --cov-report=term-missing
        ;;
    integration)
        echo "Running integration tests (medium)..."
        pytest tests/integration/ -v -m "integration"
        ;;
    e2e)
        echo "Running e2e tests (slow)..."
        pytest tests/e2e/ -v -m "e2e"
        ;;
    fast)
        echo "Running only fast tests..."
        pytest tests/unit/ -v -m "unit and not slow"
        ;;
    coverage)
        echo "Running tests with coverage report..."
        pytest tests/ -v --cov=src/capstone --cov-report=html --cov-report=term
        echo ""
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
        ;;
    all)
        echo "Running all tests..."
        pytest tests/ -v --cov=src/capstone --cov-report=term-missing
        ;;
    *)
        echo "Unknown test type: $TEST_TYPE"
        echo "Usage: $0 [unit|integration|e2e|fast|coverage|all]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Tests complete!${NC}"
