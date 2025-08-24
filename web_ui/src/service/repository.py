"""
Service management repository
Data access layer for service control operations
"""

import logging
import subprocess
import asyncio
import signal
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import json
import os
import psutil

from ..database.connection import StateRepository
from .schemas import (
    ServiceActionResponse, ServiceStatusResponse, ManualAttendanceResponse,
    CatchupResponse, ServiceInfo, ServiceConfig, ServiceHealthCheck
)

logger = logging.getLogger('webui.service.repository')

class ServiceRepository:
    """Repository for service management operations"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()
        self.service_script = self.project_path / "greythr_service.sh"
        self.greythr_script = self.project_path / "greythr_api.py"
        self.state_repo = StateRepository(self.project_path)
        
    async def get_service_status(self) -> ServiceStatusResponse:
        """Get current service status"""
        try:
            # Check if service script exists
            if not self.service_script.exists():
                return ServiceStatusResponse(
                    is_running=False,
                    pid=None,
                    status="Service script not found",
                    uptime=None,
                    last_activity=None,
                    next_scheduled_action=None,
                    daemon_running=False
                )
            
            # Get status from state file
            state_data = await self.state_repo.get_current_state()
            if not state_data:
                return ServiceStatusResponse(
                    is_running=False,
                    pid=None,
                    status="No state data available",
                    uptime=None,
                    last_activity=None,
                    next_scheduled_action=None,
                    daemon_running=False
                )
            
            script_info = state_data.get('script', {})
            schedule_info = state_data.get('schedule', {})
            statistics = state_data.get('statistics', {})
            
            # Check if daemon is running
            daemon_running = schedule_info.get('daemon_running', False)
            pid = script_info.get('pid')
            
            # Verify PID is actually running
            is_running = False
            if pid and daemon_running:
                try:
                    # Check if process exists
                    process = psutil.Process(pid)
                    is_running = process.is_running()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    is_running = False
            
            # Format uptime
            uptime_seconds = statistics.get('uptime_seconds', 0)
            uptime = self._format_uptime(uptime_seconds)
            
            # Get last activity
            last_activity = state_data.get('last_updated')
            
            # Get next scheduled action
            next_signin = schedule_info.get('next_signin')
            next_signout = schedule_info.get('next_signout')
            next_scheduled_action = next_signin or next_signout
            
            status_text = script_info.get('status', 'unknown')
            if is_running:
                status_text = f"Running ({status_text})"
            else:
                status_text = f"Stopped ({status_text})"
            
            return ServiceStatusResponse(
                is_running=is_running,
                pid=pid,
                status=status_text,
                uptime=uptime,
                last_activity=last_activity,
                next_scheduled_action=next_scheduled_action,
                daemon_running=daemon_running
            )
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return ServiceStatusResponse(
                is_running=False,
                pid=None,
                status=f"Error: {str(e)}",
                uptime=None,
                last_activity=None,
                next_scheduled_action=None,
                daemon_running=False
            )
    
    async def start_service(self) -> ServiceActionResponse:
        """Start the GreytHR service"""
        return await self._execute_service_action("start")
    
    async def stop_service(self) -> ServiceActionResponse:
        """Stop the GreytHR service"""
        return await self._execute_service_action("stop")
    
    async def restart_service(self) -> ServiceActionResponse:
        """Restart the GreytHR service"""
        return await self._execute_service_action("restart")
    
    async def reset_service(self, confirm: bool = False) -> ServiceActionResponse:
        """Reset the GreytHR service (destructive operation)"""
        if not confirm:
            return ServiceActionResponse(
                success=False,
                action="reset",
                message="Reset operation requires confirmation",
                timestamp=datetime.now().isoformat()
            )
        
        return await self._execute_service_action("reset")
    
    async def manual_signin(self, reason: Optional[str] = None) -> ManualAttendanceResponse:
        """Perform manual sign-in"""
        try:
            start_time = datetime.now()
            logger.info(f"Starting manual sign-in (reason: {reason})")
            
            # Execute manual sign-in using greythr_api.py
            result = await self._execute_greythr_script("1")  # Option 1 is manual sign-in
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return ManualAttendanceResponse(
                success=result.get('success', False),
                action="signin",
                message=result.get('message', 'Manual sign-in completed'),
                timestamp=datetime.now().isoformat(),
                attendance_time=result.get('attendance_time'),
                attempts=1
            )
            
        except Exception as e:
            logger.error(f"Manual sign-in failed: {e}")
            return ManualAttendanceResponse(
                success=False,
                action="signin",
                message=f"Manual sign-in failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                attendance_time=None,
                attempts=1
            )
    
    async def manual_signout(self, reason: Optional[str] = None) -> ManualAttendanceResponse:
        """Perform manual sign-out"""
        try:
            start_time = datetime.now()
            logger.info(f"Starting manual sign-out (reason: {reason})")
            
            # Execute manual sign-out using greythr_api.py
            result = await self._execute_greythr_script("2")  # Option 2 is manual sign-out
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return ManualAttendanceResponse(
                success=result.get('success', False),
                action="signout",
                message=result.get('message', 'Manual sign-out completed'),
                timestamp=datetime.now().isoformat(),
                attendance_time=result.get('attendance_time'),
                attempts=1
            )
            
        except Exception as e:
            logger.error(f"Manual sign-out failed: {e}")
            return ManualAttendanceResponse(
                success=False,
                action="signout",
                message=f"Manual sign-out failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                attendance_time=None,
                attempts=1
            )
    
    async def force_catchup(self) -> CatchupResponse:
        """Force catchup check"""
        try:
            start_time = datetime.now()
            logger.info("Starting force catchup check")
            
            # Execute catchup using greythr_api.py
            result = await self._execute_greythr_script("7")  # Option 7 is force catchup
            
            actions_taken = []
            signin_attempted = False
            signout_attempted = False
            
            if result.get('success'):
                actions_taken.append("Catchup check completed")
                # Parse result for specific actions
                message = result.get('message', '')
                if 'sign-in' in message.lower():
                    signin_attempted = True
                    actions_taken.append("Sign-in attempted")
                if 'sign-out' in message.lower():
                    signout_attempted = True
                    actions_taken.append("Sign-out attempted")
            
            return CatchupResponse(
                success=result.get('success', False),
                actions_taken=actions_taken,
                message=result.get('message', 'Catchup check completed'),
                timestamp=datetime.now().isoformat(),
                signin_attempted=signin_attempted,
                signout_attempted=signout_attempted
            )
            
        except Exception as e:
            logger.error(f"Force catchup failed: {e}")
            return CatchupResponse(
                success=False,
                actions_taken=[],
                message=f"Catchup failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                signin_attempted=False,
                signout_attempted=False
            )
    
    async def get_service_info(self) -> ServiceInfo:
        """Get detailed service information"""
        try:
            status = await self.get_service_status()
            
            # Check if service is installed
            is_installed = self.service_script.exists()
            
            # Check configuration validity
            config_valid = await self._check_config_validity()
            
            return ServiceInfo(
                service_name="GreytHR Attendance Automation",
                is_installed=is_installed,
                is_running=status.is_running,
                pid=status.pid,
                status=status.status,
                config_valid=config_valid,
                script_path=str(self.service_script),
                project_path=str(self.project_path),
                uptime_seconds=self._parse_uptime_seconds(status.uptime),
                last_restart=status.last_activity
            )
            
        except Exception as e:
            logger.error(f"Error getting service info: {e}")
            return ServiceInfo(
                service_name="GreytHR Attendance Automation",
                is_installed=False,
                is_running=False,
                pid=None,
                status=f"Error: {str(e)}",
                config_valid=False,
                script_path=str(self.service_script),
                project_path=str(self.project_path),
                uptime_seconds=0,
                last_restart=None
            )
    
    async def health_check(self) -> ServiceHealthCheck:
        """Perform comprehensive service health check"""
        try:
            start_time = datetime.now()
            checks = {}
            issues = []
            recommendations = []
            
            # Check service script exists
            checks['service_script_exists'] = self.service_script.exists()
            if not checks['service_script_exists']:
                issues.append("Service script not found")
                recommendations.append("Reinstall GreytHR service")
            
            # Check GreytHR script exists
            checks['greythr_script_exists'] = self.greythr_script.exists()
            if not checks['greythr_script_exists']:
                issues.append("GreytHR API script not found")
                recommendations.append("Check GreytHR installation")
            
            # Check configuration
            checks['config_valid'] = await self._check_config_validity()
            if not checks['config_valid']:
                issues.append("Configuration is invalid")
                recommendations.append("Check .env file and configuration")
            
            # Check service status
            status = await self.get_service_status()
            checks['service_running'] = status.is_running
            if not checks['service_running']:
                issues.append("Service is not running")
                recommendations.append("Start the service")
            
            # Check state file accessibility
            state_data = await self.state_repo.get_current_state()
            checks['state_accessible'] = state_data is not None
            if not checks['state_accessible']:
                issues.append("Cannot access service state")
                recommendations.append("Check file permissions and service status")
            
            # Determine overall health
            overall_health = "healthy"
            if any(issue in ['service_script_exists', 'greythr_script_exists'] 
                   for issue in checks if not checks[issue]):
                overall_health = "critical"
            elif not checks.get('service_running', False):
                overall_health = "degraded"
            elif issues:
                overall_health = "warning"
            
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return ServiceHealthCheck(
                overall_health=overall_health,
                checks=checks,
                issues=issues,
                recommendations=recommendations,
                last_check=end_time.isoformat(),
                check_duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return ServiceHealthCheck(
                overall_health="error",
                checks={"health_check_error": False},
                issues=[f"Health check failed: {str(e)}"],
                recommendations=["Check system logs and permissions"],
                last_check=datetime.now().isoformat(),
                check_duration_ms=0
            )
    
    # Private helper methods
    
    async def _execute_service_action(self, action: str) -> ServiceActionResponse:
        """Execute a service action using the service script"""
        try:
            start_time = datetime.now()
            
            if not self.service_script.exists():
                return ServiceActionResponse(
                    success=False,
                    action=action,
                    message="Service script not found",
                    timestamp=datetime.now().isoformat()
                )
            
            # Execute service script with action
            cmd = [str(self.service_script), f"--{action}"]
            logger.info(f"Executing service action: {' '.join(cmd)}")
            
            # Run with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_path
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
            except asyncio.TimeoutError:
                process.kill()
                return ServiceActionResponse(
                    success=False,
                    action=action,
                    message=f"Service {action} timed out",
                    timestamp=datetime.now().isoformat()
                )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            success = process.returncode == 0
            stdout_text = stdout.decode().strip()
            stderr_text = stderr.decode().strip()
            
            message = stdout_text if success else stderr_text
            if not message:
                message = f"Service {action} {'completed' if success else 'failed'}"
            
            return ServiceActionResponse(
                success=success,
                action=action,
                message=message,
                details=stderr_text if success and stderr_text else None,
                timestamp=datetime.now().isoformat(),
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Service action {action} failed: {e}")
            return ServiceActionResponse(
                success=False,
                action=action,
                message=f"Service {action} failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    async def _execute_greythr_script(self, option: str) -> Dict[str, Any]:
        """Execute GreytHR script with given option"""
        try:
            if not self.greythr_script.exists():
                return {
                    'success': False,
                    'message': 'GreytHR script not found'
                }
            
            # Use expect or similar to automate the interactive script
            # For now, we'll use a simpler approach with environment variables
            env = os.environ.copy()
            
            cmd = ["python3", str(self.greythr_script)]
            logger.info(f"Executing GreytHR script with option {option}")
            
            # Create process with input
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_path,
                env=env
            )
            
            # Send option to script
            input_data = f"{option}\n".encode()
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=input_data), 
                    timeout=120.0  # 2 minutes timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'success': False,
                    'message': 'Operation timed out'
                }
            
            success = process.returncode == 0
            stdout_text = stdout.decode().strip()
            stderr_text = stderr.decode().strip()
            
            # Parse output to determine if attendance was successful
            output = stdout_text + stderr_text
            attendance_success = any(phrase in output.lower() for phrase in [
                'successful', 'completed', '✅', 'sign in completed', 'sign out completed'
            ])
            
            return {
                'success': success and attendance_success,
                'message': stdout_text if stdout_text else stderr_text,
                'attendance_time': datetime.now().isoformat() if attendance_success else None
            }
            
        except Exception as e:
            logger.error(f"GreytHR script execution failed: {e}")
            return {
                'success': False,
                'message': f"Script execution failed: {str(e)}"
            }
    
    async def _check_config_validity(self) -> bool:
        """Check if configuration is valid"""
        try:
            env_file = self.project_path / ".env"
            if not env_file.exists():
                return False
            
            # Basic check for required environment variables
            required_vars = ['GREYTHR_URL', 'GREYTHR_USERNAME', 'GREYTHR_PASSWORD']
            
            with open(env_file, 'r') as f:
                content = f.read()
                for var in required_vars:
                    if f"{var}=" not in content:
                        return False
            
            return True
            
        except Exception:
            return False
    
    def _format_uptime(self, seconds: int) -> str:
        """Format uptime in human readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m {seconds % 60}s"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}d {hours}h"
    
    def _parse_uptime_seconds(self, uptime_str: Optional[str]) -> int:
        """Parse uptime string to seconds"""
        if not uptime_str:
            return 0
        
        try:
            # Simple parsing for common formats
            if 'h' in uptime_str and 'm' in uptime_str:
                parts = uptime_str.replace('h', ' ').replace('m', ' ').split()
                hours = int(parts[0]) if len(parts) > 0 else 0
                minutes = int(parts[1]) if len(parts) > 1 else 0
                return hours * 3600 + minutes * 60
            elif 'm' in uptime_str:
                minutes = int(uptime_str.replace('m', '').split()[0])
                return minutes * 60
            elif 's' in uptime_str:
                seconds = int(uptime_str.replace('s', '').split()[0])
                return seconds
            else:
                return 0
        except:
            return 0
