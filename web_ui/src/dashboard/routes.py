"""
Dashboard API routes
FastAPI endpoints for dashboard functionality
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from .controller import DashboardController
from .repository import DashboardRepository
from .schemas import (
    DashboardOverview, QuickStats, Alert, SystemHealth, 
    RefreshRequest, ErrorResponse
)
from ..models.status import SystemStatusResponse, TodaySummaryResponse, HealthCheckResponse
from ..models.activity import ActivityListItem
from ..dependencies import get_greythr_integration_optional, PaginationParams, get_pagination_params

logger = logging.getLogger('webui.dashboard.routes')

# Create router
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Dependency to get dashboard controller
def get_dashboard_controller(
    integration = Depends(get_greythr_integration_optional)
) -> DashboardController:
    """Get dashboard controller with dependency injection"""
    repository = DashboardRepository(integration.project_path)
    return DashboardController(repository)

# Main dashboard endpoints

@router.get(
    "/overview",
    response_model=DashboardOverview,
    summary="Get complete dashboard overview",
    description="Returns all dashboard data in a single response including system status, today's summary, recent activities, and alerts."
)
async def get_dashboard_overview(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get complete dashboard overview"""
    try:
        logger.info("API: Getting dashboard overview")
        overview = await controller.get_dashboard_overview()
        return overview
        
    except Exception as e:
        logger.error(f"API error getting dashboard overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard overview: {str(e)}"
        )

@router.get(
    "/status",
    response_model=SystemStatusResponse,
    summary="Get current system status",
    description="Returns current system status including daemon state, uptime, and resource usage."
)
async def get_system_status(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get current system status"""
    try:
        logger.info("API: Getting system status")
        status_data = await controller.get_system_status()
        return status_data
        
    except Exception as e:
        logger.error(f"API error getting system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )

@router.get(
    "/summary",
    response_model=TodaySummaryResponse,
    summary="Get today's attendance summary",
    description="Returns today's attendance summary including signin/signout status and attempt counts."
)
async def get_today_summary(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get today's attendance summary"""
    try:
        logger.info("API: Getting today's summary")
        summary = await controller.get_today_summary()
        return summary
        
    except Exception as e:
        logger.error(f"API error getting today's summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get today's summary: {str(e)}"
        )

@router.get(
    "/recent-activities",
    response_model=List[ActivityListItem],
    summary="Get recent activities",
    description="Returns a list of recent attendance activities."
)
async def get_recent_activities(
    limit: int = Query(5, ge=1, le=20, description="Number of recent activities to return"),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get recent activities"""
    try:
        logger.info(f"API: Getting recent activities (limit={limit})")
        activities = await controller.get_recent_activities(limit)
        return activities
        
    except Exception as e:
        logger.error(f"API error getting recent activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent activities: {str(e)}"
        )

@router.get(
    "/quick-stats",
    response_model=QuickStats,
    summary="Get quick statistics",
    description="Returns quick statistics including success rate, streak, and averages."
)
async def get_quick_stats(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get quick statistics"""
    try:
        logger.info("API: Getting quick stats")
        stats = await controller.get_quick_stats()
        return stats
        
    except Exception as e:
        logger.error(f"API error getting quick stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quick stats: {str(e)}"
        )

@router.get(
    "/alerts",
    response_model=List[Alert],
    summary="Get system alerts",
    description="Returns current system alerts and notifications."
)
async def get_system_alerts(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get system alerts"""
    try:
        logger.info("API: Getting system alerts")
        alerts = await controller.get_system_alerts()
        return alerts
        
    except Exception as e:
        logger.error(f"API error getting system alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system alerts: {str(e)}"
        )

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Get system health check",
    description="Performs a comprehensive health check of all system components."
)
async def get_system_health(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get system health check"""
    try:
        logger.info("API: Performing health check")
        # Get the repository directly for health check
        integration = controller.repository
        health = await integration.get_health_check()
        return health
        
    except Exception as e:
        logger.error(f"API error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@router.get(
    "/health/detailed",
    response_model=SystemHealth,
    summary="Get detailed system health",
    description="Returns detailed health information with component breakdown and recommendations."
)
async def get_detailed_system_health(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get detailed system health"""
    try:
        logger.info("API: Getting detailed system health")
        health = await controller.get_system_health()
        return health
        
    except Exception as e:
        logger.error(f"API error getting detailed system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed system health: {str(e)}"
        )

# Management endpoints

@router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh dashboard data",
    description="Triggers a refresh of dashboard data. Use force=true to bypass cache."
)
async def refresh_dashboard(
    request: RefreshRequest,
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Refresh dashboard data"""
    try:
        logger.info(f"API: Refreshing dashboard data (force={request.force})")
        success = await controller.refresh_dashboard_data(request.force)
        
        return {
            "success": success,
            "message": "Dashboard data refreshed successfully" if success else "Failed to refresh dashboard data",
            "timestamp": "2024-01-01T00:00:00Z"  # Will use real timestamp
        }
        
    except Exception as e:
        logger.error(f"API error refreshing dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh dashboard: {str(e)}"
        )

# Alternative endpoints for specific use cases

@router.get(
    "/status/simple",
    summary="Get simple system status",
    description="Returns a simplified system status for lightweight polling."
)
async def get_simple_system_status(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get simplified system status for polling"""
    try:
        status_data = await controller.get_system_status()
        
        return {
            "status": status_data.status,
            "daemon_running": status_data.daemon_running,
            "uptime": status_data.uptime_formatted,
            "last_updated": status_data.last_updated
        }
        
    except Exception as e:
        logger.error(f"API error getting simple status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get simple status: {str(e)}"
        )

@router.get(
    "/summary/simple",
    summary="Get simple today summary",
    description="Returns a simplified today summary for lightweight polling."
)
async def get_simple_today_summary(
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get simplified today summary for polling"""
    try:
        summary = await controller.get_today_summary()
        
        return {
            "date": summary.date,
            "signin_completed": summary.signin_completed,
            "signout_completed": summary.signout_completed,
            "signin_status": summary.signin_status,
            "signout_status": summary.signout_status
        }
        
    except Exception as e:
        logger.error(f"API error getting simple summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get simple summary: {str(e)}"
        )

# Note: Exception handlers are registered in main.py for the FastAPI app
