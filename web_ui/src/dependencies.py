"""
FastAPI dependencies for GreytHR Web UI Dashboard
Following the established dependency injection patterns
"""

from functools import lru_cache
from fastapi import Depends, HTTPException, status
from typing import Optional
import logging

from .app_utils import ConfigManager, GreytHRIntegration

logger = logging.getLogger('webui.dependencies')

# Configuration dependencies
@lru_cache()
def get_config_manager() -> ConfigManager:
    """Get singleton ConfigManager instance"""
    return ConfigManager()

@lru_cache()
def get_greythr_integration() -> GreytHRIntegration:
    """Get singleton GreytHRIntegration instance"""
    config_manager = get_config_manager()
    config = config_manager.load_config()
    project_path = config.get("greythr", {}).get("project_path", "../")
    return GreytHRIntegration(project_path)

# Health check dependency
async def check_greythr_project_accessible(
    integration: GreytHRIntegration = Depends(get_greythr_integration)
) -> GreytHRIntegration:
    """Check if GreytHR project is accessible"""
    if not integration.is_project_accessible():
        logger.error(f"GreytHR project not accessible at: {integration.project_path}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "GreytHR project not accessible",
                "project_path": str(integration.project_path),
                "suggestion": "Check if the project path is correct in configuration"
            }
        )
    return integration

# Optional project access (doesn't raise error if not accessible)
async def get_greythr_integration_optional(
    integration: GreytHRIntegration = Depends(get_greythr_integration)
) -> GreytHRIntegration:
    """Get GreytHR integration without requiring accessibility"""
    return integration

# Configuration dependency
async def get_current_config(
    config_manager: ConfigManager = Depends(get_config_manager)
) -> dict:
    """Get current configuration"""
    return config_manager.load_config()

# Pagination dependencies
class PaginationParams:
    def __init__(
        self,
        page: int = 0,
        size: int = 25,
        max_size: int = 100
    ):
        self.page = max(0, page)
        self.size = min(max_size, max(1, size))
        self.offset = self.page * self.size

def get_pagination_params(
    page: int = 0,
    size: int = 25
) -> PaginationParams:
    """Get pagination parameters with validation"""
    return PaginationParams(page=page, size=size)

# Log file validation dependency
def validate_log_filename(filename: str) -> str:
    """Validate log filename for security"""
    # Only allow specific log file patterns
    allowed_patterns = [
        'webui_',
        'greythr_attendance_',
        'launchd_stdout',
        'launchd_stderr'
    ]
    
    if not any(filename.startswith(pattern) for pattern in allowed_patterns):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log filename: {filename}"
        )
    
    # Prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid characters in filename"
        )
    
    return filename

# Date validation dependency
def validate_date_format(date_str: str) -> str:
    """Validate date format (YYYY-MM-DD)"""
    import re
    from datetime import datetime
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date value"
        )
    
    return date_str
