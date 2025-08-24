"""
Logs API routes
FastAPI endpoints for system log management
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from .repository import LogsRepository
from ..dependencies import get_greythr_integration_optional

logger = logging.getLogger('webui.logs.routes')

# Create router
router = APIRouter(prefix="/api/logs", tags=["logs"])

# Dependency to get logs repository
def get_logs_repository(
    integration = Depends(get_greythr_integration_optional)
) -> LogsRepository:
    """Get logs repository with dependency injection"""
    return LogsRepository(integration.project_path)

@router.get(
    "/recent",
    summary="Get recent log entries",
    description="Returns recent system log entries with optional filtering."
)
async def get_recent_logs(
    limit: int = Query(500, description="Maximum number of log entries to return"),
    level: Optional[str] = Query(None, description="Filter by log level (error, warning, info, debug)"),
    date_filter: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    repository: LogsRepository = Depends(get_logs_repository)
):
    """Get recent log entries"""
    try:
        logger.info(f"API: Getting recent logs (limit={limit}, level={level}, date={date_filter})")
        
        if limit > 10000:
            raise ValueError("Limit cannot exceed 10,000 entries")
        
        logs_data = await repository.get_recent_logs(limit, level, date_filter)
        return logs_data
        
    except ValueError as e:
        logger.error(f"Validation error in recent logs API: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"API error getting recent logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent logs: {str(e)}"
        )