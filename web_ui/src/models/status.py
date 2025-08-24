"""
Pydantic models for system status data
Based on the current_state.json structure from GreytHR
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ScriptInfo(BaseModel):
    """Script execution information"""
    status: str = Field(..., description="Current script status")
    start_time: Optional[str] = Field(None, description="Script start time (ISO format)")
    pid: Optional[int] = Field(None, description="Process ID")
    python_version: Optional[str] = Field(None, description="Python version")
    platform: Optional[str] = Field(None, description="Operating system platform")
    hostname: Optional[str] = Field(None, description="System hostname")
    working_directory: Optional[str] = Field(None, description="Working directory")
    details: Optional[str] = Field(None, description="Additional status details")

class CurrentOperation(BaseModel):
    """Current operation information"""
    action: str = Field(..., description="Current action being performed")
    details: Optional[str] = Field(None, description="Operation details")
    start_time: Optional[str] = Field(None, description="Operation start time")
    progress: Optional[int] = Field(0, description="Progress percentage (0-100)")

class Configuration(BaseModel):
    """System configuration"""
    signin_time: Optional[str] = Field(None, description="Configured sign-in time")
    signout_time: Optional[str] = Field(None, description="Configured sign-out time")
    test_mode: Optional[bool] = Field(False, description="Test mode enabled")
    timezone: Optional[str] = Field("Asia/Kolkata", description="System timezone")
    max_retry_attempts: Optional[int] = Field(5, description="Maximum retry attempts")
    base_retry_delay_minutes: Optional[int] = Field(5, description="Base retry delay in minutes")

class ScheduleInfo(BaseModel):
    """Schedule information"""
    next_signin: Optional[str] = Field(None, description="Next scheduled sign-in time")
    next_signout: Optional[str] = Field(None, description="Next scheduled sign-out time")
    daemon_running: Optional[bool] = Field(False, description="Daemon running status")
    scheduler_active: Optional[bool] = Field(False, description="Scheduler active status")

class TodaySummary(BaseModel):
    """Today's attendance summary"""
    date: Optional[str] = Field(None, description="Date (YYYY-MM-DD)")
    signin_status: Optional[str] = Field(None, description="Sign-in status description")
    signout_status: Optional[str] = Field(None, description="Sign-out status description")
    signin_time: Optional[str] = Field(None, description="Actual sign-in time")
    signout_time: Optional[str] = Field(None, description="Actual sign-out time")
    signin_attempts: Optional[int] = Field(0, description="Number of sign-in attempts")
    signout_attempts: Optional[int] = Field(0, description="Number of sign-out attempts")
    signin_failed_attempts: Optional[int] = Field(0, description="Failed sign-in attempts")
    signout_failed_attempts: Optional[int] = Field(0, description="Failed sign-out attempts")
    signin_last_error: Optional[str] = Field(None, description="Last sign-in error")
    signout_last_error: Optional[str] = Field(None, description="Last sign-out error")
    signin_next_retry: Optional[str] = Field(None, description="Next sign-in retry time")
    signout_next_retry: Optional[str] = Field(None, description="Next sign-out retry time")

class Statistics(BaseModel):
    """System statistics"""
    total_operations: Optional[int] = Field(0, description="Total operations performed")
    successful_operations: Optional[int] = Field(0, description="Successful operations")
    failed_operations: Optional[int] = Field(0, description="Failed operations")
    signin_attempts: Optional[int] = Field(0, description="Total sign-in attempts")
    signout_attempts: Optional[int] = Field(0, description="Total sign-out attempts")
    last_successful_signin: Optional[str] = Field(None, description="Last successful sign-in time")
    last_successful_signout: Optional[str] = Field(None, description="Last successful sign-out time")
    uptime_seconds: Optional[int] = Field(0, description="System uptime in seconds")

class SystemResources(BaseModel):
    """System resource usage"""
    memory_usage_mb: Optional[float] = Field(0.0, description="Memory usage in MB")
    cpu_percent: Optional[float] = Field(0.0, description="CPU usage percentage")
    disk_usage_percent: Optional[float] = Field(0.0, description="Disk usage percentage")

class ErrorInfo(BaseModel):
    """Error information"""
    last_error: Optional[str] = Field(None, description="Last error message")
    last_error_time: Optional[str] = Field(None, description="Last error timestamp")
    retry_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Retry information")

class SystemStatus(BaseModel):
    """Complete system status model"""
    script: Optional[ScriptInfo] = Field(None, description="Script information")
    current_operation: Optional[CurrentOperation] = Field(None, description="Current operation")
    configuration: Optional[Configuration] = Field(None, description="System configuration")
    schedule: Optional[ScheduleInfo] = Field(None, description="Schedule information")
    today_summary: Optional[TodaySummary] = Field(None, description="Today's attendance summary")
    statistics: Optional[Statistics] = Field(None, description="System statistics")
    system: Optional[SystemResources] = Field(None, description="System resources")
    errors: Optional[ErrorInfo] = Field(None, description="Error information")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")

# Response models for API endpoints
class SystemStatusResponse(BaseModel):
    """API response for system status"""
    status: str = Field(..., description="Overall system status")
    daemon_running: bool = Field(..., description="Whether daemon is running")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    uptime_formatted: str = Field(..., description="Human-readable uptime")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_percent: float = Field(..., description="CPU usage percentage")
    last_updated: str = Field(..., description="Last update timestamp")
    script_pid: Optional[int] = Field(None, description="Script process ID")
    
class TodaySummaryResponse(BaseModel):
    """API response for today's summary"""
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    signin_completed: bool = Field(..., description="Sign-in completed today")
    signout_completed: bool = Field(..., description="Sign-out completed today")
    signin_status: str = Field(..., description="Sign-in status with icon")
    signout_status: str = Field(..., description="Sign-out status with icon")
    signin_time: Optional[str] = Field(None, description="Sign-in time (formatted)")
    signout_time: Optional[str] = Field(None, description="Sign-out time (formatted)")
    total_attempts: int = Field(..., description="Total attempts today")
    failed_attempts: int = Field(..., description="Failed attempts today")
    next_retry: Optional[str] = Field(None, description="Next retry time if applicable")

class HealthCheckResponse(BaseModel):
    """API response for health check"""
    status: str = Field(..., description="Health status")
    checks: Dict[str, bool] = Field(..., description="Individual health checks")
    timestamp: str = Field(..., description="Health check timestamp")
    greythr_project_path: Optional[str] = Field(None, description="GreytHR project path")
    message: Optional[str] = Field(None, description="Additional status message")
