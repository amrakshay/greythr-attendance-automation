"""
Dashboard API schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Import the main models
from ..models.status import SystemStatusResponse, TodaySummaryResponse
from ..models.activity import ActivityListItem

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

# Update forward references
DashboardOverview.model_rebuild()