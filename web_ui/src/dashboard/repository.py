"""
Dashboard repository
Data access layer for dashboard functionality
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio

from ..database.connection import StateRepository, ActivitiesRepository
from ..models.status import SystemStatus, SystemStatusResponse, TodaySummaryResponse
from ..models.activity import AttendanceActivity, ActivityListItem
from ..app_utils import format_uptime, format_file_size
from .schemas import QuickStats, Alert, DashboardOverview

logger = logging.getLogger('webui.dashboard.repository')

class DashboardRepository:
    """Repository for dashboard data operations"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.state_repo = StateRepository(project_path)
        self.activities_repo = ActivitiesRepository(project_path)
        
    async def get_system_status(self) -> Optional[SystemStatusResponse]:
        """Get current system status"""
        try:
            state_data = await self.state_repo.get_current_state()
            if not state_data:
                logger.warning("No state data available")
                return self._get_fallback_status()
            
            # Parse the state data
            script_info = state_data.get('script', {})
            system_info = state_data.get('system', {})
            statistics = state_data.get('statistics', {})
            
            # Calculate uptime
            uptime_seconds = statistics.get('uptime_seconds', 0)
            uptime_formatted = format_uptime(uptime_seconds)
            
            return SystemStatusResponse(
                status=script_info.get('status', 'unknown'),
                daemon_running=state_data.get('schedule', {}).get('daemon_running', False),
                uptime_seconds=uptime_seconds,
                uptime_formatted=uptime_formatted,
                memory_usage_mb=system_info.get('memory_usage_mb', 0.0),
                cpu_percent=system_info.get('cpu_percent', 0.0),
                last_updated=state_data.get('last_updated', datetime.now().isoformat()),
                script_pid=script_info.get('pid')
            )
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return self._get_fallback_status()
    
    async def get_today_summary(self) -> Optional[TodaySummaryResponse]:
        """Get today's attendance summary"""
        try:
            state_data = await self.state_repo.get_current_state()
            if not state_data:
                return self._get_fallback_today_summary()
            
            today_summary = state_data.get('today_summary', {})
            if not today_summary:
                return self._get_fallback_today_summary()
            
            # Format times if available
            signin_time_formatted = None
            signout_time_formatted = None
            
            if today_summary.get('signin_time'):
                try:
                    signin_dt = datetime.fromisoformat(today_summary['signin_time'])
                    signin_time_formatted = signin_dt.strftime('%I:%M %p')
                except:
                    pass
            
            if today_summary.get('signout_time'):
                try:
                    signout_dt = datetime.fromisoformat(today_summary['signout_time'])
                    signout_time_formatted = signout_dt.strftime('%I:%M %p')
                except:
                    pass
            
            # Calculate total attempts and failures
            signin_attempts = today_summary.get('signin_attempts', 0)
            signout_attempts = today_summary.get('signout_attempts', 0)
            signin_failed = today_summary.get('signin_failed_attempts', 0)
            signout_failed = today_summary.get('signout_failed_attempts', 0)
            
            total_attempts = signin_attempts + signout_attempts
            failed_attempts = signin_failed + signout_failed
            
            # Determine next retry
            next_retry = None
            if today_summary.get('signin_next_retry'):
                next_retry = today_summary['signin_next_retry']
            elif today_summary.get('signout_next_retry'):
                next_retry = today_summary['signout_next_retry']
            
            return TodaySummaryResponse(
                date=today_summary.get('date', datetime.now().strftime('%Y-%m-%d')),
                signin_completed=today_summary.get('signin_status', '').startswith('✅'),
                signout_completed=today_summary.get('signout_status', '').startswith('✅'),
                signin_status=today_summary.get('signin_status', '❌ Pending'),
                signout_status=today_summary.get('signout_status', '❌ Pending'),
                signin_time=signin_time_formatted,
                signout_time=signout_time_formatted,
                total_attempts=total_attempts,
                failed_attempts=failed_attempts,
                next_retry=next_retry
            )
            
        except Exception as e:
            logger.error(f"Error getting today summary: {e}")
            return self._get_fallback_today_summary()
    
    async def get_recent_activities(self, limit: int = 5) -> List[ActivityListItem]:
        """Get recent activity items"""
        try:
            activity_dates = await self.activities_repo.list_activity_files()
            recent_activities = []
            
            for date in activity_dates[:limit]:
                activity_data = await self.activities_repo.get_activity_by_date(date)
                if activity_data:
                    activity_item = self._format_activity_item(activity_data)
                    recent_activities.append(activity_item)
            
            return recent_activities
            
        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            return []
    
    async def get_quick_stats(self) -> QuickStats:
        """Get quick statistics for dashboard"""
        try:
            # Get all activity files
            activity_dates = await self.activities_repo.list_activity_files()
            total_days = len(activity_dates)
            
            if total_days == 0:
                return QuickStats(
                    total_days_tracked=0,
                    success_rate=0.0,
                    current_streak=0,
                    last_7_days_success=0,
                    avg_signin_time=None,
                    avg_signout_time=None
                )
            
            successful_days = 0
            current_streak = 0
            last_7_days_success = 0
            signin_times = []
            signout_times = []
            
            # Process activities
            for i, date in enumerate(activity_dates):
                activity_data = await self.activities_repo.get_activity_by_date(date)
                if activity_data:
                    signin_complete = activity_data.get('signin_completed', False)
                    signout_complete = activity_data.get('signout_completed', False)
                    
                    # Count successful days (both signin and signout)
                    if signin_complete and signout_complete:
                        successful_days += 1
                        
                        # Calculate current streak (from most recent)
                        if i < len(activity_dates) and current_streak == i:
                            current_streak += 1
                        
                        # Count last 7 days
                        if i < 7:
                            last_7_days_success += 1
                    else:
                        # Break streak if not successful
                        if i < len(activity_dates) and current_streak == i:
                            pass  # Stop counting streak
                    
                    # Collect times for averages
                    if activity_data.get('signin_time'):
                        signin_times.append(activity_data['signin_time'])
                    if activity_data.get('signout_time'):
                        signout_times.append(activity_data['signout_time'])
            
            # Calculate success rate
            success_rate = (successful_days / total_days * 100) if total_days > 0 else 0.0
            
            # Calculate average times
            avg_signin_time = self._calculate_average_time(signin_times)
            avg_signout_time = self._calculate_average_time(signout_times)
            
            return QuickStats(
                total_days_tracked=total_days,
                success_rate=round(success_rate, 1),
                current_streak=current_streak,
                last_7_days_success=last_7_days_success,
                avg_signin_time=avg_signin_time,
                avg_signout_time=avg_signout_time
            )
            
        except Exception as e:
            logger.error(f"Error calculating quick stats: {e}")
            return QuickStats(
                total_days_tracked=0,
                success_rate=0.0,
                current_streak=0,
                last_7_days_success=0,
                avg_signin_time=None,
                avg_signout_time=None
            )
    
    async def get_system_alerts(self) -> List[Alert]:
        """Get system alerts"""
        alerts = []
        
        try:
            # Check state data for issues
            state_data = await self.state_repo.get_current_state()
            
            if not state_data:
                alerts.append(Alert(
                    type="warning",
                    title="No State Data",
                    message="Cannot read system state file. Check if GreytHR service is running.",
                    timestamp=datetime.now().isoformat()
                ))
                return alerts
            
            # Check for errors
            errors = state_data.get('errors', {})
            if errors.get('last_error'):
                alerts.append(Alert(
                    type="error",
                    title="System Error",
                    message=f"Last error: {errors['last_error']}",
                    timestamp=errors.get('last_error_time', datetime.now().isoformat())
                ))
            
            # Check daemon status
            daemon_running = state_data.get('schedule', {}).get('daemon_running', False)
            if not daemon_running:
                alerts.append(Alert(
                    type="warning",
                    title="Service Not Running",
                    message="GreytHR attendance automation service is not running.",
                    timestamp=datetime.now().isoformat(),
                    action_url="/api/service/start",
                    action_text="Start Service"
                ))
            
            # Check for pending retries
            today_summary = state_data.get('today_summary', {})
            if today_summary.get('signin_next_retry') or today_summary.get('signout_next_retry'):
                alerts.append(Alert(
                    type="info",
                    title="Retry Scheduled",
                    message="Attendance action will be retried automatically.",
                    timestamp=datetime.now().isoformat()
                ))
            
            # Uptime info is available in the main dashboard - no alert needed
            
        except Exception as e:
            logger.error(f"Error getting system alerts: {e}")
            alerts.append(Alert(
                type="error",
                title="Alert System Error",
                message=f"Failed to check system alerts: {str(e)}",
                timestamp=datetime.now().isoformat()
            ))
        
        return alerts
    

    
    # Helper methods
    
    def _get_fallback_status(self) -> SystemStatusResponse:
        """Get fallback status when no data is available"""
        return SystemStatusResponse(
            status="unknown",
            daemon_running=False,
            uptime_seconds=0,
            uptime_formatted="0s",
            memory_usage_mb=0.0,
            cpu_percent=0.0,
            last_updated=datetime.now().isoformat(),
            script_pid=None
        )
    
    def _get_fallback_today_summary(self) -> TodaySummaryResponse:
        """Get fallback today summary when no data is available"""
        return TodaySummaryResponse(
            date=datetime.now().strftime('%Y-%m-%d'),
            signin_completed=False,
            signout_completed=False,
            signin_status="❌ No Data",
            signout_status="❌ No Data",
            signin_time=None,
            signout_time=None,
            total_attempts=0,
            failed_attempts=0,
            next_retry=None
        )
    
    def _format_activity_item(self, activity_data: Dict[str, Any]) -> ActivityListItem:
        """Format activity data for list display"""
        date = activity_data.get('date', 'unknown')
        signin_complete = activity_data.get('signin_completed', False)
        signout_complete = activity_data.get('signout_completed', False)
        
        # Determine status
        if signin_complete and signout_complete:
            status = "Complete"
            status_color = "success"
        elif signin_complete or signout_complete:
            status = "Partial"
            status_color = "warning"
        else:
            status = "Failed"
            status_color = "danger"
        
        # Format times
        signin_time_formatted = None
        signout_time_formatted = None
        
        if activity_data.get('signin_time'):
            try:
                signin_dt = datetime.fromisoformat(activity_data['signin_time'])
                signin_time_formatted = signin_dt.strftime('%I:%M %p')
            except:
                pass
        
        if activity_data.get('signout_time'):
            try:
                signout_dt = datetime.fromisoformat(activity_data['signout_time'])
                signout_time_formatted = signout_dt.strftime('%I:%M %p')
            except:
                pass
        
        # Day of week
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            day_of_week = date_obj.strftime('%A')
        except:
            day_of_week = "Unknown"
        
        # Total attempts
        total_attempts = (
            activity_data.get('signin_attempts', 0) + 
            activity_data.get('signout_attempts', 0)
        )
        
        # Check for errors
        has_errors = bool(
            activity_data.get('signin_last_error') or 
            activity_data.get('signout_last_error')
        )
        
        return ActivityListItem(
            date=date,
            day_of_week=day_of_week,
            signin_completed=signin_complete,
            signout_completed=signout_complete,
            signin_time_formatted=signin_time_formatted,
            signout_time_formatted=signout_time_formatted,
            status=status,
            status_color=status_color,
            total_attempts=total_attempts,
            has_errors=has_errors
        )
    
    def _calculate_average_time(self, times: List[str]) -> Optional[str]:
        """Calculate average time from list of ISO timestamps"""
        if not times:
            return None
        
        try:
            parsed_times = []
            for time_str in times:
                dt = datetime.fromisoformat(time_str)
                # Convert to minutes since midnight
                minutes = dt.hour * 60 + dt.minute
                parsed_times.append(minutes)
            
            avg_minutes = sum(parsed_times) / len(parsed_times)
            avg_hour = int(avg_minutes // 60)
            avg_min = int(avg_minutes % 60)
            
            return f"{avg_hour:02d}:{avg_min:02d}"
            
        except Exception as e:
            logger.error(f"Error calculating average time: {e}")
            return None
