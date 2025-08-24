"""
Dashboard controller
Business logic layer for dashboard operations
"""

import logging
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from .repository import DashboardRepository
from .schemas import DashboardOverview, QuickStats, Alert
from ..models.status import SystemStatusResponse, TodaySummaryResponse
from ..models.activity import ActivityListItem

logger = logging.getLogger('webui.dashboard.controller')

class DashboardController:
    """Controller for dashboard business logic"""
    
    def __init__(self, repository: DashboardRepository):
        self.repository = repository
        
    async def get_dashboard_overview(self) -> DashboardOverview:
        """Get complete dashboard overview with all components"""
        try:
            logger.info("Fetching dashboard overview")
            
            # Fetch all data concurrently
            import asyncio
            system_status, today_summary, recent_activities, quick_stats, alerts = await asyncio.gather(
                self.get_system_status(),
                self.get_today_summary(),
                self.get_recent_activities(),
                self.get_quick_stats(),
                self.get_system_alerts(),
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(system_status, Exception):
                logger.error(f"Error fetching system status: {system_status}")
                system_status = self.repository._get_fallback_status()
            
            if isinstance(today_summary, Exception):
                logger.error(f"Error fetching today summary: {today_summary}")
                today_summary = self.repository._get_fallback_today_summary()
            
            if isinstance(recent_activities, Exception):
                logger.error(f"Error fetching recent activities: {recent_activities}")
                recent_activities = []
            
            if isinstance(quick_stats, Exception):
                logger.error(f"Error fetching quick stats: {quick_stats}")
                quick_stats = QuickStats(
                    total_days_tracked=0,
                    success_rate=0.0,
                    current_streak=0,
                    last_7_days_success=0,
                    avg_signin_time=None,
                    avg_signout_time=None
                )
            
            if isinstance(alerts, Exception):
                logger.error(f"Error fetching alerts: {alerts}")
                alerts = []
            
            return DashboardOverview(
                system_status=system_status,
                today_summary=today_summary,
                recent_activities=recent_activities,
                quick_stats=quick_stats,
                alerts=alerts
            )
            
        except Exception as e:
            logger.error(f"Error creating dashboard overview: {e}")
            # Return a minimal fallback overview
            return DashboardOverview(
                system_status=self.repository._get_fallback_status(),
                today_summary=self.repository._get_fallback_today_summary(),
                recent_activities=[],
                quick_stats=QuickStats(
                    total_days_tracked=0,
                    success_rate=0.0,
                    current_streak=0,
                    last_7_days_success=0,
                    avg_signin_time=None,
                    avg_signout_time=None
                ),
                alerts=[Alert(
                    type="error",
                    title="Dashboard Error",
                    message=f"Failed to load dashboard: {str(e)}",
                    timestamp=datetime.now().isoformat()
                )]
            )
    
    async def get_system_status(self) -> SystemStatusResponse:
        """Get current system status with validation"""
        try:
            status = await self.repository.get_system_status()
            if status is None:
                logger.warning("No system status available, using fallback")
                return self.repository._get_fallback_status()
            
            # Add business logic validation
            validated_status = self._validate_system_status(status)
            return validated_status
            
        except Exception as e:
            logger.error(f"Error in get_system_status controller: {e}")
            return self.repository._get_fallback_status()
    
    async def get_today_summary(self) -> TodaySummaryResponse:
        """Get today's summary with business logic enhancements"""
        try:
            summary = await self.repository.get_today_summary()
            if summary is None:
                logger.warning("No today summary available, using fallback")
                return self.repository._get_fallback_today_summary()
            
            # Add business logic enhancements
            enhanced_summary = self._enhance_today_summary(summary)
            return enhanced_summary
            
        except Exception as e:
            logger.error(f"Error in get_today_summary controller: {e}")
            return self.repository._get_fallback_today_summary()
    
    async def get_recent_activities(self, limit: int = 5) -> List[ActivityListItem]:
        """Get recent activities with filtering and validation"""
        try:
            activities = await self.repository.get_recent_activities(limit)
            
            # Apply business logic filtering
            filtered_activities = self._filter_recent_activities(activities)
            return filtered_activities
            
        except Exception as e:
            logger.error(f"Error in get_recent_activities controller: {e}")
            return []
    
    async def get_quick_stats(self) -> QuickStats:
        """Get quick statistics with business logic calculations"""
        try:
            stats = await self.repository.get_quick_stats()
            
            # Apply business logic enhancements
            enhanced_stats = self._enhance_quick_stats(stats)
            return enhanced_stats
            
        except Exception as e:
            logger.error(f"Error in get_quick_stats controller: {e}")
            return QuickStats(
                total_days_tracked=0,
                success_rate=0.0,
                current_streak=0,
                last_7_days_success=0,
                avg_signin_time=None,
                avg_signout_time=None
            )
    
    async def get_system_alerts(self) -> List[Alert]:
        """Get system alerts with prioritization and filtering"""
        try:
            alerts = await self.repository.get_system_alerts()
            
            # Apply business logic for alert prioritization
            prioritized_alerts = self._prioritize_alerts(alerts)
            return prioritized_alerts
            
        except Exception as e:
            logger.error(f"Error in get_system_alerts controller: {e}")
            return [Alert(
                type="error",
                title="Alert System Error",
                message=f"Failed to fetch alerts: {str(e)}",
                timestamp=datetime.now().isoformat()
            )]
    

    
    # Private helper methods for business logic
    
    def _validate_system_status(self, status: SystemStatusResponse) -> SystemStatusResponse:
        """Apply business logic validation to system status"""
        # Validate uptime consistency
        if status.uptime_seconds < 0:
            status.uptime_seconds = 0
            status.uptime_formatted = "0s"
        
        # Validate resource usage
        if status.memory_usage_mb < 0:
            status.memory_usage_mb = 0.0
        
        if status.cpu_percent < 0 or status.cpu_percent > 100:
            status.cpu_percent = 0.0
        
        return status
    
    def _enhance_today_summary(self, summary: TodaySummaryResponse) -> TodaySummaryResponse:
        """Apply business logic enhancements to today's summary"""
        # Add success indicators
        if summary.signin_completed and summary.signout_completed:
            # Both completed - add success rate info
            if summary.failed_attempts == 0:
                # Perfect day
                pass
        
        return summary
    
    def _filter_recent_activities(self, activities: List[ActivityListItem]) -> List[ActivityListItem]:
        """Apply filtering to recent activities"""
        # Sort by date (most recent first)
        try:
            activities.sort(key=lambda x: x.date, reverse=True)
        except Exception:
            pass
        
        return activities
    
    def _enhance_quick_stats(self, stats: QuickStats) -> QuickStats:
        """Apply business logic enhancements to quick stats"""
        # Ensure percentages are within valid ranges
        if stats.success_rate < 0:
            stats.success_rate = 0.0
        elif stats.success_rate > 100:
            stats.success_rate = 100.0
        
        # Ensure counts are non-negative
        if stats.current_streak < 0:
            stats.current_streak = 0
        
        if stats.last_7_days_success < 0:
            stats.last_7_days_success = 0
        elif stats.last_7_days_success > 7:
            stats.last_7_days_success = 7
        
        return stats
    
    def _prioritize_alerts(self, alerts: List[Alert]) -> List[Alert]:
        """Prioritize and filter alerts based on business logic"""
        # Sort by priority: error > warning > info > success
        priority_map = {"error": 1, "warning": 2, "info": 3, "success": 4}
        
        try:
            alerts.sort(key=lambda x: (
                priority_map.get(x.type, 5),
                x.timestamp
            ))
        except Exception:
            pass
        
        # Limit to maximum 5 alerts to avoid UI clutter
        return alerts[:5]
    

