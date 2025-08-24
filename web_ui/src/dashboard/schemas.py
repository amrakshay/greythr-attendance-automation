"""
Dashboard API schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Import the main models
from ..models.status import (
    SystemStatusResponse, 
    TodaySummaryResponse, 
    HealthCheckResponse
)
from ..models.activity import ActivityListItem

# Dashboard-specific request models
class RefreshRequest(BaseModel):
    """Request to refresh dashboard data"""
    force: bool = Field(False, description="Force refresh even if cache is valid")

# Dashboard-specific response models
class DashboardOverview(BaseModel):
    """Complete dashboard overview"""
    system_status: SystemStatusResponse = Field(..., description="System status")
    today_summary: TodaySummaryResponse = Field(..., description="Today's attendance summary")
    recent_activities: List[ActivityListItem] = Field(..., description="Recent activities (last 5 days)")
    quick_stats: "QuickStats" = Field(..., description="Quick statistics")
    alerts: List["Alert"] = Field(default_factory=list, description="System alerts")

class QuickStats(BaseModel):
    """Quick statistics for dashboard"""
    total_days_tracked: int = Field(..., description="Total days with attendance data")
    success_rate: float = Field(..., description="Overall success rate percentage")
    current_streak: int = Field(..., description="Current successful attendance streak")
    last_7_days_success: int = Field(..., description="Successful days in last 7 days")
    avg_signin_time: Optional[str] = Field(None, description="Average sign-in time")
    avg_signout_time: Optional[str] = Field(None, description="Average sign-out time")

class Alert(BaseModel):
    """System alert"""
    type: str = Field(..., description="Alert type (info, warning, error, success)")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    timestamp: str = Field(..., description="Alert timestamp")
    dismissible: bool = Field(True, description="Whether alert can be dismissed")
    action_url: Optional[str] = Field(None, description="Optional action URL")
    action_text: Optional[str] = Field(None, description="Optional action button text")

class ServiceStatus(BaseModel):
    """Service status information"""
    is_running: bool = Field(..., description="Whether service is running")
    pid: Optional[int] = Field(None, description="Process ID if running")
    uptime: Optional[str] = Field(None, description="Service uptime")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")
    next_scheduled_action: Optional[str] = Field(None, description="Next scheduled action")
    config_valid: bool = Field(..., description="Whether configuration is valid")

class SystemHealth(BaseModel):
    """Detailed system health"""
    overall_status: str = Field(..., description="Overall health status")
    components: Dict[str, "ComponentHealth"] = Field(..., description="Individual component health")
    last_check: str = Field(..., description="Last health check timestamp")
    issues: List[str] = Field(default_factory=list, description="List of current issues")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")

class ComponentHealth(BaseModel):
    """Individual component health"""
    status: str = Field(..., description="Component status")
    message: str = Field(..., description="Status message")
    last_check: str = Field(..., description="Last check timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")

# Error response models
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: str = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    field: str = Field(..., description="Field with validation error")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value")

class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error: str = Field("validation_error", description="Error type")
    message: str = Field(..., description="General error message")
    details: List[ValidationErrorDetail] = Field(..., description="Validation error details")
    timestamp: str = Field(..., description="Error timestamp")

# Update forward references
DashboardOverview.model_rebuild()
SystemHealth.model_rebuild()

# Configuration models for dashboard settings
class DashboardConfig(BaseModel):
    """Dashboard configuration"""
    auto_refresh_interval: int = Field(30, description="Auto refresh interval in seconds")
    show_alerts: bool = Field(True, description="Whether to show alerts")
    show_quick_stats: bool = Field(True, description="Whether to show quick stats")
    recent_activities_limit: int = Field(5, description="Number of recent activities to show")
    theme: str = Field("light", description="Dashboard theme (light/dark)")

class DashboardSettings(BaseModel):
    """Dashboard user settings"""
    config: DashboardConfig = Field(..., description="Dashboard configuration")
    last_updated: str = Field(..., description="Last update timestamp")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
