"""
Logging configuration for GreytHR Web UI Dashboard
Following the established logging patterns
"""

import logging
import logging.config
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logging(config_path: str = "conf", log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration for the web UI application
    """
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Generate today's date for log files
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Try to load logging configuration from file
    config_file = Path(config_path) / 'logging_config.yaml'
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update file paths with today's date
            if 'handlers' in config:
                for handler_name, handler_config in config['handlers'].items():
                    if 'filename' in handler_config:
                        filename = handler_config['filename'].format(date=today)
                        handler_config['filename'] = filename
            
            # Apply configuration
            logging.config.dictConfig(config)
            logger = logging.getLogger('webui')
            logger.info(f"Logging initialized from config file: {config_file}")
            
        except Exception as e:
            # Fallback to basic configuration
            logger = _setup_basic_logging(logs_dir, today, log_level)
            logger.error(f"Failed to load logging config from {config_file}: {e}")
            logger.info("Using fallback logging configuration")
    else:
        # Use basic configuration if config file doesn't exist
        logger = _setup_basic_logging(logs_dir, today, log_level)
        logger.info(f"Logging config file not found at {config_file}, using basic configuration")
    
    return logger

def _setup_basic_logging(logs_dir: Path, today: str, log_level: str) -> logging.Logger:
    """Setup basic logging configuration"""
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / f'webui_{today}.log'),
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    
    # Return main application logger
    logger = logging.getLogger('webui')
    logger.info(f"Basic logging initialized - writing to logs/webui_{today}.log")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(f'webui.{name}')

class RequestLoggingMiddleware:
    """Middleware for logging HTTP requests"""
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger('requests')
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            method = scope["method"]
            path = scope["path"]
            query_string = scope.get("query_string", b"").decode()
            client = scope.get("client", ["unknown", 0])
            
            # Log request
            self.logger.info(f"{method} {path}{'?' + query_string if query_string else ''} - Client: {client[0]}")
        
        await self.app(scope, receive, send)
