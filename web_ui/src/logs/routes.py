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

@router.get(
    "/search",
    summary="Search log entries",
    description="Search through log entries for specific terms."
)
async def search_logs(
    query: str = Query(..., description="Search term to look for in log messages"),
    limit: int = Query(100, description="Maximum number of results to return"),
    repository: LogsRepository = Depends(get_logs_repository)
):
    """Search log entries"""
    try:
        logger.info(f"API: Searching logs for '{query}' (limit={limit})")
        
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        
        if limit > 1000:
            raise ValueError("Search limit cannot exceed 1,000 entries")
        
        search_results = await repository.search_logs(query.strip(), limit)
        return search_results
        
    except ValueError as e:
        logger.error(f"Validation error in search logs API: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"API error searching logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {str(e)}"
        )

@router.get(
    "/statistics",
    summary="Get log statistics",
    description="Returns statistics about log files and log levels."
)
async def get_log_statistics(
    repository: LogsRepository = Depends(get_logs_repository)
):
    """Get log statistics"""
    try:
        logger.info("API: Getting log statistics")
        
        stats = await repository.get_log_statistics()
        return stats
        
    except Exception as e:
        logger.error(f"API error getting log statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log statistics: {str(e)}"
        )

@router.get(
    "/files",
    summary="Get log files list",
    description="Returns list of available log files."
)
async def get_log_files(
    repository: LogsRepository = Depends(get_logs_repository)
):
    """Get list of log files"""
    try:
        logger.info("API: Getting log files list")
        
        files = await repository.get_log_files()
        return {
            "files": files,
            "total": len(files)
        }
        
    except Exception as e:
        logger.error(f"API error getting log files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log files: {str(e)}"
        )

@router.post(
    "/clear",
    summary="Clear log files",
    description="Clear log files, optionally keeping files newer than specified days."
)
async def clear_logs(
    older_than_days: Optional[int] = Query(None, description="Only delete files older than this many days"),
    repository: LogsRepository = Depends(get_logs_repository)
):
    """Clear log files"""
    try:
        logger.info(f"API: Clearing logs (older_than_days={older_than_days})")
        
        if older_than_days is not None and older_than_days < 0:
            raise ValueError("older_than_days must be non-negative")
        
        result = await repository.clear_logs(older_than_days)
        
        if 'error' in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in clear logs API: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"API error clearing logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear logs: {str(e)}"
        )
