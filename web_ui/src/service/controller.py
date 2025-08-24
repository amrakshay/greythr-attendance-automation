"""
Service management controller
Business logic layer for service control operations
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from .repository import ServiceRepository
from .schemas import ServiceActionResponse, ServiceStatusResponse

logger = logging.getLogger('webui.service.controller')

class ServiceController:
    """Controller for service management business logic"""
    
    def __init__(self, repository: ServiceRepository):
        self.repository = repository
    
    async def get_service_status(self) -> ServiceStatusResponse:
        """Get current service status with business logic validation"""
        try:
            logger.info("Getting service status")
            status = await self.repository.get_service_status()
            
            # Apply business logic enhancements
            enhanced_status = self._enhance_service_status(status)
            return enhanced_status
            
        except Exception as e:
            logger.error(f"Error in get_service_status controller: {e}")
            return ServiceStatusResponse(
                is_running=False,
                pid=None,
                status=f"Controller error: {str(e)}",
                uptime=None,
                last_activity=None,
                next_scheduled_action=None,
                daemon_running=False
            )
    
    async def start_service(self, force: bool = False) -> ServiceActionResponse:
        """Start service with business logic validation"""
        try:
            logger.info(f"Starting service (force={force})")
            
            # Validate prerequisites before starting
            validation = await self._validate_service_prerequisites()
            if not validation['valid']:
                return ServiceActionResponse(
                    success=False,
                    action="start",
                    message=f"Service start blocked: {validation['message']}",
                    timestamp=datetime.now().isoformat()
                )
            
            # Check if already running (unless forced)
            if not force:
                current_status = await self.repository.get_service_status()
                if current_status.is_running:
                    return ServiceActionResponse(
                        success=False,
                        action="start",
                        message="Service is already running. Use force=true to restart.",
                        timestamp=datetime.now().isoformat()
                    )
            
            # Execute start action
            result = await self.repository.start_service()
            
            # Apply business logic enhancements
            enhanced_result = self._enhance_action_result(result, "start")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in start_service controller: {e}")
            return ServiceActionResponse(
                success=False,
                action="start",
                message=f"Start service failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def stop_service(self, force: bool = False) -> ServiceActionResponse:
        """Stop service with business logic validation"""
        try:
            logger.info(f"Stopping service (force={force})")
            
            # Check if already stopped (unless forced)
            if not force:
                current_status = await self.repository.get_service_status()
                if not current_status.is_running:
                    return ServiceActionResponse(
                        success=True,
                        action="stop",
                        message="Service is already stopped.",
                        timestamp=datetime.now().isoformat()
                    )
            
            # Execute stop action
            result = await self.repository.stop_service()
            
            # Apply business logic enhancements
            enhanced_result = self._enhance_action_result(result, "stop")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in stop_service controller: {e}")
            return ServiceActionResponse(
                success=False,
                action="stop",
                message=f"Stop service failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def restart_service(self) -> ServiceActionResponse:
        """Restart service with business logic validation"""
        try:
            logger.info("Restarting service")
            
            # Validate prerequisites
            validation = await self._validate_service_prerequisites()
            if not validation['valid']:
                return ServiceActionResponse(
                    success=False,
                    action="restart",
                    message=f"Service restart blocked: {validation['message']}",
                    timestamp=datetime.now().isoformat()
                )
            
            # Execute restart action
            result = await self.repository.restart_service()
            
            # Apply business logic enhancements
            enhanced_result = self._enhance_action_result(result, "restart")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in restart_service controller: {e}")
            return ServiceActionResponse(
                success=False,
                action="restart",
                message=f"Restart service failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def reset_service(self, confirm: bool = False) -> ServiceActionResponse:
        """Reset service with business logic validation"""
        try:
            logger.info(f"Resetting service (confirm={confirm})")
            
            if not confirm:
                return ServiceActionResponse(
                    success=False,
                    action="reset",
                    message="Reset operation requires explicit confirmation (destructive operation)",
                    timestamp=datetime.now().isoformat()
                )
            
            # Execute reset action
            result = await self.repository.reset_service(confirm=confirm)
            
            # Apply business logic enhancements
            enhanced_result = self._enhance_action_result(result, "reset")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in reset_service controller: {e}")
            return ServiceActionResponse(
                success=False,
                action="reset",
                message=f"Reset service failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    # Private helper methods for business logic
    
    async def _validate_service_prerequisites(self) -> Dict[str, Any]:
        """Validate prerequisites for service operations"""
        try:
            # Check if .env file exists
            env_file = self.repository.project_path / ".env"
            if not env_file.exists():
                return {
                    'valid': False,
                    'message': '.env file not found. Create configuration first.'
                }
            
            # Check if service script exists
            if not self.repository.service_script.exists():
                return {
                    'valid': False,
                    'message': 'Service script not found. Check installation.'
                }
            
            return {'valid': True, 'message': 'Prerequisites met'}
            
        except Exception as e:
            return {
                'valid': False,
                'message': f'Validation failed: {str(e)}'
            }
    
    def _enhance_service_status(self, status: ServiceStatusResponse) -> ServiceStatusResponse:
        """Apply business logic enhancements to service status"""
        # Add any business logic modifications here
        return status
    
    def _enhance_action_result(self, result: ServiceActionResponse, action: str) -> ServiceActionResponse:
        """Enhance action result with business logic"""
        # Add context-specific messaging
        if result.success:
            if action == "start":
                result.message = f"✅ Service started successfully. {result.message}"
            elif action == "stop":
                result.message = f"🛑 Service stopped successfully. {result.message}"
            elif action == "restart":
                result.message = f"🔄 Service restarted successfully. {result.message}"
            elif action == "reset":
                result.message = f"♻️ Service reset completed. {result.message}"
        
        return result