#!/bin/bash
# Test runner for GreytHR Web UI Dashboard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Running GreytHR Web UI Dashboard Tests${NC}"
echo -e "${BLUE}=======================================${NC}"

# Set environment variables
export CONFIG_PATH="conf"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Activate virtual environment if it exists
if [[ -d ".venv" ]]; then
    echo -e "${BLUE}📦 Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio pytest-cov
fi

# Create test directories if they don't exist
mkdir -p tests

# Run tests with different options based on arguments
case "${1:-all}" in
    "unit")
        echo -e "${BLUE}🔬 Running unit tests...${NC}"
        python -m pytest tests/ -v --tb=short -k "not integration"
        ;;
    "integration")
        echo -e "${BLUE}🔗 Running integration tests...${NC}"
        python -m pytest tests/ -v --tb=short -k "integration"
        ;;
    "coverage")
        echo -e "${BLUE}📊 Running tests with coverage...${NC}"
        python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}📈 Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "fast")
        echo -e "${BLUE}⚡ Running fast tests only...${NC}"
        python -m pytest tests/ -v --tb=short -x -k "not slow"
        ;;
    "all"|*)
        echo -e "${BLUE}🧪 Running all tests...${NC}"
        python -m pytest tests/ -v --tb=short
        ;;
esac

# Check exit code
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi
