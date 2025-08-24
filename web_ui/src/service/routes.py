"""
Service management API routes
FastAPI endpoints for service control operations
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Optional

from .controller import ServiceController
from .repository import ServiceRepository
from .schemas import (
    ServiceActionRequest, ServiceActionResponse, ServiceStatusResponse,
    ManualAttendanceRequest, ManualAttendanceResponse, CatchupRequest, CatchupResponse,
    ServiceInfo, ServiceHealthCheck
)
from ..dependencies import get_greythr_integration_optional

logger = logging.getLogger('webui.service.routes')

# Create router
router = APIRouter(prefix="/api/service", tags=["service"])

# Dependency to get service controller
def get_service_controller(
    integration = Depends(get_greythr_integration_optional)
) -> ServiceController:
    """Get service controller with dependency injection"""
    repository = ServiceRepository(integration.project_path)
    return ServiceController(repository)

# Service status endpoints

@router.get(
    "/status",
    response_model=ServiceStatusResponse,
    summary="Get service status",
    description="Returns current status of the GreytHR attendance service."
)
async def get_service_status(
    controller: ServiceController = Depends(get_service_controller)
):
    """Get current service status"""
    try:
        logger.info("API: Getting service status")
        status = await controller.get_service_status()
        return status
        
    except Exception as e:
        logger.error(f"API error getting service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )

@router.get(
    "/info",
    response_model=ServiceInfo,
    summary="Get detailed service information",
    description="Returns detailed information about the GreytHR service including configuration and health."
)
async def get_service_info(
    controller: ServiceController = Depends(get_service_controller)
):
    """Get detailed service information"""
    try:
        logger.info("API: Getting service info")
        info = await controller.get_service_info()
        return info
        
    except Exception as e:
        logger.error(f"API error getting service info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service info: {str(e)}"
        )

@router.get(
    "/health",
    response_model=ServiceHealthCheck,
    summary="Perform service health check",
    description="Performs a comprehensive health check of the GreytHR service and its dependencies."
)
async def service_health_check(
    controller: ServiceController = Depends(get_service_controller)
):
    """Perform service health check"""
    try:
        logger.info("API: Performing service health check")
        health = await controller.health_check()
        
        # Set appropriate HTTP status based on health
        if health.overall_health == "critical":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is in critical state"
            )
        elif health.overall_health == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Health check failed"
            )
        
        return health
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error in service health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

# Service control endpoints

@router.post(
    "/start",
    response_model=ServiceActionResponse,
    summary="Start the service",
    description="Starts the GreytHR attendance automation service."
)
async def start_service(
    request: ServiceActionRequest = Body(default=ServiceActionRequest(action="start")),
    controller: ServiceController = Depends(get_service_controller)
):
    """Start the GreytHR service"""
    try:
        logger.info(f"API: Starting service (force={request.force})")
        result = await controller.start_service(force=request.force)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error starting service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start service: {str(e)}"
        )

@router.post(
    "/stop",
    response_model=ServiceActionResponse,
    summary="Stop the service",
    description="Stops the GreytHR attendance automation service."
)
async def stop_service(
    request: ServiceActionRequest = Body(default=ServiceActionRequest(action="stop")),
    controller: ServiceController = Depends(get_service_controller)
):
    """Stop the GreytHR service"""
    try:
        logger.info(f"API: Stopping service (force={request.force})")
        result = await controller.stop_service(force=request.force)
        
        return result
        
    except Exception as e:
        logger.error(f"API error stopping service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop service: {str(e)}"
        )

@router.post(
    "/restart",
    response_model=ServiceActionResponse,
    summary="Restart the service",
    description="Restarts the GreytHR attendance automation service."
)
async def restart_service(
    controller: ServiceController = Depends(get_service_controller)
):
    """Restart the GreytHR service"""
    try:
        logger.info("API: Restarting service")
        result = await controller.restart_service()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error restarting service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart service: {str(e)}"
        )

@router.post(
    "/reset",
    response_model=ServiceActionResponse,
    summary="Reset the service",
    description="Resets the GreytHR service, clearing all data and restarting. DESTRUCTIVE OPERATION - requires confirmation."
)
async def reset_service(
    request: ServiceActionRequest,
    controller: ServiceController = Depends(get_service_controller)
):
    """Reset the GreytHR service (destructive operation)"""
    try:
        logger.info(f"API: Resetting service (confirm={request.confirm})")
        
        if not request.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset operation requires explicit confirmation. This will delete all logs, activities, and state data."
            )
        
        result = await controller.reset_service(confirm=request.confirm)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error resetting service: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset service: {str(e)}"
        )

# Manual attendance endpoints

@router.post(
    "/attendance/signin",
    response_model=ManualAttendanceResponse,
    summary="Manual sign-in",
    description="Performs a manual sign-in operation immediately."
)
async def manual_signin(
    request: ManualAttendanceRequest = Body(default=ManualAttendanceRequest(action="signin")),
    controller: ServiceController = Depends(get_service_controller)
):
    """Perform manual sign-in"""
    try:
        logger.info(f"API: Manual sign-in (reason: {request.reason})")
        result = await controller.manual_signin(reason=request.reason)
        
        if not result.success:
            # Don't raise HTTP error for attendance failures - they're business logic failures
            pass
        
        return result
        
    except Exception as e:
        logger.error(f"API error in manual sign-in: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manual sign-in failed: {str(e)}"
        )

@router.post(
    "/attendance/signout",
    response_model=ManualAttendanceResponse,
    summary="Manual sign-out",
    description="Performs a manual sign-out operation immediately."
)
async def manual_signout(
    request: ManualAttendanceRequest = Body(default=ManualAttendanceRequest(action="signout")),
    controller: ServiceController = Depends(get_service_controller)
):
    """Perform manual sign-out"""
    try:
        logger.info(f"API: Manual sign-out (reason: {request.reason})")
        result = await controller.manual_signout(reason=request.reason)
        
        if not result.success:
            # Don't raise HTTP error for attendance failures - they're business logic failures
            pass
        
        return result
        
    except Exception as e:
        logger.error(f"API error in manual sign-out: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manual sign-out failed: {str(e)}"
        )

# Utility endpoints

@router.post(
    "/catchup",
    response_model=CatchupResponse,
    summary="Force catchup check",
    description="Forces a catchup check to handle any missed attendance actions."
)
async def force_catchup(
    request: CatchupRequest = Body(default=CatchupRequest()),
    controller: ServiceController = Depends(get_service_controller)
):
    """Force catchup check"""
    try:
        logger.info(f"API: Force catchup (force={request.force})")
        result = await controller.force_catchup()
        
        return result
        
    except Exception as e:
        logger.error(f"API error in force catchup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Force catchup failed: {str(e)}"
        )

# Simplified endpoints for quick access

@router.get(
    "/status/simple",
    summary="Get simple service status",
    description="Returns a simplified service status for lightweight polling."
)
async def get_simple_service_status(
    controller: ServiceController = Depends(get_service_controller)
):
    """Get simplified service status"""
    try:
        status = await controller.get_service_status()
        
        return {
            "is_running": status.is_running,
            "status": status.status,
            "daemon_running": status.daemon_running,
            "pid": status.pid,
            "uptime": status.uptime
        }
        
    except Exception as e:
        logger.error(f"API error getting simple service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )

@router.post(
    "/quick-action/{action}",
    summary="Quick service action",
    description="Performs a quick service action without detailed request body."
)
async def quick_service_action(
    action: str,
    confirm: bool = False,
    controller: ServiceController = Depends(get_service_controller)
):
    """Perform quick service action"""
    try:
        logger.info(f"API: Quick action '{action}' (confirm={confirm})")
        
        if action == "start":
            result = await controller.start_service()
        elif action == "stop":
            result = await controller.stop_service()
        elif action == "restart":
            result = await controller.restart_service()
        elif action == "reset":
            if not confirm:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset requires confirmation parameter"
                )
            result = await controller.reset_service(confirm=True)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {action}"
            )
        
        return {
            "action": action,
            "success": result.success,
            "message": result.message,
            "timestamp": result.timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error in quick action {action}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick action {action} failed: {str(e)}"
        )
