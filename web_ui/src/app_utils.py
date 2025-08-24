"""
Application utilities for GreytHR Web UI Dashboard
Configuration management and helper functions
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os
from functools import lru_cache

logger = logging.getLogger(__name__)

class ConfigManager:
    """Configuration manager following the established pattern"""
    
    def __init__(self, config_path: str = "conf"):
        self.config_path = Path(config_path)
        self._config_cache: Optional[Dict[str, Any]] = None
        
    def load_yaml_config(self, filename: str = "default_config.yaml") -> Dict[str, Any]:
        """Load YAML configuration file"""
        config_file = self.config_path / filename
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}")
            return {}
            
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            logger.info(f"Loaded YAML config from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load YAML config {config_file}: {e}")
            return {}
    
    def load_properties_config(self, filename: str = "default-config.properties") -> Dict[str, Any]:
        """Load properties configuration file"""
        config_file = self.config_path / filename
        
        if not config_file.exists():
            logger.warning(f"Properties file not found: {config_file}")
            return {}
            
        config = {}
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            # Convert nested keys (e.g., server.host -> {"server": {"host": value}})
                            keys = key.strip().split('.')
                            current = config
                            for k in keys[:-1]:
                                current = current.setdefault(k, {})
                            current[keys[-1]] = value.strip()
            
            logger.info(f"Loaded properties config from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load properties config {config_file}: {e}")
            return {}
    
    def load_config(self) -> Dict[str, Any]:
        """Load and merge all configuration files"""
        if self._config_cache is not None:
            return self._config_cache
            
        # Load YAML config first
        config = self.load_yaml_config()
        
        # Merge properties config
        properties_config = self.load_properties_config()
        config = self._deep_merge(config, properties_config)
        
        # Override with environment variables
        env_overrides = self._load_env_overrides()
        config = self._deep_merge(config, env_overrides)
        
        self._config_cache = config
        return config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _load_env_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables"""
        overrides = {}
        
        # Map environment variables to config structure
        env_mappings = {
            'WEBUI_HOST': ['server', 'host'],
            'WEBUI_PORT': ['server', 'port'],
            'GREYTHR_PROJECT_PATH': ['greythr', 'project_path'],
            'WEBUI_LOG_LEVEL': ['logging', 'level']
        }
        
        for env_var, keys in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                current = overrides
                for key in keys[:-1]:
                    current = current.setdefault(key, {})
                
                # Try to convert to appropriate type
                if keys[-1] == 'port':
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                elif value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                    
                current[keys[-1]] = value
        
        return overrides
    
    def reload_config(self):
        """Reload configuration from files"""
        self._config_cache = None
        return self.load_config()

class GreytHRIntegration:
    """Integration with existing GreytHR attendance automation system"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.state_dir = self.project_path / "state"
        self.activities_dir = self.project_path / "activities" 
        self.logs_dir = self.project_path / "logs"
        
    def is_project_accessible(self) -> bool:
        """Check if GreytHR project directory is accessible"""
        return (
            self.project_path.exists() and
            self.project_path.is_dir()
        )
    
    def get_state_file_path(self) -> Path:
        """Get path to current state file"""
        return self.state_dir / "current_state.json"
    
    def get_activities_dir(self) -> Path:
        """Get activities directory path"""
        return self.activities_dir
    
    def get_logs_dir(self) -> Path:
        """Get logs directory path"""
        return self.logs_dir
    
    def get_service_script_path(self) -> Path:
        """Get path to service management script"""
        return self.project_path / "greythr_service.sh"

@lru_cache()
def get_config_manager() -> ConfigManager:
    """Get singleton ConfigManager instance"""
    return ConfigManager()

@lru_cache()
def get_greythr_integration() -> GreytHRIntegration:
    """Get singleton GreytHRIntegration instance"""
    config = get_config_manager().load_config()
    project_path = config.get("greythr", {}).get("project_path", "../")
    return GreytHRIntegration(project_path)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_uptime(seconds: int) -> str:
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
