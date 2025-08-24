#!/bin/bash
# Development server runner for GreytHR Web UI Dashboard

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting GreytHR Web UI Dashboard - Development Server${NC}"
echo -e "${BLUE}==========================================================${NC}"

# Set environment variables
export CONFIG_PATH="conf"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies if requirements.txt exists
if [[ -f "requirements.txt" ]]; then
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if GreytHR project is accessible
GREYTHR_PATH="../"
if [[ -f "../greythr_api.py" ]]; then
    echo -e "${GREEN}✅ GreytHR project found at: $(realpath $GREYTHR_PATH)${NC}"
else
    echo -e "${YELLOW}⚠️  GreytHR project not found at expected location${NC}"
    echo -e "${YELLOW}   Expected: $(realpath $GREYTHR_PATH)/greythr_api.py${NC}"
    echo -e "${YELLOW}   You may need to update the project_path in conf/default_config.yaml${NC}"
fi

# Start the development server
echo -e "${BLUE}🌐 Starting FastAPI development server...${NC}"
echo -e "${GREEN}📍 Dashboard: http://127.0.0.1:8000${NC}"
echo -e "${GREEN}📖 API Docs: http://127.0.0.1:8000/docs${NC}"
echo -e "${GREEN}📋 ReDoc: http://127.0.0.1:8000/redoc${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run uvicorn with reload for development
uvicorn main:app --reload --host 127.0.0.1 --port 8000 --log-level info
