#!/usr/bin/env python3
"""
GreytHR Attendance Automation - Web UI Dashboard
FastAPI-based web interface for monitoring and managing GreytHR attendance automation
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
from datetime import datetime

from src.app_utils import ConfigManager
from src.logging_config import setup_logging
from src.dashboard.routes import router as dashboard_router
from src.service.routes import router as service_router
from src.activities.routes import router as activities_router
from src.logs.routes import router as logs_router


# Initialize logging
logger = setup_logging()

# Initialize configuration
config_manager = ConfigManager()
config = config_manager.load_config()

# Create FastAPI application
app = FastAPI(
    title="GreytHR Attendance Automation Dashboard",
    description="Web UI for monitoring and managing GreytHR attendance automation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("cors", {}).get("allow_origins", ["http://localhost:8000"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard_router)
app.include_router(service_router)
app.include_router(activities_router)
app.include_router(logs_router)


# Setup static files and templates
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# Health check endpoint
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GreytHR Web UI Dashboard",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    try:
        # Check if we can access the GreytHR project directory
        greythr_path = Path(config.get("greythr", {}).get("project_path", "../"))
        state_file = greythr_path / "state" / "current_state.json"
        
        checks = {
            "greythr_project_accessible": greythr_path.exists(),
            "state_file_exists": state_file.exists(),
            "config_loaded": bool(config)
        }
        
        all_healthy = all(checks.values())
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    logger.warning(f"HTTP exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    # Load server configuration
    host = config.get("server", {}).get("host", "127.0.0.1")
    port = int(config.get("server", {}).get("port", 8000))
    
    logger.info(f"Starting GreytHR Web UI Dashboard on {host}:{port}")
    logger.info(f"Dashboard: http://{host}:{port}")
    logger.info(f"API Docs: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info"
    )
