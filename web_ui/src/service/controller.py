"""
Service management controller
Business logic layer for service operations
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from .repository import ServiceRepository
from .schemas import (
    ServiceActionResponse, ServiceStatusResponse, ManualAttendanceResponse,
    CatchupResponse, ServiceInfo, ServiceHealthCheck, ServiceConfig
)

logger = logging.getLogger('webui.service.controller')

class ServiceController:
    """Controller for service management business logic"""
    
    def __init__(self, repository: ServiceRepository):
        self.repository = repository
        
    async def get_service_status(self) -> ServiceStatusResponse:
        """Get current service status with business logic validation"""
        try:
            status = await self.repository.get_service_status()
            
            # Add business logic enhancements
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
            logger.info("Service start requested")
            
            # Check if service is already running
            status = await self.repository.get_service_status()
            if status.is_running and not force:
                return ServiceActionResponse(
                    success=False,
                    action="start",
                    message="Service is already running. Use force=true to restart.",
                    timestamp=datetime.now().isoformat()
                )
            
            # Validate prerequisites
            validation_result = await self._validate_service_prerequisites()
            if not validation_result['valid']:
                return ServiceActionResponse(
                    success=False,
                    action="start",
                    message=f"Prerequisites not met: {validation_result['message']}",
                    timestamp=datetime.now().isoformat()
                )
            
            # Start the service
            result = await self.repository.start_service()
            
            # Enhance result with business logic
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
            logger.info("Service stop requested")
            
            # Check if service is running
            status = await self.repository.get_service_status()
            if not status.is_running and not force:
                return ServiceActionResponse(
                    success=True,  # Not an error - service is already stopped
                    action="stop",
                    message="Service is already stopped.",
                    timestamp=datetime.now().isoformat()
                )
            
            # Stop the service
            result = await self.repository.stop_service()
            
            # Enhance result with business logic
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
        """Restart service with proper sequencing"""
        try:
            logger.info("Service restart requested")
            
            # Get current status
            status = await self.repository.get_service_status()
            was_running = status.is_running
            
            if was_running:
                # Stop first
                stop_result = await self.repository.stop_service()
                if not stop_result.success:
                    return ServiceActionResponse(
                        success=False,
                        action="restart",
                        message=f"Failed to stop service: {stop_result.message}",
                        timestamp=datetime.now().isoformat()
                    )
                
                # Wait a moment for clean shutdown
                import asyncio
                await asyncio.sleep(2)
            
            # Start the service
            start_result = await self.repository.start_service()
            
            if start_result.success:
                message = "Service restarted successfully"
                if not was_running:
                    message = "Service was not running, started successfully"
            else:
                message = f"Failed to start service after stop: {start_result.message}"
            
            return ServiceActionResponse(
                success=start_result.success,
                action="restart",
                message=message,
                timestamp=datetime.now().isoformat(),
                duration_seconds=(start_result.duration_seconds or 0) + 2
            )
            
        except Exception as e:
            logger.error(f"Error in restart_service controller: {e}")
            return ServiceActionResponse(
                success=False,
                action="restart",
                message=f"Restart service failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def reset_service(self, confirm: bool = False) -> ServiceActionResponse:
        """Reset service with confirmation requirement"""
        try:
            logger.info(f"Service reset requested (confirm={confirm})")
            
            if not confirm:
                return ServiceActionResponse(
                    success=False,
                    action="reset",
                    message="Reset operation requires explicit confirmation. This will delete all logs, activities, and state data.",
                    timestamp=datetime.now().isoformat()
                )
            
            # Validate that this is safe to do
            status = await self.repository.get_service_status()
            if status.is_running:
                # Could warn user but allow reset
                logger.warning("Resetting service while it's running")
            
            # Execute reset
            result = await self.repository.reset_service(confirm=True)
            
            # Enhance result
            enhanced_result = self._enhance_action_result(result, "reset")
            if enhanced_result.success:
                enhanced_result.message = "Service reset completed. All data cleared and service restarted."
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in reset_service controller: {e}")
            return ServiceActionResponse(
                success=False,
                action="reset",
                message=f"Reset service failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def manual_signin(self, reason: Optional[str] = None) -> ManualAttendanceResponse:
        """Manual sign-in with business logic validation"""
        try:
            logger.info(f"Manual sign-in requested (reason: {reason})")
            
            # Check if already signed in today
            current_status = await self._check_today_attendance_status()
            if current_status.get('signin_completed'):
                return ManualAttendanceResponse(
                    success=False,
                    action="signin",
                    message="Sign-in already completed for today",
                    timestamp=datetime.now().isoformat(),
                    attendance_time=current_status.get('signin_time'),
                    attempts=0
                )
            
            # Validate prerequisites for manual attendance
            validation = await self._validate_attendance_prerequisites()
            if not validation['valid']:
                return ManualAttendanceResponse(
                    success=False,
                    action="signin",
                    message=f"Manual sign-in not possible: {validation['message']}",
                    timestamp=datetime.now().isoformat(),
                    attendance_time=None,
                    attempts=0
                )
            
            # Execute manual sign-in
            result = await self.repository.manual_signin(reason)
            
            # Enhance result with business logic
            enhanced_result = self._enhance_attendance_result(result, "signin")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in manual_signin controller: {e}")
            return ManualAttendanceResponse(
                success=False,
                action="signin",
                message=f"Manual sign-in failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                attendance_time=None,
                attempts=1
            )
    
    async def manual_signout(self, reason: Optional[str] = None) -> ManualAttendanceResponse:
        """Manual sign-out with business logic validation"""
        try:
            logger.info(f"Manual sign-out requested (reason: {reason})")
            
            # Check if already signed out today
            current_status = await self._check_today_attendance_status()
            if current_status.get('signout_completed'):
                return ManualAttendanceResponse(
                    success=False,
                    action="signout",
                    message="Sign-out already completed for today",
                    timestamp=datetime.now().isoformat(),
                    attendance_time=current_status.get('signout_time'),
                    attempts=0
                )
            
            # Check if signed in first
            if not current_status.get('signin_completed'):
                return ManualAttendanceResponse(
                    success=False,
                    action="signout",
                    message="Cannot sign out - no sign-in recorded for today",
                    timestamp=datetime.now().isoformat(),
                    attendance_time=None,
                    attempts=0
                )
            
            # Validate prerequisites
            validation = await self._validate_attendance_prerequisites()
            if not validation['valid']:
                return ManualAttendanceResponse(
                    success=False,
                    action="signout",
                    message=f"Manual sign-out not possible: {validation['message']}",
                    timestamp=datetime.now().isoformat(),
                    attendance_time=None,
                    attempts=0
                )
            
            # Execute manual sign-out
            result = await self.repository.manual_signout(reason)
            
            # Enhance result with business logic
            enhanced_result = self._enhance_attendance_result(result, "signout")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in manual_signout controller: {e}")
            return ManualAttendanceResponse(
                success=False,
                action="signout",
                message=f"Manual sign-out failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                attendance_time=None,
                attempts=1
            )
    
    async def force_catchup(self) -> CatchupResponse:
        """Force catchup with business logic"""
        try:
            logger.info("Force catchup requested")
            
            # Check if catchup is needed
            current_status = await self._check_today_attendance_status()
            catchup_info = self._analyze_catchup_needs(current_status)
            
            if not catchup_info['needed']:
                return CatchupResponse(
                    success=True,
                    actions_taken=["No catchup needed"],
                    message="All attendance actions are up to date",
                    timestamp=datetime.now().isoformat(),
                    signin_attempted=False,
                    signout_attempted=False
                )
            
            # Execute catchup
            result = await self.repository.force_catchup()
            
            # Enhance result with business logic
            enhanced_result = self._enhance_catchup_result(result, catchup_info)
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in force_catchup controller: {e}")
            return CatchupResponse(
                success=False,
                actions_taken=[],
                message=f"Force catchup failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                signin_attempted=False,
                signout_attempted=False
            )
    
    async def get_service_info(self) -> ServiceInfo:
        """Get detailed service information"""
        try:
            info = await self.repository.get_service_info()
            
            # Enhance with business logic
            enhanced_info = self._enhance_service_info(info)
            return enhanced_info
            
        except Exception as e:
            logger.error(f"Error in get_service_info controller: {e}")
            return ServiceInfo(
                service_name="GreytHR Attendance Automation",
                is_installed=False,
                is_running=False,
                pid=None,
                status=f"Controller error: {str(e)}",
                config_valid=False,
                script_path="",
                project_path="",
                uptime_seconds=0,
                last_restart=None
            )
    
    async def health_check(self) -> ServiceHealthCheck:
        """Comprehensive health check with business logic"""
        try:
            health = await self.repository.health_check()
            
            # Enhance with business logic analysis
            enhanced_health = self._enhance_health_check(health)
            return enhanced_health
            
        except Exception as e:
            logger.error(f"Error in health_check controller: {e}")
            return ServiceHealthCheck(
                overall_health="error",
                checks={"controller_error": False},
                issues=[f"Health check controller failed: {str(e)}"],
                recommendations=["Check system logs and controller implementation"],
                last_check=datetime.now().isoformat(),
                check_duration_ms=0
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
    
    async def _validate_attendance_prerequisites(self) -> Dict[str, Any]:
        """Validate prerequisites for attendance operations"""
        try:
            # Check if GreytHR script exists
            if not self.repository.greythr_script.exists():
                return {
                    'valid': False,
                    'message': 'GreytHR script not found'
                }
            
            # Check if configuration is valid
            config_valid = await self.repository._check_config_validity()
            if not config_valid:
                return {
                    'valid': False,
                    'message': 'Configuration is invalid. Check credentials.'
                }
            
            return {'valid': True, 'message': 'Prerequisites met'}
            
        except Exception as e:
            return {
                'valid': False,
                'message': f'Validation failed: {str(e)}'
            }
    
    async def _check_today_attendance_status(self) -> Dict[str, Any]:
        """Check today's attendance status"""
        try:
            state_data = await self.repository.state_repo.get_current_state()
            if not state_data:
                return {
                    'signin_completed': False,
                    'signout_completed': False,
                    'signin_time': None,
                    'signout_time': None
                }
            
            today_summary = state_data.get('today_summary', {})
            return {
                'signin_completed': today_summary.get('signin_status', '').startswith('✅'),
                'signout_completed': today_summary.get('signout_status', '').startswith('✅'),
                'signin_time': today_summary.get('signin_time'),
                'signout_time': today_summary.get('signout_time')
            }
            
        except Exception:
            return {
                'signin_completed': False,
                'signout_completed': False,
                'signin_time': None,
                'signout_time': None
            }
    
    def _analyze_catchup_needs(self, current_status: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if catchup is needed"""
        now = datetime.now()
        
        # Simple logic: if it's past normal work hours and not completed
        is_past_signin_time = now.hour >= 9  # Assuming 9 AM sign-in
        is_past_signout_time = now.hour >= 19  # Assuming 7 PM sign-out
        
        needs_signin = is_past_signin_time and not current_status['signin_completed']
        needs_signout = is_past_signout_time and not current_status['signout_completed']
        
        return {
            'needed': needs_signin or needs_signout,
            'needs_signin': needs_signin,
            'needs_signout': needs_signout,
            'reason': 'Past scheduled time and not completed'
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
    
    def _enhance_attendance_result(self, result: ManualAttendanceResponse, action: str) -> ManualAttendanceResponse:
        """Enhance attendance result with business logic"""
        if result.success:
            if action == "signin":
                result.message = f"✅ Manual sign-in completed successfully"
            elif action == "signout":
                result.message = f"✅ Manual sign-out completed successfully"
        
        return result
    
    def _enhance_catchup_result(self, result: CatchupResponse, catchup_info: Dict[str, Any]) -> CatchupResponse:
        """Enhance catchup result with business logic"""
        if result.success and catchup_info['needed']:
            actions = []
            if catchup_info['needs_signin']:
                actions.append("Attempted overdue sign-in")
            if catchup_info['needs_signout']:
                actions.append("Attempted overdue sign-out")
            
            if actions:
                result.actions_taken.extend(actions)
                result.message = f"Catchup completed: {', '.join(actions)}"
        
        return result
    
    def _enhance_service_info(self, info: ServiceInfo) -> ServiceInfo:
        """Enhance service info with business logic"""
        # Add any business logic enhancements
        return info
    
    def _enhance_health_check(self, health: ServiceHealthCheck) -> ServiceHealthCheck:
        """Enhance health check with business logic analysis"""
        # Add business logic for better health analysis
        critical_checks = ['service_script_exists', 'greythr_script_exists']
        
        critical_failed = any(
            check in critical_checks and not health.checks.get(check, False)
            for check in health.checks
        )
        
        if critical_failed and health.overall_health != "critical":
            health.overall_health = "critical"
            if "System is in critical state" not in health.issues:
                health.issues.insert(0, "System is in critical state")
        
        return health
