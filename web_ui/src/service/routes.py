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
    ServiceActionRequest, ServiceActionResponse, ServiceStatusResponse
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