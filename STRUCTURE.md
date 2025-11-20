# Repository Structure

Production-grade organization for AI Code Review Orchestration System.

## Quick Start

```bash
# Setup development environment
./scripts/setup_dev.sh

# Activate virtual environment
source venv/bin/activate

# Run tests
./scripts/run_tests.sh unit      # Fast unit tests
./scripts/run_tests.sh all       # All tests
./scripts/run_tests.sh coverage  # With coverage report

# Code quality
./scripts/lint.sh
```

## Directory Layout

### `src/capstone/` - Production Code

All production source code in proper Python package structure.

```
src/capstone/
├── config.py           # Configuration management
├── models.py           # Shared Pydantic models
├── agents/             # Agent implementations
├── memory/             # Memory Bank system
├── tools/              # Agent tools (GitHub, parsing, analysis)
└── lib/                # Utilities (logging, metrics)
```

**Install as package:**
```bash
pip install -e .  # Editable install for development
```

### `tests/` - Test Hierarchy

Organized by test type for performance optimization.

```
tests/
├── conftest.py         # Pytest fixtures
├── unit/               # Fast, isolated (< 1s each)
├── integration/        # Mock external services (< 5s each)
├── e2e/                # Full workflow (< 30s each)
└── fixtures/           # Shared test data
    ├── changesets.py
    ├── mock_github.py
    └── mock_pr.py
```

**Run by type:**
```bash
pytest tests/unit/           # Only unit tests (fastest)
pytest tests/integration/    # Integration tests
pytest tests/e2e/            # End-to-end tests (slowest)
pytest -m "unit"             # By marker
pytest -m "not slow"         # Exclude slow tests
```

### `deployment/` - Deployment Configuration

Everything needed for production deployment.

```
deployment/
├── .env.example            # Production config template
├── .env.dev.example        # Local development template
├── .env.deploy.example     # Deployment settings template
├── Dockerfile              # Container image
├── deploy.py               # Deployment automation
├── check_agent.py          # Status verification
└── .gitignore              # Secret protection
```

**Usage:**
```bash
# 1. Setup configs
cp deployment/.env.dev.example deployment/.env.dev
# Add GOOGLE_API_KEY and GITHUB_TOKEN

# 2. Deploy to GCP (requires GCP project)
cp deployment/.env.deploy.example deployment/.env.deploy
# Add GCP_PROJECT_ID, service account key
python deployment/deploy.py
```

### `requirements/` - Dependency Management

Split requirements for minimal container size.

```
requirements/
├── base.txt    # Core dependencies (ADK, PyGithub, Pydantic)
├── dev.txt     # Development tools (black, ruff, mypy)
├── test.txt    # Testing libraries (pytest, coverage)
└── deploy.txt  # Production only (minimal)
```

**Install:**
```bash
pip install -r requirements/base.txt      # Core only
pip install -r requirements/dev.txt       # + dev tools
pip install -r requirements/test.txt      # + test tools
pip install -r requirements/deploy.txt    # Production
```

### `scripts/` - Development Utilities

Automation scripts for common tasks.

```
scripts/
├── setup_dev.sh        # One-command env setup
├── run_tests.sh        # Test runner with options
├── lint.sh             # Code quality checks
├── create_test_prs.py  # Generate test data
└── reset_fixture.py    # Reset test environment
```

### `docs/` - Documentation

Project documentation and diagrams.

```
docs/
├── project-plan.md
├── architecture-overview.md
├── testing-strategy.md
└── diagrams/
```

### `evalsets/` - ADK Evaluation Sets

Agent evaluation datasets for ADK.

```
evalsets/
├── README.md
└── test_fixture_prs.evalset.json
```

### `test-fixture/` - Test Repository

Separate test application for PR testing.

```
test-fixture/
└── app/          # Sample Python app with intentional issues
```

## Development Workflow

### 1. Initial Setup

```bash
git clone <repo>
cd capstone
./scripts/setup_dev.sh
source venv/bin/activate
```

### 2. Development Cycle

```bash
# Make changes
vim src/capstone/agents/analyzer.py

# Run relevant tests (fast feedback)
pytest tests/unit/test_analyzer.py -v

# Check code quality
./scripts/lint.sh

# Fix formatting if needed
black src/ tests/
ruff check --fix src/ tests/

# Run full test suite
./scripts/run_tests.sh all
```

### 3. Testing Strategy

```bash
# Fast iteration (unit tests only)
pytest tests/unit/ -v --tb=short

# Integration testing (with mocks)
pytest tests/integration/ -v

# Full validation (before commit)
./scripts/run_tests.sh coverage

# CI/CD simulation
./scripts/lint.sh && ./scripts/run_tests.sh all
```

### 4. Deployment

```bash
# Local testing first
cp deployment/.env.dev.example deployment/.env.dev
# Add GOOGLE_API_KEY
# Test locally with ADK

# Deploy to GCP
cp deployment/.env.deploy.example deployment/.env.deploy
# Add GCP_PROJECT_ID, credentials
python deployment/deploy.py

# Verify deployment
python deployment/check_agent.py
```

## Benefits of This Structure

### For Development
- **Clear boundaries**: Each module has single responsibility
- **Easy navigation**: Predictable file locations
- **Proper imports**: `from capstone.agents import Analyzer`
- **Package installable**: `pip install -e .` for editable mode

### For Testing
- **Performance tiering**: Run only what you need
  - Unit tests: < 1 second total
  - Integration: < 10 seconds
  - E2E: < 60 seconds
- **Isolated fixtures**: Reusable test data
- **Mock layers**: Test without external dependencies
- **Coverage tracking**: `pytest --cov` works out of box

### For Deployment
- **Single source of truth**: `deployment/` folder
- **Minimal containers**: Split requirements = small images
- **Config templates**: Easy to set up new environments
- **Automated scripts**: Reproducible deployments

### For CI/CD
- **Fast feedback**: Unit tests on every commit (< 1s)
- **Thorough validation**: Integration tests on PR (< 10s)
- **Full verification**: E2E on main branch (< 60s)
- **Quality gates**: Lint + tests must pass

## Migration from Old Structure

Old structure had files scattered in root:
```
OLD:
capstone/
├── changesets.py          # Was in root
├── github_utils.py        # Was in root
├── interfaces.py          # Was in root
├── memory_schema.py       # Was in root
├── tools/                 # Only test mocks
└── tests/                 # Only test_changesets.py
```

New structure is organized:
```
NEW:
capstone/
├── src/capstone/          # All production code
│   ├── agents/
│   ├── memory/
│   ├── tools/
│   └── lib/
├── tests/                 # All tests organized
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── deployment/            # All deployment configs
├── requirements/          # Split dependencies
└── scripts/               # Dev utilities
```

## Next Steps

1. **Review structure** - Check if layout makes sense
2. **Fix imports** - Update any remaining old imports
3. **Run tests** - Verify everything works
4. **Start development** - Build agents with clean structure
5. **Deploy** - Use deployment/ configs for production

---

**Created:** 2025-11-19  
**Structure Type:** Production-grade multi-agent system  
**Package Manager:** pip + pyproject.toml  
**Test Framework:** pytest with markers and coverage
