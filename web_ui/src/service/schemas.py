"""
Service management API schemas
Pydantic models for service control operations
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Request models
class ServiceActionRequest(BaseModel):
    """Request to perform a service action"""
    action: str = Field(..., description="Action to perform (start, stop, restart, reset)")
    confirm: bool = Field(False, description="Confirmation for destructive actions")
    force: bool = Field(False, description="Force action even if risky")

class ManualAttendanceRequest(BaseModel):
    """Request for manual attendance action"""
    action: str = Field(..., description="Attendance action (signin, signout)")
    reason: Optional[str] = Field(None, description="Optional reason for manual action")

class CatchupRequest(BaseModel):
    """Request for catchup check"""
    force: bool = Field(False, description="Force catchup even if not needed")

# Response models
class ServiceActionResponse(BaseModel):
    """Response from service action"""
    success: bool = Field(..., description="Whether action was successful")
    action: str = Field(..., description="Action that was performed")
    message: str = Field(..., description="Human-readable result message")
    details: Optional[str] = Field(None, description="Additional details")
    timestamp: str = Field(..., description="Action timestamp")
    duration_seconds: Optional[float] = Field(None, description="Action duration")

class ServiceStatusResponse(BaseModel):
    """Current service status"""
    is_running: bool = Field(..., description="Whether service is running")
    pid: Optional[int] = Field(None, description="Process ID if running")
    status: str = Field(..., description="Service status description")
    uptime: Optional[str] = Field(None, description="Service uptime")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    next_scheduled_action: Optional[str] = Field(None, description="Next scheduled action")
    daemon_running: bool = Field(..., description="Whether daemon is active")

class ManualAttendanceResponse(BaseModel):
    """Response from manual attendance action"""
    success: bool = Field(..., description="Whether attendance action was successful")
    action: str = Field(..., description="Attendance action performed")
    message: str = Field(..., description="Result message")
    timestamp: str = Field(..., description="Action timestamp")
    attendance_time: Optional[str] = Field(None, description="Recorded attendance time")
    attempts: int = Field(..., description="Number of attempts made")

class CatchupResponse(BaseModel):
    """Response from catchup check"""
    success: bool = Field(..., description="Whether catchup was successful")
    actions_taken: List[str] = Field(..., description="List of actions taken during catchup")
    message: str = Field(..., description="Summary message")
    timestamp: str = Field(..., description="Catchup timestamp")
    signin_attempted: bool = Field(False, description="Whether signin was attempted")
    signout_attempted: bool = Field(False, description="Whether signout was attempted")

class ServiceInfo(BaseModel):
    """Detailed service information"""
    service_name: str = Field(..., description="Service name")
    is_installed: bool = Field(..., description="Whether service is installed")
    is_running: bool = Field(..., description="Whether service is running")
    pid: Optional[int] = Field(None, description="Process ID")
    status: str = Field(..., description="Service status")
    config_valid: bool = Field(..., description="Whether configuration is valid")
    script_path: str = Field(..., description="Path to service script")
    project_path: str = Field(..., description="Path to GreytHR project")
    uptime_seconds: int = Field(0, description="Uptime in seconds")
    last_restart: Optional[str] = Field(None, description="Last restart timestamp")

class OperationProgress(BaseModel):
    """Progress information for long-running operations"""
    operation_id: str = Field(..., description="Unique operation identifier")
    operation: str = Field(..., description="Operation being performed")
    status: str = Field(..., description="Current status (running, completed, failed)")
    progress_percent: int = Field(..., description="Progress percentage (0-100)")
    message: str = Field(..., description="Current status message")
    started_at: str = Field(..., description="Operation start time")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")

# Configuration models
class ServiceConfig(BaseModel):
    """Service configuration"""
    signin_time: str = Field(..., description="Configured sign-in time")
    signout_time: str = Field(..., description="Configured sign-out time")
    test_mode: bool = Field(False, description="Test mode enabled")
    max_retry_attempts: int = Field(5, description="Maximum retry attempts")
    base_retry_delay: int = Field(300, description="Base retry delay in seconds")
    auto_restart: bool = Field(True, description="Auto-restart on failure")
    timezone: str = Field("Asia/Kolkata", description="Timezone")

class ServiceConfigUpdateRequest(BaseModel):
    """Request to update service configuration"""
    signin_time: Optional[str] = Field(None, description="New sign-in time")
    signout_time: Optional[str] = Field(None, description="New sign-out time")
    test_mode: Optional[bool] = Field(None, description="Enable/disable test mode")
    max_retry_attempts: Optional[int] = Field(None, description="Max retry attempts")
    base_retry_delay: Optional[int] = Field(None, description="Base retry delay")
    restart_service: bool = Field(False, description="Restart service after config change")

# Error models
class ServiceError(BaseModel):
    """Service operation error"""
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: str = Field(..., description="Error timestamp")
    operation: Optional[str] = Field(None, description="Operation that failed")
    recoverable: bool = Field(True, description="Whether error is recoverable")
    suggestions: List[str] = Field(default_factory=list, description="Suggested fixes")

# Validation models
class ServiceHealthCheck(BaseModel):
    """Service health check result"""
    overall_health: str = Field(..., description="Overall health status")
    checks: Dict[str, bool] = Field(..., description="Individual health checks")
    issues: List[str] = Field(default_factory=list, description="Health issues found")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    last_check: str = Field(..., description="Last health check timestamp")
    check_duration_ms: int = Field(..., description="Health check duration in milliseconds")
