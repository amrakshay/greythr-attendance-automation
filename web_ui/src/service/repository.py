"""
Service repository for GreytHR service management
Data access layer for service control operations
"""

import logging
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os
import psutil

from ..database.connection import StateRepository
from .schemas import ServiceActionResponse, ServiceStatusResponse

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
            
            # Get state data
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
            
            # Get daemon and process info
            daemon_running = schedule_info.get('daemon_running', False)
            pid = script_info.get('pid')
            
            # Check if process is actually running
            is_running = False
            if pid:
                try:
                    process = psutil.Process(pid)
                    is_running = process.is_running()
                except psutil.NoSuchProcess:
                    is_running = False
            
            # Get uptime
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
        """Reset the GreytHR service"""
        if not confirm:
            return ServiceActionResponse(
                success=False,
                action="reset",
                message="Reset operation requires confirmation",
                timestamp=datetime.now().isoformat()
            )
        
        return await self._execute_service_action("reset")
    
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
            
            # Execute service script command
            cmd = [str(self.service_script), f"--{action}"]
            logger.info(f"Executing service action: {' '.join(cmd)}")
            
            # Execute with timeout
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
            logger.error(f"Error executing service action {action}: {e}")
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
            
            # Set up environment
            env = os.environ.copy()
            
            cmd = ["python3", str(self.greythr_script)]
            logger.info(f"Executing GreytHR script: {' '.join(cmd)}")
            
            # Execute with input simulation
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.project_path
            )
            
            # Send option as input
            input_data = f"{option}\n".encode()
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=input_data), 
                    timeout=120.0
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    'success': False,
                    'message': 'GreytHR script execution timed out'
                }
            
            success = process.returncode == 0
            stdout_text = stdout.decode().strip()
            stderr_text = stderr.decode().strip()
            
            message = stdout_text if success else stderr_text
            if not message:
                message = f"GreytHR script option {option} {'completed' if success else 'failed'}"
            
            return {
                'success': success,
                'message': message,
                'stdout': stdout_text,
                'stderr': stderr_text
            }
            
        except Exception as e:
            logger.error(f"Error executing GreytHR script: {e}")
            return {
                'success': False,
                'message': f'GreytHR script execution failed: {str(e)}'
            }
    
    def _format_uptime(self, uptime_seconds: int) -> str:
        """Format uptime seconds into human readable string"""
        if uptime_seconds <= 0:
            return "0s"
        
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")
        
        return " ".join(parts)
    
    def _parse_uptime_seconds(self, uptime_str: Optional[str]) -> int:
        """Parse uptime string back to seconds"""
        if not uptime_str:
            return 0
        
        try:
            total_seconds = 0
            parts = uptime_str.split()
            
            for part in parts:
                if part.endswith('d'):
                    total_seconds += int(part[:-1]) * 86400
                elif part.endswith('h'):
                    total_seconds += int(part[:-1]) * 3600
                elif part.endswith('m'):
                    total_seconds += int(part[:-1]) * 60
                elif part.endswith('s'):
                    total_seconds += int(part[:-1])
            
            return total_seconds
        except:
            return 0
    
    async def _check_config_validity(self) -> bool:
        """Check if configuration is valid"""
        try:
            # Check if .env file exists
            env_file = self.project_path / ".env"
            if not env_file.exists():
                return False
            
            # Check if required files exist
            if not self.greythr_script.exists():
                return False
            
            # TODO: Add more comprehensive config validation
            return True
            
        except Exception:
            return False