#!/bin/bash
# Setup development environment

set -e

echo "🔧 Setting up development environment..."

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
if [[ "$python_version" < "3.10" ]]; then
    echo "❌ Python 3.10+ required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install package in editable mode with dev dependencies
echo "Installing package in editable mode..."
pip install -e .

echo "Installing development dependencies..."
pip install -r requirements/dev.txt

echo "Installing test dependencies..."
pip install -r requirements/test.txt

# Create .env template if it doesn't exist
if [ ! -f "deployment/.env.dev.example" ]; then
    echo "Creating .env templates..."
    cat > deployment/.env.dev.example << 'EOF'
# Local Development Configuration

# Google AI Studio API Key (get at https://aistudio.google.com/apikey)
GOOGLE_API_KEY=your_api_key_here

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_TEST_REPO=owner/repo  # Optional: for testing

# Logging
LOG_LEVEL=INFO
EOF
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Copy deployment/.env.dev.example to deployment/.env.dev"
echo "  2. Add your GOOGLE_API_KEY and GITHUB_TOKEN"
echo "  3. Activate environment: source venv/bin/activate"
echo "  4. Run tests: ./scripts/run_tests.sh"
echo ""
