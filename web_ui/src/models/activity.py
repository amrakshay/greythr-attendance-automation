"""
Pydantic models for activity/attendance data
Based on the attendance_YYYY-MM-DD.json structure from GreytHR
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AttendanceActivity(BaseModel):
    """Single day attendance activity model"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    signin_completed: bool = Field(False, description="Sign-in completed for this date")
    signout_completed: bool = Field(False, description="Sign-out completed for this date")
    signin_time: Optional[str] = Field(None, description="Actual sign-in time (ISO format)")
    signout_time: Optional[str] = Field(None, description="Actual sign-out time (ISO format)")
    signin_attempts: int = Field(0, description="Number of sign-in attempts")
    signout_attempts: int = Field(0, description="Number of sign-out attempts")
    signin_failed_attempts: int = Field(0, description="Failed sign-in attempts")
    signout_failed_attempts: int = Field(0, description="Failed sign-out attempts")
    signin_next_retry: Optional[str] = Field(None, description="Next sign-in retry time")
    signout_next_retry: Optional[str] = Field(None, description="Next sign-out retry time")
    signin_last_error: Optional[str] = Field(None, description="Last sign-in error message")
    signout_last_error: Optional[str] = Field(None, description="Last sign-out error message")
    last_updated: str = Field(..., description="Last update timestamp")

class ActivityListItem(BaseModel):
    """Activity list item for API responses"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    day_of_week: str = Field(..., description="Day of the week")
    signin_completed: bool = Field(..., description="Sign-in completed")
    signout_completed: bool = Field(..., description="Sign-out completed")
    signin_time_formatted: Optional[str] = Field(None, description="Formatted sign-in time")
    signout_time_formatted: Optional[str] = Field(None, description="Formatted sign-out time")
    status: str = Field(..., description="Overall day status")
    status_color: str = Field(..., description="Status color for UI")
    total_attempts: int = Field(..., description="Total attempts for the day")
    has_errors: bool = Field(..., description="Whether there were any errors")

class ActivitySummary(BaseModel):
    """Summary statistics for activities"""
    total_days: int = Field(..., description="Total days with activity")
    successful_days: int = Field(..., description="Days with both signin/signout completed")
    partial_days: int = Field(..., description="Days with only signin or signout")
    failed_days: int = Field(..., description="Days with no successful attendance")
    success_rate: float = Field(..., description="Success rate percentage")
    total_attempts: int = Field(..., description="Total attempts across all days")
    total_failures: int = Field(..., description="Total failed attempts")
    average_signin_time: Optional[str] = Field(None, description="Average sign-in time")
    average_signout_time: Optional[str] = Field(None, description="Average sign-out time")
    date_range: str = Field(..., description="Date range of the data")

# API Response Models
class ActivityResponse(BaseModel):
    """API response for single activity"""
    activity: AttendanceActivity = Field(..., description="Activity data")
    formatted: ActivityListItem = Field(..., description="Formatted data for display")

class ActivitiesListResponse(BaseModel):
    """API response for activities list"""
    activities: List[ActivityListItem] = Field(..., description="List of activities")
    pagination: "PaginationInfo" = Field(..., description="Pagination information")
    summary: ActivitySummary = Field(..., description="Summary statistics")

class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int = Field(..., description="Current page (0-based)")
    size: int = Field(..., description="Page size")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class ActivityStatsResponse(BaseModel):
    """API response for activity statistics"""
    summary: ActivitySummary = Field(..., description="Activity summary")
    recent_activities: List[ActivityListItem] = Field(..., description="Recent activities (last 7 days)")
    weekly_stats: List["WeeklyStats"] = Field(..., description="Weekly statistics")

class WeeklyStats(BaseModel):
    """Weekly statistics"""
    week_start: str = Field(..., description="Week start date")
    week_end: str = Field(..., description="Week end date")
    days_completed: int = Field(..., description="Days with full attendance")
    days_partial: int = Field(..., description="Days with partial attendance")
    days_missed: int = Field(..., description="Days with no attendance")
    success_rate: float = Field(..., description="Week success rate percentage")

# Update forward references
ActivitiesListResponse.model_rebuild()
ActivityStatsResponse.model_rebuild()

# Calendar view models
class CalendarDay(BaseModel):
    """Calendar day representation"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    day_number: int = Field(..., description="Day of month")
    is_current_month: bool = Field(..., description="Whether day is in current month")
    is_today: bool = Field(..., description="Whether day is today")
    is_weekend: bool = Field(..., description="Whether day is weekend")
    attendance_status: str = Field(..., description="Attendance status for the day")
    status_color: str = Field(..., description="Color for the status")
    signin_time: Optional[str] = Field(None, description="Sign-in time if available")
    signout_time: Optional[str] = Field(None, description="Sign-out time if available")
    has_data: bool = Field(..., description="Whether there is attendance data for this day")

class CalendarMonth(BaseModel):
    """Calendar month representation"""
    year: int = Field(..., description="Year")
    month: int = Field(..., description="Month (1-12)")
    month_name: str = Field(..., description="Month name")
    days: List[CalendarDay] = Field(..., description="Days in the calendar view")
    summary: "MonthSummary" = Field(..., description="Month summary")

class MonthSummary(BaseModel):
    """Monthly summary"""
    total_working_days: int = Field(..., description="Total working days in month")
    attended_days: int = Field(..., description="Days with attendance")
    partial_days: int = Field(..., description="Days with partial attendance")
    missed_days: int = Field(..., description="Days missed")
    attendance_rate: float = Field(..., description="Attendance rate percentage")

# Update forward references
CalendarMonth.model_rebuild()
