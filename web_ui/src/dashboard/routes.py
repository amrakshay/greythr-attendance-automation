"""
Dashboard API routes
FastAPI endpoints for dashboard functionality
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List

from .controller import DashboardController
from .repository import DashboardRepository
from .schemas import DashboardOverview, QuickStats, Alert
from ..models.status import SystemStatusResponse, TodaySummaryResponse
from ..models.activity import ActivityListItem
from ..dependencies import get_greythr_integration_optional

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