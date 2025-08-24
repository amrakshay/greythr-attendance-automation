#!/bin/bash
# Setup script for GreytHR Web UI Dashboard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛠️  Setting up GreytHR Web UI Dashboard${NC}"
echo -e "${BLUE}======================================${NC}"

# Check Python version
python_version=$(python3 --version 2>&1)
echo -e "${BLUE}🐍 Python version: $python_version${NC}"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo -e "${RED}❌ Python 3.8+ is required${NC}"
    exit 1
fi

# Create virtual environment
if [[ ! -d ".venv" ]]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}📦 Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${BLUE}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
if [[ -f "requirements.txt" ]]; then
    echo -e "${BLUE}📦 Installing dependencies from requirements.txt...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, installing basic dependencies...${NC}"
    pip install fastapi uvicorn jinja2 aiofiles pyyaml
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p logs
mkdir -p src/static/css
mkdir -p src/static/js
mkdir -p src/static/images
mkdir -p src/templates
echo -e "${GREEN}✅ Directories created${NC}"

# Make scripts executable
echo -e "${BLUE}🔧 Making scripts executable...${NC}"
chmod +x scripts/*.sh
echo -e "${GREEN}✅ Scripts are now executable${NC}"

# Check GreytHR project accessibility
echo -e "${BLUE}🔍 Checking GreytHR project accessibility...${NC}"
GREYTHR_PATH="../"
if [[ -f "../greythr_api.py" ]]; then
    echo -e "${GREEN}✅ GreytHR project found at: $(realpath $GREYTHR_PATH)${NC}"
else
    echo -e "${YELLOW}⚠️  GreytHR project not found at expected location${NC}"
    echo -e "${YELLOW}   Expected: $(realpath $GREYTHR_PATH)/greythr_api.py${NC}"
    echo -e "${YELLOW}   Please update the project_path in conf/default_config.yaml${NC}"
fi

echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Review configuration in conf/default_config.yaml"
echo -e "  2. Start development server: ${GREEN}./scripts/run_dev.sh${NC}"
echo -e "  3. Open browser: ${GREEN}http://127.0.0.1:8000${NC}"
echo -e "  4. View API docs: ${GREEN}http://127.0.0.1:8000/docs${NC}"
