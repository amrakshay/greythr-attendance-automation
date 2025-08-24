"""
Service management API schemas
Pydantic models for service control operations
"""

from pydantic import BaseModel, Field
from typing import Optional

# Request models
class ServiceActionRequest(BaseModel):
    """Request to perform a service action"""
    action: str = Field(..., description="Action to perform (start, stop, restart)")
    force: bool = Field(False, description="Force action even if risky")

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