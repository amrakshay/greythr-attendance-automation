"""
Export API routes
FastAPI endpoints for data export functionality
"""

import logging
import json
import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional

from ..activities.controller import ActivitiesController
from ..activities.repository import ActivitiesRepository
from ..logs.repository import LogsRepository
from ..dependencies import get_greythr_integration_optional

logger = logging.getLogger('webui.export.routes')

# Create router
router = APIRouter(prefix="/api/export", tags=["export"])

# Dependencies
def get_activities_controller(
    integration = Depends(get_greythr_integration_optional)
) -> ActivitiesController:
    """Get activities controller"""
    repository = ActivitiesRepository(integration.project_path)
    return ActivitiesController(repository)

def get_logs_repository(
    integration = Depends(get_greythr_integration_optional)
) -> LogsRepository:
    """Get logs repository"""
    return LogsRepository(integration.project_path)

@router.get(
    "/",
    summary="Export data",
    description="Export various types of data in different formats."
)
async def export_data(
    type: str = Query(..., description="Type of data to export: attendance, logs, config"),
    format: str = Query("json", description="Export format: json, csv"),
    start_date: Optional[str] = Query(None, description="Start date for data range (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for data range (YYYY-MM-DD)"),
    activities_controller: ActivitiesController = Depends(get_activities_controller),
    logs_repository: LogsRepository = Depends(get_logs_repository)
):
    """Export data in various formats"""
    try:
        logger.info(f"API: Exporting {type} data in {format} format")
        
        if type not in ['attendance', 'logs', 'config']:
            raise ValueError("Export type must be 'attendance', 'logs', or 'config'")
        
        if format not in ['json', 'csv']:
            raise ValueError("Export format must be 'json' or 'csv'")
        
        # Export attendance data
        if type == 'attendance':
            if not start_date or not end_date:
                raise ValueError("start_date and end_date are required for attendance export")
            
            export_data = await activities_controller.export_activities(start_date, end_date, format)
            
            if format == 'json':
                content = json.dumps(export_data, indent=2)
                media_type = "application/json"
                filename = f"greythr-attendance-{start_date}-to-{end_date}.json"
            else:  # csv
                content = _convert_attendance_to_csv(export_data)
                media_type = "text/csv"
                filename = f"greythr-attendance-{start_date}-to-{end_date}.csv"
        
        # Export logs data
        elif type == 'logs':
            logs_data = await logs_repository.get_recent_logs(limit=10000)
            
            if format == 'json':
                content = json.dumps(logs_data, indent=2)
                media_type = "application/json"
                filename = "greythr-logs.json"
            else:  # csv
                content = _convert_logs_to_csv(logs_data)
                media_type = "text/csv"
                filename = "greythr-logs.csv"
        
        # Export configuration (placeholder)
        else:  # config
            config_data = {
                "export_info": {
                    "type": "configuration",
                    "exported_at": "2024-01-01T00:00:00",
                    "note": "Configuration export not yet implemented"
                },
                "config": {
                    "service_enabled": True,
                    "auto_signin": True,
                    "auto_signout": True
                }
            }
            
            if format == 'json':
                content = json.dumps(config_data, indent=2)
                media_type = "application/json"
                filename = "greythr-config.json"
            else:  # csv
                content = "type,key,value\nconfig,service_enabled,true\nconfig,auto_signin,true\nconfig,auto_signout,true\n"
                media_type = "text/csv"
                filename = "greythr-config.csv"
        
        # Return file download response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except ValueError as e:
        logger.error(f"Validation error in export API: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"API error in export: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}"
        )

def _convert_attendance_to_csv(data: dict) -> str:
    """Convert attendance data to CSV format"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Day', 'Time', 'Type', 'Status', 'Message', 'Details'])
    
    # Write activities
    for activity in data.get('activities', []):
        writer.writerow([
            activity.get('date', ''),
            activity.get('day_of_week', ''),
            activity.get('time', ''),
            activity.get('type', ''),
            activity.get('status', ''),
            activity.get('message', ''),
            activity.get('details', '')
        ])
    
    return output.getvalue()

def _convert_logs_to_csv(data: dict) -> str:
    """Convert logs data to CSV format"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Timestamp', 'Level', 'Message', 'File'])
    
    # Write log entries
    for log in data.get('logs', []):
        writer.writerow([
            log.get('timestamp', ''),
            log.get('level', ''),
            log.get('message', ''),
            log.get('file', '')
        ])
    
    return output.getvalue()
