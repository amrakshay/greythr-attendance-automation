#!/usr/bin/env python3
"""
GreytHR Attendance Automation - API Version
Login with Selenium -> Use API calls for attendance marking
"""

import time
import requests
import json
import os
import logging
import logging.config
import schedule
import threading
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import pytz
from pathlib import Path
import random
import yaml
import platform
import psutil
import signal
import sys
import atexit
import argparse

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    # Note: logger not available yet at import time, will be handled in main()

# Setup logging from configuration file
def setup_logging():
    """Setup logging configuration from YAML file"""
    # Create logs directory
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    # Generate today's date for log files
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Load logging configuration
    config_file = Path('logging_config.yaml')
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
            
        except Exception as e:
            # Fallback to basic configuration
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(f'logs/greythr_attendance_{today}.log'),
                    logging.StreamHandler()
                ]
            )
            logging.error(f"Failed to load logging config: {e}")
    else:
        # Fallback configuration if config file doesn't exist
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/greythr_attendance_{today}.log'),
                logging.StreamHandler()
            ]
        )
        logging.warning("Logging config file not found, using basic configuration")
    
    # Return main application logger
    app_logger = logging.getLogger('greythr_automation')
    app_logger.info(f"Logging initialized - writing to logs/greythr_attendance_{today}.log")
    
    return app_logger

logger = setup_logging()

class AttendanceStateManager:
    """Manages daily attendance state using JSON files"""
    
    def __init__(self):
        self.activities_dir = Path('activities')
        self.activities_dir.mkdir(exist_ok=True)
        self.tz = pytz.timezone('Asia/Kolkata')
    
    def get_today_file_path(self):
        """Get today's state file path"""
        today = datetime.now(self.tz).strftime('%Y-%m-%d')
        return self.activities_dir / f'attendance_{today}.json'
    
    def load_today_state(self):
        """Load today's attendance state"""
        file_path = self.get_today_file_path()
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading state file: {e}")
                return self.get_default_state()
        return self.get_default_state()
    
    def get_default_state(self):
        """Get default attendance state"""
        today = datetime.now(self.tz)
        return {
            'date': today.strftime('%Y-%m-%d'),
            'signin_completed': False,
            'signout_completed': False,
            'signin_time': None,
            'signout_time': None,
            'signin_attempts': 0,
            'signout_attempts': 0,
            'signin_failed_attempts': 0,
            'signout_failed_attempts': 0,
            'signin_next_retry': None,
            'signout_next_retry': None,
            'signin_last_error': None,
            'signout_last_error': None,
            'last_updated': today.isoformat()
        }
    
    def save_today_state(self, state):
        """Save today's attendance state"""
        state['last_updated'] = datetime.now(self.tz).isoformat()
        file_path = self.get_today_file_path()
        
        try:
            with open(file_path, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug(f"State saved to {file_path}")
        except IOError as e:
            logger.error(f"Error saving state file: {e}")
    
    def mark_signin_completed(self):
        """Mark sign-in as completed for today"""
        state = self.load_today_state()
        state['signin_completed'] = True
        state['signin_time'] = datetime.now(self.tz).isoformat()
        state['signin_attempts'] += 1
        self.save_today_state(state)
        logger.info("✅ Sign-in state updated")
    
    def mark_signout_completed(self):
        """Mark sign-out as completed for today"""
        state = self.load_today_state()
        state['signout_completed'] = True
        state['signout_time'] = datetime.now(self.tz).isoformat()
        state['signout_attempts'] += 1
        self.save_today_state(state)
        logger.info("✅ Sign-out state updated")
    
    def is_signin_completed(self):
        """Check if sign-in is completed for today"""
        state = self.load_today_state()
        return state.get('signin_completed', False)
    
    def is_signout_completed(self):
        """Check if sign-out is completed for today"""
        state = self.load_today_state()
        return state.get('signout_completed', False)
    
    def should_signin_now(self, signin_time_str, signout_time_str):
        """Check if we should do sign-in now (catch-up logic)"""
        now = datetime.now(self.tz)
        
        signin_time = datetime.strptime(signin_time_str, '%H:%M').time()
        signin_datetime = datetime.combine(now.date(), signin_time)
        signin_datetime = self.tz.localize(signin_datetime)
        
        signout_time = datetime.strptime(signout_time_str, '%H:%M').time()
        signout_datetime = datetime.combine(now.date(), signout_time)
        signout_datetime = self.tz.localize(signout_datetime)
        
        current_time_str = now.strftime('%H:%M')
        
        # Already completed
        if self.is_signin_completed():
            logger.debug(f"Sign-in already completed today")
            return False
            
        # Don't sign in if we're past sign-out time (missed window)
        if now >= signout_datetime:
            logger.info(f"⏰ MISSED WINDOW: Current time {current_time_str} is past sign-out time {signout_time_str}")
            return False
            
        # Check if we're past sign-in time
        if now >= signin_datetime:
            logger.info(f"⏰ CATCH-UP NEEDED: Current time {current_time_str} is past sign-in time {signin_time_str}")
            return True
        
        logger.debug(f"No sign-in needed: Current time {current_time_str} is before sign-in time {signin_time_str}")
        return False
    
    def should_signout_now(self, signout_time_str):
        """Check if we should do sign-out now (catch-up logic)"""
        now = datetime.now(self.tz)
        signout_time = datetime.strptime(signout_time_str, '%H:%M').time()
        signout_datetime = datetime.combine(now.date(), signout_time)
        signout_datetime = self.tz.localize(signout_datetime)
        
        current_time_str = now.strftime('%H:%M')
        
        # Already completed
        if self.is_signout_completed():
            logger.debug(f"Sign-out already completed today")
            return False
            
        # Must have signed in first
        if not self.is_signin_completed():
            logger.debug(f"Cannot sign out - no sign-in recorded for today")
            return False
        
        # Check if we're past sign-out time
        if now >= signout_datetime:
            logger.info(f"⏰ CATCH-UP NEEDED: Current time {current_time_str} is past sign-out time {signout_time_str}")
            return True
            
        logger.debug(f"No sign-out needed: Current time {current_time_str} is before sign-out time {signout_time_str}")
        return False
    
    def mark_signin_failed(self, error_msg):
        """Mark sign-in attempt as failed and schedule retry"""
        state = self.load_today_state()
        state['signin_failed_attempts'] = state.get('signin_failed_attempts', 0) + 1
        state['signin_attempts'] = state.get('signin_attempts', 0) + 1
        state['signin_last_error'] = error_msg
        
        # Calculate next retry time with exponential backoff
        max_retries = int(os.getenv('MAX_RETRY_ATTEMPTS', '5'))
        base_delay = int(os.getenv('BASE_RETRY_DELAY', '300'))  # 5 minutes
        
        if state['signin_failed_attempts'] <= max_retries:
            # Exponential backoff: 5min, 15min, 45min, 135min, 405min
            delay_seconds = base_delay * (3 ** (state['signin_failed_attempts'] - 1))
            # Add jitter to avoid thundering herd
            jitter = random.randint(0, 60)
            next_retry = datetime.now(self.tz) + timedelta(seconds=delay_seconds + jitter)
            state['signin_next_retry'] = next_retry.isoformat()
            logger.info(f"🔄 Sign-in retry #{state['signin_failed_attempts']} scheduled for {next_retry.strftime('%H:%M:%S')}")
        else:
            state['signin_next_retry'] = None
            logger.error(f"❌ Sign-in max retries ({max_retries}) exceeded. Giving up for today.")
        
        self.save_today_state(state)
    
    def mark_signout_failed(self, error_msg):
        """Mark sign-out attempt as failed and schedule retry"""
        state = self.load_today_state()
        state['signout_failed_attempts'] = state.get('signout_failed_attempts', 0) + 1
        state['signout_attempts'] = state.get('signout_attempts', 0) + 1
        state['signout_last_error'] = error_msg
        
        # Calculate next retry time with exponential backoff
        max_retries = int(os.getenv('MAX_RETRY_ATTEMPTS', '5'))
        base_delay = int(os.getenv('BASE_RETRY_DELAY', '300'))  # 5 minutes
        
        if state['signout_failed_attempts'] <= max_retries:
            # Exponential backoff: 5min, 15min, 45min, 135min, 405min
            delay_seconds = base_delay * (3 ** (state['signout_failed_attempts'] - 1))
            # Add jitter to avoid thundering herd
            jitter = random.randint(0, 60)
            next_retry = datetime.now(self.tz) + timedelta(seconds=delay_seconds + jitter)
            state['signout_next_retry'] = next_retry.isoformat()
            logger.info(f"🔄 Sign-out retry #{state['signout_failed_attempts']} scheduled for {next_retry.strftime('%H:%M:%S')}")
        else:
            state['signout_next_retry'] = None
            logger.error(f"❌ Sign-out max retries ({max_retries}) exceeded. Giving up for today.")
        
        self.save_today_state(state)
    
    def should_retry_signin_now(self):
        """Check if it's time to retry a failed sign-in"""
        state = self.load_today_state()
        next_retry_str = state.get('signin_next_retry')
        
        if not next_retry_str or state.get('signin_completed'):
            return False
            
        next_retry = datetime.fromisoformat(next_retry_str)
        now = datetime.now(self.tz)
        
        if now >= next_retry:
            logger.info(f"⏰ Sign-in retry time reached (attempt #{state.get('signin_failed_attempts', 0) + 1})")
            return True
        
        return False
    
    def should_retry_signout_now(self):
        """Check if it's time to retry a failed sign-out"""
        state = self.load_today_state()
        next_retry_str = state.get('signout_next_retry')
        
        if not next_retry_str or state.get('signout_completed'):
            return False
            
        next_retry = datetime.fromisoformat(next_retry_str)
        now = datetime.now(self.tz)
        
        if now >= next_retry:
            logger.info(f"⏰ Sign-out retry time reached (attempt #{state.get('signout_failed_attempts', 0) + 1})")
            return True
        
        return False
    
    def clear_retry_schedule(self, action):
        """Clear retry schedule for successful action"""
        state = self.load_today_state()
        if action == 'signin':
            state['signin_next_retry'] = None
            state['signin_last_error'] = None
        elif action == 'signout':
            state['signout_next_retry'] = None
            state['signout_last_error'] = None
        self.save_today_state(state)
    
    def get_status_summary(self):
        """Get today's status summary"""
        state = self.load_today_state()
        
        # Check for pending retries
        signin_status = '✅ Completed' if state.get('signin_completed') else '❌ Pending'
        signout_status = '✅ Completed' if state.get('signout_completed') else '❌ Pending'
        
        if state.get('signin_next_retry') and not state.get('signin_completed'):
            retry_time = datetime.fromisoformat(state['signin_next_retry'])
            signin_status = f"🔄 Retry at {retry_time.strftime('%H:%M')}"
        
        if state.get('signout_next_retry') and not state.get('signout_completed'):
            retry_time = datetime.fromisoformat(state['signout_next_retry'])
            signout_status = f"🔄 Retry at {retry_time.strftime('%H:%M')}"
        
        return {
            'date': state.get('date'),
            'signin_status': signin_status,
            'signout_status': signout_status,
            'signin_time': state.get('signin_time'),
            'signout_time': state.get('signout_time'),
            'signin_attempts': state.get('signin_attempts', 0),
            'signout_attempts': state.get('signout_attempts', 0),
            'signin_failed_attempts': state.get('signin_failed_attempts', 0),
            'signout_failed_attempts': state.get('signout_failed_attempts', 0),
            'signin_last_error': state.get('signin_last_error'),
            'signout_last_error': state.get('signout_last_error'),
            'signin_next_retry': state.get('signin_next_retry'),
            'signout_next_retry': state.get('signout_next_retry')
        }


class SingleInstanceManager:
    """Ensures only one instance of the script runs at a time using PID file locking"""
    
    def __init__(self, lock_file_path="greythr_attendance.lock"):
        self.lock_file = Path(lock_file_path)
        self.pid = os.getpid()
        self.logger = logging.getLogger('greythr_automation.single_instance')
        
    def is_another_instance_running(self):
        """Check if another instance is already running"""
        if not self.lock_file.exists():
            return False
        
        try:
            with open(self.lock_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if the process with this PID is still running
            try:
                # Send signal 0 to check if process exists (doesn't actually send a signal)
                os.kill(old_pid, 0)
                self.logger.warning(f"Another instance is running with PID {old_pid}")
                return True
            except OSError:
                # Process doesn't exist, remove stale lock file
                self.logger.info(f"Removing stale lock file (PID {old_pid} not found)")
                self.lock_file.unlink()
                return False
                
        except (ValueError, FileNotFoundError):
            # Invalid lock file, remove it
            if self.lock_file.exists():
                self.lock_file.unlink()
            return False
    
    def acquire_lock(self):
        """Acquire the instance lock"""
        if self.is_another_instance_running():
            self.logger.error("❌ Another instance is already running!")
            self.logger.error("❌ Only one instance of GreytHR Attendance Automation is allowed")
            self.logger.info("💡 If you're sure no other instance is running, delete the lock file:")
            self.logger.info(f"   rm {self.lock_file}")
            return False
        
        try:
            # Create lock file with current PID
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
            
            # Register cleanup function to remove lock file on exit
            atexit.register(self.release_lock)
            
            # Handle signals to cleanup lock file
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.logger.debug(f"✅ Instance lock acquired (PID: {self.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to acquire instance lock: {e}")
            return False
    
    def release_lock(self):
        """Release the instance lock"""
        try:
            if self.lock_file.exists():
                with open(self.lock_file, 'r') as f:
                    lock_pid = int(f.read().strip())
                
                # Only remove the lock if it's our PID
                if lock_pid == self.pid:
                    self.lock_file.unlink()
                    self.logger.debug(f"✅ Instance lock released (PID: {self.pid})")
                    
        except Exception as e:
            self.logger.error(f"❌ Error releasing instance lock: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self.logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.release_lock()
        sys.exit(0)


class StateTracker:
    """Tracks current script state for dashboard and monitoring"""
    
    def __init__(self):
        self.state_dir = Path('state')
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / 'current_state.json'
        self.script_start_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        self.logger = logging.getLogger('greythr_automation.state_tracker')
        
        # Initialize state
        self._initialize_state()
    
    def _initialize_state(self):
        """Initialize the state file with basic information"""
        try:
            initial_state = {
                'script': {
                    'status': 'starting',
                    'start_time': self.script_start_time.isoformat(),
                    'pid': os.getpid(),
                    'python_version': platform.python_version(),
                    'platform': platform.system(),
                    'hostname': platform.node(),
                    'working_directory': str(Path.cwd()),
                },
                'current_operation': {
                    'action': 'initializing',
                    'details': 'Script is starting up',
                    'start_time': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                    'progress': 0
                },
                'configuration': {
                    'signin_time': os.getenv('SIGNIN_TIME', '09:00'),
                    'signout_time': os.getenv('SIGNOUT_TIME', '19:00'),
                    'test_mode': os.getenv('TEST_MODE', 'false').lower() == 'true',
                    'timezone': 'Asia/Kolkata',
                    'max_retry_attempts': int(os.getenv('MAX_RETRY_ATTEMPTS', '5')),
                    'base_retry_delay_minutes': int(os.getenv('BASE_RETRY_DELAY', '300')) // 60
                },
                'schedule': {
                    'next_signin': None,
                    'next_signout': None,
                    'daemon_running': False,
                    'scheduler_active': False
                },
                'today_summary': {},
                'statistics': {
                    'total_operations': 0,
                    'successful_operations': 0,
                    'failed_operations': 0,
                    'signin_attempts': 0,
                    'signout_attempts': 0,
                    'last_successful_signin': None,
                    'last_successful_signout': None,
                    'uptime_seconds': 0
                },
                'system': {
                    'memory_usage_mb': 0,
                    'cpu_percent': 0,
                    'disk_usage_percent': 0
                },
                'errors': {
                    'last_error': None,
                    'last_error_time': None,
                    'retry_info': {}
                },
                'last_updated': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            }
            
            self._save_state(initial_state)
            self.logger.debug(f"State tracker initialized - state file: {self.state_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize state tracker: {e}")
    
    def _save_state(self, state):
        """Save state to JSON file"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def _load_state(self):
        """Load current state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
            return {}
    
    def _update_system_info(self, state):
        """Update system information in state"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            state['system'] = {
                'memory_usage_mb': round(memory_info.rss / 1024 / 1024, 2),
                'cpu_percent': round(process.cpu_percent(), 2),
                'disk_usage_percent': round(psutil.disk_usage('.').percent, 2)
            }
            
            # Update uptime
            current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
            uptime = (current_time - self.script_start_time).total_seconds()
            state['statistics']['uptime_seconds'] = round(uptime)
            
        except Exception as e:
            self.logger.error(f"Failed to update system info: {e}")
    
    def update_status(self, status, details=None):
        """Update script status"""
        try:
            state = self._load_state()
            state['script']['status'] = status
            if details:
                state['script']['details'] = details
            
            self._update_system_info(state)
            state['last_updated'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            
            self._save_state(state)
            self.logger.debug(f"Status updated: {status}")
            
        except Exception as e:
            self.logger.error(f"Failed to update status: {e}")
    
    def start_operation(self, action, details=None):
        """Start a new operation"""
        try:
            state = self._load_state()
            state['current_operation'] = {
                'action': action,
                'details': details or f"Performing {action}",
                'start_time': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                'progress': 0
            }
            state['script']['status'] = 'active'
            
            self._update_system_info(state)
            state['last_updated'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            
            self._save_state(state)
            self.logger.debug(f"Started operation: {action}")
            
        except Exception as e:
            self.logger.error(f"Failed to start operation: {e}")
    
    def update_operation_progress(self, progress, details=None):
        """Update current operation progress"""
        try:
            state = self._load_state()
            if 'current_operation' in state:
                state['current_operation']['progress'] = progress
                if details:
                    state['current_operation']['details'] = details
                
                self._update_system_info(state)
                state['last_updated'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
                
                self._save_state(state)
            
        except Exception as e:
            self.logger.error(f"Failed to update operation progress: {e}")
    
    def complete_operation(self, success=True, result=None):
        """Complete current operation"""
        try:
            state = self._load_state()
            
            # Update statistics
            state['statistics']['total_operations'] += 1
            if success:
                state['statistics']['successful_operations'] += 1
            else:
                state['statistics']['failed_operations'] += 1
            
            # Mark operation as complete
            if 'current_operation' in state:
                action = state['current_operation'].get('action', 'unknown')
                state['current_operation'] = {
                    'action': 'idle',
                    'details': 'Waiting for next operation',
                    'last_completed': {
                        'action': action,
                        'success': success,
                        'result': result,
                        'completed_at': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
                    }
                }
            
            state['script']['status'] = 'idle'
            
            self._update_system_info(state)
            state['last_updated'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            
            self._save_state(state)
            self.logger.debug(f"Operation completed: success={success}")
            
        except Exception as e:
            self.logger.error(f"Failed to complete operation: {e}")
    
    def update_schedule_info(self, next_signin=None, next_signout=None, daemon_running=False):
        """Update schedule information"""
        try:
            state = self._load_state()
            state['schedule'] = {
                'next_signin': next_signin.isoformat() if next_signin else None,
                'next_signout': next_signout.isoformat() if next_signout else None,
                'daemon_running': daemon_running,
                'scheduler_active': daemon_running
            }
            
            self._update_system_info(state)
            state['last_updated'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            
            self._save_state(state)
            
        except Exception as e:
            self.logger.error(f"Failed to update schedule info: {e}")
    
    def update_today_summary(self):
        """Update today's attendance summary"""
        try:
            state_manager = AttendanceStateManager()
            summary = state_manager.get_status_summary()
            
            state = self._load_state()
            state['today_summary'] = summary
            
            # Update specific statistics
            state['statistics']['signin_attempts'] = summary.get('signin_attempts', 0)
            state['statistics']['signout_attempts'] = summary.get('signout_attempts', 0)
            
            if summary.get('signin_time'):
                state['statistics']['last_successful_signin'] = summary['signin_time']
            if summary.get('signout_time'):
                state['statistics']['last_successful_signout'] = summary['signout_time']
            
            self._update_system_info(state)
            state['last_updated'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            
            self._save_state(state)
            
        except Exception as e:
            self.logger.error(f"Failed to update today summary: {e}")
    
    def log_error(self, error_msg, retry_info=None):
        """Log an error to state"""
        try:
            state = self._load_state()
            state['errors'] = {
                'last_error': str(error_msg),
                'last_error_time': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
                'retry_info': retry_info or {}
            }
            state['script']['status'] = 'error'
            
            self._update_system_info(state)
            state['last_updated'] = datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
            
            self._save_state(state)
            
        except Exception as e:
            self.logger.error(f"Failed to log error to state: {e}")
    
    def get_current_state(self):
        """Get current state as dictionary"""
        try:
            state = self._load_state()
            self._update_system_info(state)
            return state
        except Exception as e:
            self.logger.error(f"Failed to get current state: {e}")
            return {}


class GreytHRAttendanceAPI:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get configuration from environment variables
        self.base_url = os.getenv('GREYTHR_URL')
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        
        self.api_base = f"{self.base_url.rstrip('/')}/v3/api"
        self.attendance_api = f"{self.api_base}/attendance/mark-attendance"
        
        # Initialize requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })

    def login_and_get_cookies(self, username, password):
        """
        Login using Selenium and extract cookies for API calls
        """
        if not SELENIUM_AVAILABLE:
            return False

        logger.info("🚀 Starting Login Process...")
        logger.info("=" * 50)
        logger.info("🚀 Starting browser-based login process...")
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = None
        try:
            # Initialize WebDriver
            logger.info("🔧 Setting up browser...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            
            # Login process
            logger.info(f"🔐 Logging in to: {self.base_url}")
            driver.get(self.base_url)
            time.sleep(5)  # Wait for JavaScript to load
            
            # Find and fill login fields
            logger.info("🔍 Finding login fields...")
            
            # Find username field
            username_selectors = [
                "input[name*='user']",
                "input[name*='email']", 
                "input[type='email']",
                "input[type='text']:first-of-type"
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Username field found")
                    break
                except:
                    continue
            
            if not username_field:
                logger.error("❌ Could not find username field")
                return False
            
            # Find password field
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                logger.info("✅ Password field found")
            except:
                logger.error("❌ Could not find password field")
                return False
            
            # Fill credentials
            logger.info("📝 Entering credentials...")
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # Submit login
            try:
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_button.click()
            except:
                password_field.send_keys(Keys.RETURN)
            
            logger.info("🔘 Login submitted, waiting...")
            time.sleep(5)
            
            # Check if login successful
            if "dashboard" in driver.current_url.lower() or "home" in driver.current_url.lower():
                logger.info("✅ Login successful!")
                logger.info(f"✅ Login successful - redirected to {driver.current_url}")
            else:
                logger.warning(f"⚠️ Redirected to: {driver.current_url}")
                logger.warning(f"⚠️ Unexpected redirect to: {driver.current_url}")
            
            # Extract cookies
            logger.info("🍪 Extracting cookies...")
            logger.info("🍪 Extracting cookies for API authentication...")
            selenium_cookies = driver.get_cookies()
            
            # Transfer cookies to requests session
            for cookie in selenium_cookies:
                self.session.cookies.set(
                    cookie['name'], 
                    cookie['value'],
                    domain=cookie.get('domain'),
                    path=cookie.get('path', '/'),
                    secure=cookie.get('secure', False)
                )
            
            logger.info(f"✅ Transferred {len(selenium_cookies)} cookies to session")
            logger.info(f"✅ Transferred {len(selenium_cookies)} cookies to requests session")
            
            # Log important cookies for debugging
            important_cookies = ['access_token', 'PLAY_SESSION']
            for cookie_name in important_cookies:
                cookie_value = self.session.cookies.get(cookie_name)
                if cookie_value:
                    logger.info(f"🔑 {cookie_name}: {cookie_value[:20]}...")
                    logger.debug(f"🔑 Found {cookie_name}: {cookie_value[:20]}...")
                else:
                    logger.warning(f"⚠️ {cookie_name}: Not found")
                    logger.warning(f"⚠️ {cookie_name}: Not found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Login error: {e}", exc_info=True)
            return False
            
        finally:
            if driver:
                logger.debug("🛑 Closing browser driver")
                driver.quit()

    def mark_attendance(self, action="Signin"):
        """
        Mark attendance using the API endpoint
        action can be "Signin" or "Signout"
        """
        logger.info(f"🎯 MARKING ATTENDANCE: {action.upper()}")
        logger.info("=" * 50)
        logger.info(f"🎯 Starting attendance API call: {action.upper()}")
        
        # Prepare API request
        url = f"{self.attendance_api}?action={action}"
        
        # Empty JSON payload as shown in your curl
        payload = {}
        
        logger.info(f"📤 API Request:")
        logger.info(f"   URL: {url}")
        logger.info(f"   Method: POST")
        logger.info(f"   Payload: {json.dumps(payload)}")
        
        logger.info(f"📤 API Request: POST {url}")
        logger.debug(f"📤 Request payload: {json.dumps(payload)}")
        
        try:
            # Make the API request
            response = self.session.post(
                url,
                json=payload,
                timeout=30
            )
            
            logger.info(f"📥 Response:")
            logger.info(f"   Status Code: {response.status_code}")
            logger.debug(f"   Headers: {dict(response.headers)}")
            
            logger.info(f"📥 API Response: Status {response.status_code}")
            logger.debug(f"📥 Response headers: {dict(response.headers)}")
            
            # Try to parse response as JSON
            try:
                response_data = response.json()
                logger.info(f"   JSON Response: {json.dumps(response_data, indent=2)}")
                logger.debug(f"📥 JSON Response: {json.dumps(response_data, indent=2)}")
            except:
                logger.info(f"   Text Response: {response.text}")
                logger.debug(f"📥 Text Response: {response.text}")
            
            if response.status_code == 200:
                logger.info(f"✅ {action} SUCCESSFUL!")
                logger.info(f"✅ {action} API call successful!")
                return True
            else:
                logger.error(f"❌ {action} FAILED! Status: {response.status_code}")
                logger.error(f"❌ {action} API call failed! Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API request error: {e}")
            logger.error(f"❌ API request error: {e}", exc_info=True)
            return False

    def run_full_automation(self, username, password, action="Signin"):
        """
        Complete flow: Login -> Mark Attendance via API
        """
        logger.info("🚀 GreytHR API Attendance Automation")
        logger.info("=" * 50)
        logger.info(f"🚀 Starting full automation: {action} for user {username}")
        
        # Step 1: Login and get cookies
        login_success = self.login_and_get_cookies(username, password)
        
        if not login_success:
            logger.error("❌ Login failed! Cannot proceed with attendance marking.")
            return False
        
        logger.info("⏳ Waiting 3 seconds before API call...")
        time.sleep(3)
        
        # Step 2: Mark attendance via API
        attendance_success = self.mark_attendance(action)
        
        return attendance_success

class GreytHRScheduler:
    """Background scheduler for automated attendance marking"""
    
    def __init__(self):
        load_dotenv()
        self.greythr_api = GreytHRAttendanceAPI()
        self.state_manager = AttendanceStateManager()
        self.username = os.getenv('GREYTHR_USERNAME')
        self.password = os.getenv('GREYTHR_PASSWORD')
        self.signin_time = os.getenv('SIGNIN_TIME', '09:00')
        self.signout_time = os.getenv('SIGNOUT_TIME', '19:00')
        self.timezone = pytz.timezone('Asia/Kolkata')  # IST timezone
        
        # Validate configuration
        if not all([self.username, self.password]):
            raise ValueError("Missing credentials in .env file")
        
        # Check test mode
        self.test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        
        logger.info(f"Scheduler initialized - Sign in: {self.signin_time} IST, Sign out: {self.signout_time} IST")
        if self.test_mode:
            logger.info("🧪 TEST MODE ENABLED: Will run on weekends and bypass normal restrictions")
        
        # Show current status
        status = self.state_manager.get_status_summary()
        logger.info(f"Today's status: Sign-in {status['signin_status']}, Sign-out {status['signout_status']}")
    
    def scheduled_signin(self, is_retry=False):
        """Scheduled sign-in function with retry support"""
        # Check if already completed today
        if self.state_manager.is_signin_completed():
            if is_retry:
                self.state_manager.clear_retry_schedule('signin')
            logger.info("ℹ️ Sign-in already completed today, skipping...")
            return
        
        attempt_type = "RETRY" if is_retry else "SCHEDULED"
        logger.info(f"🌅 Starting {attempt_type} SIGN IN...")
        
        try:
            success = self.greythr_api.run_full_automation(self.username, self.password, "Signin")
            if success:
                self.state_manager.mark_signin_completed()
                self.state_manager.clear_retry_schedule('signin')
                logger.info(f"✅ {attempt_type} SIGN IN completed successfully!")
            else:
                error_msg = f"{attempt_type} sign-in failed - unknown error"
                self.state_manager.mark_signin_failed(error_msg)
                logger.error(f"❌ {attempt_type} SIGN IN failed!")
                
        except Exception as e:
            error_msg = f"{attempt_type} sign-in error: {str(e)}"
            self.state_manager.mark_signin_failed(error_msg)
            logger.error(f"❌ {attempt_type} SIGN IN error: {e}")
    
    def scheduled_signout(self, is_retry=False):
        """Scheduled sign-out function with retry support"""
        # Check if already completed today
        if self.state_manager.is_signout_completed():
            if is_retry:
                self.state_manager.clear_retry_schedule('signout')
            logger.info("ℹ️ Sign-out already completed today, skipping...")
            return
            
        # Check if sign-in was done first
        if not self.state_manager.is_signin_completed():
            error_msg = "Cannot sign out - no sign-in recorded for today"
            if is_retry:
                self.state_manager.mark_signout_failed(error_msg)
            logger.warning(f"⚠️ {error_msg}!")
            return
        
        attempt_type = "RETRY" if is_retry else "SCHEDULED"
        logger.info(f"🌇 Starting {attempt_type} SIGN OUT...")
        
        try:
            success = self.greythr_api.run_full_automation(self.username, self.password, "Signout")
            if success:
                self.state_manager.mark_signout_completed()
                self.state_manager.clear_retry_schedule('signout')
                logger.info(f"✅ {attempt_type} SIGN OUT completed successfully!")
            else:
                error_msg = f"{attempt_type} sign-out failed - unknown error"
                self.state_manager.mark_signout_failed(error_msg)
                logger.error(f"❌ {attempt_type} SIGN OUT failed!")
                
        except Exception as e:
            error_msg = f"{attempt_type} sign-out error: {str(e)}"
            self.state_manager.mark_signout_failed(error_msg)
            logger.error(f"❌ {attempt_type} SIGN OUT error: {e}")
    
    def check_and_catchup(self):
        """Check if any attendance actions are overdue and execute them"""
        logger.info("🔍 Checking for overdue attendance actions...")
        
        current_time = datetime.now(self.timezone)
        is_weekday = current_time.weekday() < 5  # Monday=0, Friday=4
        test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        
        if not is_weekday and not test_mode:
            logger.info("📅 It's weekend, skipping catch-up checks (use TEST_MODE=true to override)")
            return
        
        if test_mode:
            logger.info("🧪 TEST MODE: Running checks regardless of day of week")
            
        # Check for retries first
        if self.state_manager.should_retry_signin_now():
            logger.info("🔄 RETRY: Sign-in retry time reached!")
            self.scheduled_signin(is_retry=True)
        elif self.state_manager.should_signin_now(self.signin_time, self.signout_time):
            logger.info("🚨 CATCH-UP: Sign-in is overdue! Executing now...")
            self.scheduled_signin()
        
        if self.state_manager.should_retry_signout_now():
            logger.info("🔄 RETRY: Sign-out retry time reached!")
            self.scheduled_signout(is_retry=True)
        elif self.state_manager.should_signout_now(self.signout_time):
            logger.info("🚨 CATCH-UP: Sign-out is overdue! Executing now...")
            self.scheduled_signout()
    
    def start_scheduler(self):
        """Start the background scheduler"""
        logger.info("🚀 Starting GreytHR Background Scheduler...")
        
        # First, check for any overdue actions (catch-up logic)
        self.check_and_catchup()
        
        # Schedule sign-in and sign-out
        if self.test_mode:
            # In test mode, schedule for every day of the week
            schedule.every().day.at(self.signin_time).do(self.scheduled_signin)
            schedule.every().day.at(self.signout_time).do(self.scheduled_signout)
            logger.info("🧪 TEST MODE: Scheduled for ALL DAYS (Mon-Sun)")
        else:
            # Normal mode - weekdays only
            schedule.every().monday.at(self.signin_time).do(self.scheduled_signin)
            schedule.every().tuesday.at(self.signin_time).do(self.scheduled_signin)
            schedule.every().wednesday.at(self.signin_time).do(self.scheduled_signin)
            schedule.every().thursday.at(self.signin_time).do(self.scheduled_signin)
            schedule.every().friday.at(self.signin_time).do(self.scheduled_signin)
            
            schedule.every().monday.at(self.signout_time).do(self.scheduled_signout)
            schedule.every().tuesday.at(self.signout_time).do(self.scheduled_signout)
            schedule.every().wednesday.at(self.signout_time).do(self.scheduled_signout)
            schedule.every().thursday.at(self.signout_time).do(self.scheduled_signout)
            schedule.every().friday.at(self.signout_time).do(self.scheduled_signout)
            
            logger.info("📅 Scheduled for weekdays (Mon-Fri)")
        if schedule.jobs:
            logger.info(f"⏰ Next scheduled job: {schedule.next_run()}")
        
        # Run scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                
                # Check for retries every minute (more frequent than regular schedule)
                try:
                    if self.state_manager.should_retry_signin_now():
                        logger.info("🔄 RETRY: Sign-in retry time reached (background check)!")
                        self.scheduled_signin(is_retry=True)
                    
                    if self.state_manager.should_retry_signout_now():
                        logger.info("🔄 RETRY: Sign-out retry time reached (background check)!")
                        self.scheduled_signout(is_retry=True)
                except Exception as e:
                    logger.error(f"❌ Error during retry check: {e}")
                
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        return scheduler_thread

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GreytHR Attendance Automation')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode (for startup services)')
    args = parser.parse_args()
    
    if not SELENIUM_AVAILABLE:
        logger.error("❌ Selenium not installed! Run: pip install selenium webdriver-manager")
        return
    
    # Initialize single instance manager
    instance_manager = SingleInstanceManager()
    if not instance_manager.acquire_lock():
        return 1  # Exit with error code if another instance is running
    
    # Check if test mode is enabled for display
    test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    
    # Log startup
    logger.info("=" * 50)
    logger.info("🎯 GreytHR Attendance Automation Started")
    logger.info(f"🧪 Test Mode: {'ENABLED' if test_mode else 'DISABLED'}")
    logger.info(f"📅 Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    logger.info("=" * 50)
    
    # Initialize state tracker for dashboard monitoring
    state_tracker = StateTracker()
    state_tracker.update_status('starting', 'Initializing GreytHR automation script')
    
    # Handle daemon mode
    if args.daemon:
        logger.info("🤖 DAEMON MODE - Running in background")
        logger.info("🔒 Single instance protection: ENABLED")
        
        # Get credentials from environment variables
        url = os.getenv('GREYTHR_URL')
        username = os.getenv('GREYTHR_USERNAME')
        password = os.getenv('GREYTHR_PASSWORD')
        signin_time = os.getenv('SIGNIN_TIME')
        signout_time = os.getenv('SIGNOUT_TIME')
        
        if not all([url, username, password, signin_time, signout_time]):
            logger.error("❌ Missing required environment variables for daemon mode!")
            logger.error("Required: GREYTHR_URL, GREYTHR_USERNAME, GREYTHR_PASSWORD, SIGNIN_TIME, SIGNOUT_TIME")
            return 1
        
        logger.info(f"✅ Configuration loaded - Sign in: {signin_time}, Sign out: {signout_time}")
        logger.info("🚀 Starting background scheduler...")
        
        try:
            # Start the scheduler in daemon mode
            scheduler = GreytHRScheduler()
            scheduler_thread = scheduler.start_scheduler()
            state_tracker.update_schedule_info(daemon_running=True)
            state_tracker.update_status('daemon_running', 'Background scheduler active')
            
            logger.info("✅ Background scheduler started successfully!")
            logger.info(f"📋 The daemon will automatically:")
            logger.info(f"   • Sign in at {scheduler.signin_time} IST on {'all days' if test_mode else 'weekdays'}")
            logger.info(f"   • Sign out at {scheduler.signout_time} IST on {'all days' if test_mode else 'weekdays'}")
            logger.info(f"   • Retry failed attempts with exponential backoff")
            logger.info(f"   • Log all activities to: {Path.cwd() / 'logs'}")
            logger.info(f"   • Store state data to: {Path.cwd() / 'state'}")
            logger.info("🔄 Daemon is now running... (Ctrl+C to stop)")
            
            # Keep the main thread alive in daemon mode
            try:
                while True:
                    time.sleep(60)  # Check every minute
                    state_tracker.update_today_summary()  # Update state periodically
            except KeyboardInterrupt:
                logger.info("📡 Received interrupt signal, shutting down gracefully...")
                state_tracker.update_status('shutting_down', 'Daemon received shutdown signal')
            
        except Exception as e:
            logger.error(f"❌ Failed to start daemon: {e}")
            state_tracker.log_error(f"Daemon startup failed: {str(e)}")
            return 1
        
        logger.info("👋 Daemon shutdown complete")
        return 0
    
    if test_mode:
        logger.info("🧪 GreytHR API Attendance Automation - TEST MODE")
        logger.info("=" * 50)
        logger.info("⚠️  TEST MODE ENABLED - Will run on weekends!")
    else:
        logger.info("🎯 GreytHR API Attendance Automation")
        logger.info("=" * 40)
    logger.info("This uses the API endpoint you discovered!")
    
    # Get credentials from environment variables
    url = os.getenv('GREYTHR_URL')
    username = os.getenv('GREYTHR_USERNAME')
    password = os.getenv('GREYTHR_PASSWORD')
    
    if not url or not username or not password:
        logger.error("❌ Credentials not found in environment!")
        logger.info("Please create a .env file with:")
        logger.info("GREYTHR_URL=https://company.greythr.com")
        logger.info("GREYTHR_USERNAME=your_username")
        logger.info("GREYTHR_PASSWORD=your_password")
        logger.info("SIGNIN_TIME=09:00")
        logger.info("SIGNOUT_TIME=19:00")
        logger.info("TEST_MODE=true  # For testing on weekends")
        logger.info("MAX_RETRY_ATTEMPTS=5  # Max retry attempts per action")
        logger.info("BASE_RETRY_DELAY=300  # Base delay in seconds (5min)")
        return
    
    # Choose action
    logger.info("\nChoose mode:")
    logger.info("1. ✅ Manual Sign In")
    logger.info("2. ❌ Manual Sign Out") 
    logger.info("3. 🔄 Test Both (Sign In, wait, then Sign Out)")
    logger.info("4. 🕐 Background Daemon Mode (Auto Sign In/Out)")
    logger.info("5. 📊 View Today's Status")
    logger.info("6. ℹ️  View Schedule Configuration")
    logger.info("7. 🚨 Force Catch-up Check (Check for missed attendance)")
    logger.info("8. 🧪 Test Missed Window Logic (Debug)")
    logger.info("9. 📊 View Current Script State (Dashboard Data)")
    
    choice = input("Choose (1-9): ").strip()
    
    # Create API automation instance
    greythr_api = GreytHRAttendanceAPI()
    
    success = True  # Default success for non-immediate actions
    
    if choice == "1":
        logger.info("👤 User selected: Manual Sign In")
        state_tracker.start_operation("manual_signin", "User initiated manual sign-in")
        state_manager = AttendanceStateManager()
        try:
            success = greythr_api.run_full_automation(username, password, "Signin")
            if success:
                state_manager.mark_signin_completed()
                state_manager.clear_retry_schedule('signin')
                logger.info("✅ Manual sign-in completed successfully")
                state_tracker.complete_operation(success=True, result="Manual sign-in successful")
            else:
                state_manager.mark_signin_failed("Manual sign-in failed - unknown error")
                logger.error("❌ Manual sign-in failed")
                state_tracker.complete_operation(success=False, result="Manual sign-in failed")
        except Exception as e:
            state_manager.mark_signin_failed(f"Manual sign-in error: {str(e)}")
            logger.error(f"❌ Manual sign-in error: {e}")
            success = False
            state_tracker.log_error(f"Manual sign-in error: {str(e)}")
            state_tracker.complete_operation(success=False, result="Manual sign-in error")
        
    elif choice == "2":
        logger.info("👤 User selected: Manual Sign Out")
        state_tracker.start_operation("manual_signout", "User initiated manual sign-out")
        state_manager = AttendanceStateManager()
        try:
            success = greythr_api.run_full_automation(username, password, "Signout")
            if success:
                state_manager.mark_signout_completed()
                state_manager.clear_retry_schedule('signout')
                logger.info("✅ Manual sign-out completed successfully")
                state_tracker.complete_operation(success=True, result="Manual sign-out successful")
            else:
                state_manager.mark_signout_failed("Manual sign-out failed - unknown error")
                logger.error("❌ Manual sign-out failed")
                state_tracker.complete_operation(success=False, result="Manual sign-out failed")
        except Exception as e:
            state_manager.mark_signout_failed(f"Manual sign-out error: {str(e)}")
            logger.error(f"❌ Manual sign-out error: {e}")
            success = False
            state_tracker.log_error(f"Manual sign-out error: {str(e)}")
            state_tracker.complete_operation(success=False, result="Manual sign-out error")
        
    elif choice == "3":
        logger.info("🔄 Testing both actions...")
        state_tracker.start_operation("test_both", "Testing both sign-in and sign-out")
        state_manager = AttendanceStateManager()
        
        # Sign In
        try:
            signin_success = greythr_api.run_full_automation(username, password, "Signin")
            if signin_success:
                state_manager.mark_signin_completed()
                state_manager.clear_retry_schedule('signin')
            else:
                state_manager.mark_signin_failed("Test sign-in failed - unknown error")
        except Exception as e:
            state_manager.mark_signin_failed(f"Test sign-in error: {str(e)}")
            signin_success = False
        
        if signin_success:
            logger.info("⏳ Waiting 30 seconds before sign out...")
            state_tracker.update_operation_progress(50, "Sign-in completed, waiting 30 seconds before sign-out")
            for i in range(30, 0, -1):
                logger.info(f"⏰ {i} seconds remaining...")
                progress = 50 + ((30 - i) / 30) * 25  # Progress from 50% to 75%
                state_tracker.update_operation_progress(progress, f"Waiting {i} seconds before sign-out")
                time.sleep(1)
            logger.info("Proceeding to sign out...")
            state_tracker.update_operation_progress(75, "Starting sign-out process")
            
            # Sign Out (reuse the same session)
            try:
                signout_success = greythr_api.mark_attendance("Signout")
                if signout_success:
                    state_manager.mark_signout_completed()
                    state_manager.clear_retry_schedule('signout')
                else:
                    state_manager.mark_signout_failed("Test sign-out failed - unknown error")
            except Exception as e:
                state_manager.mark_signout_failed(f"Test sign-out error: {str(e)}")
                signout_success = False
                
            success = signin_success and signout_success
        else:
            success = False
        
        # Complete the test both operation
        if success:
            state_tracker.complete_operation(success=True, result="Both sign-in and sign-out completed successfully")
        else:
            state_tracker.complete_operation(success=False, result="Test both operation failed")
            
    elif choice == "4":
        logger.info("🕐 Starting Background Daemon Mode...")
        logger.info("🕐 Starting Background Daemon Mode...")
        state_tracker.start_operation("daemon_mode", "Starting background daemon mode")
        
        try:
            scheduler = GreytHRScheduler()
            scheduler_thread = scheduler.start_scheduler()
            state_tracker.update_schedule_info(daemon_running=True)
            
            logger.info("✅ Background scheduler started successfully!")
            logger.info("📋 The script will now run in the background and automatically:")
            logger.info(f"   • Sign in at {scheduler.signin_time} IST on weekdays")
            logger.info(f"   • Sign out at {scheduler.signout_time} IST on weekdays")
            logger.info(f"📄 All logs are being written to: logs/greythr_attendance_{datetime.now().strftime('%Y-%m-%d')}.log")
            logger.info("⚠️  Keep this script running! Press Ctrl+C to stop.")
            
            # Log the same info
            logger.info("✅ Background scheduler started successfully!")
            logger.info(f"📋 Automatic sign-in at {scheduler.signin_time} IST, sign-out at {scheduler.signout_time} IST")
            
            try:
                while True:
                    time.sleep(60)  # Keep main thread alive
            except KeyboardInterrupt:
                logger.info("👋 Background scheduler stopped.")
                logger.info("👋 Background scheduler stopped by user")
                
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            logger.error(f"❌ Failed to start scheduler: {e}")
            success = False
            
    elif choice == "5":
        logger.info("📊 Today's Attendance Status:")
        logger.info("=" * 50)
        state_manager = AttendanceStateManager()
        status = state_manager.get_status_summary()
        
        logger.info(f"📅 Date: {status['date']}")
        logger.info(f"🌅 Sign In: {status['signin_status']}")
        if status['signin_time']:
            signin_dt = datetime.fromisoformat(status['signin_time'])
            logger.info(f"    ✅ Completed at: {signin_dt.strftime('%I:%M %p IST')}")
        
        logger.info(f"🌇 Sign Out: {status['signout_status']}")
        if status['signout_time']:
            signout_dt = datetime.fromisoformat(status['signout_time'])
            logger.info(f"    ✅ Completed at: {signout_dt.strftime('%I:%M %p IST')}")
            
        logger.info(f"📈 Attempt Statistics:")
        logger.info(f"   Sign-in: {status['signin_attempts']} total, {status['signin_failed_attempts']} failed")
        logger.info(f"   Sign-out: {status['signout_attempts']} total, {status['signout_failed_attempts']} failed")
        
        # Show retry information if applicable
        if status.get('signin_next_retry'):
            retry_time = datetime.fromisoformat(status['signin_next_retry'])
            logger.info(f"🔄 Sign-in Retry: Scheduled for {retry_time.strftime('%I:%M %p IST')}")
            if status.get('signin_last_error'):
                logger.info(f"   Last Error: {status['signin_last_error']}")
                
        if status.get('signout_next_retry'):
            retry_time = datetime.fromisoformat(status['signout_next_retry'])
            logger.info(f"🔄 Sign-out Retry: Scheduled for {retry_time.strftime('%I:%M %p IST')}")
            if status.get('signout_last_error'):
                logger.info(f"   Last Error: {status['signout_last_error']}")
        
        logger.info("=" * 50)
        return  # Don't show success/failure message
        
    elif choice == "6":
        logger.info("📅 Current Schedule Configuration:")
        logger.info("=" * 50)
        signin_time = os.getenv('SIGNIN_TIME', '09:00')
        signout_time = os.getenv('SIGNOUT_TIME', '19:00')
        test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        max_retries = os.getenv('MAX_RETRY_ATTEMPTS', '5')
        base_delay = int(os.getenv('BASE_RETRY_DELAY', '300')) // 60
        
        logger.info(f"🌅 Sign In Time: {signin_time} IST")
        logger.info(f"🌇 Sign Out Time: {signout_time} IST")
        if test_mode:
            logger.info("📅 Days: ALL DAYS (Mon-Sun) - 🧪 TEST MODE")
            logger.info("🧪 TEST MODE: ENABLED")
        else:
            logger.info("📅 Days: Monday to Friday")
            logger.info("🧪 TEST MODE: Disabled")
        logger.info("🕐 Timezone: Asia/Kolkata (IST)")
        
        logger.info(f"🔄 Retry Configuration:")
        logger.info(f"   Max Attempts: {max_retries}")
        logger.info(f"   Base Delay: {base_delay} minutes")
        logger.info(f"   Retry Schedule: {base_delay}min → {base_delay*3}min → {base_delay*9}min → {base_delay*27}min → {base_delay*81}min")
        
        logger.info(f"📂 Storage:")
        logger.info("   Activities: ./activities/")
        logger.info("   Logs: ./logs/")
        logger.info("=" * 50)
        return  # Don't show success/failure message
        
    elif choice == "7":
        logger.info("🚨 Running Catch-up Check...")
        logger.info("👤 User selected: Force Catch-up Check")
        scheduler = GreytHRScheduler()
        scheduler.check_and_catchup()
        logger.info("✅ Catch-up check completed!")
        logger.info("✅ Manual catch-up check completed")
        return  # Don't show success/failure message
        
    elif choice == "8":
        logger.info("🧪 Testing Missed Window Logic...")
        logger.info("=" * 40)
        state_manager = AttendanceStateManager()
        signin_time = os.getenv('SIGNIN_TIME', '09:00')
        signout_time = os.getenv('SIGNOUT_TIME', '19:00')
        
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        logger.info(f"⏰ Current Time: {current_time.strftime('%H:%M')}")
        logger.info(f"📅 Sign-in Time: {signin_time}")
        logger.info(f"📅 Sign-out Time: {signout_time}")
        logger.info("")
        
        # Test sign-in logic
        should_signin = state_manager.should_signin_now(signin_time, signout_time)
        logger.info(f"🔍 Should Sign-in Now: {'✅ YES' if should_signin else '❌ NO'}")
        
        # Test sign-out logic  
        should_signout = state_manager.should_signout_now(signout_time)
        logger.info(f"🔍 Should Sign-out Now: {'✅ YES' if should_signout else '❌ NO'}")
        
        logger.info("📊 Current Status:")
        signin_completed = state_manager.is_signin_completed()
        signout_completed = state_manager.is_signout_completed()
        logger.info(f"   Sign-in Completed: {'✅ YES' if signin_completed else '❌ NO'}")
        logger.info(f"   Sign-out Completed: {'✅ YES' if signout_completed else '❌ NO'}")
        
        logger.info("=" * 40)
        return  # Don't show success/failure message
        
    elif choice == "9":
        logger.info("📊 Current Script State (Dashboard Data):")
        logger.info("=" * 50)
        
        # Update today's summary first
        state_tracker.update_today_summary()
        current_state = state_tracker.get_current_state()
        
        # Display formatted state information
        logger.info(f"🖥️  Script Information:")
        script_info = current_state.get('script', {})
        logger.info(f"   Status: {script_info.get('status', 'unknown')}")
        logger.info(f"   Start Time: {script_info.get('start_time', 'unknown')}")
        logger.info(f"   PID: {script_info.get('pid', 'unknown')}")
        logger.info(f"   Platform: {script_info.get('platform', 'unknown')}")
        
        logger.info(f"\n🔄 Current Operation:")
        operation = current_state.get('current_operation', {})
        logger.info(f"   Action: {operation.get('action', 'unknown')}")
        logger.info(f"   Details: {operation.get('details', 'N/A')}")
        logger.info(f"   Progress: {operation.get('progress', 0)}%")
        
        logger.info(f"\n⚙️  Configuration:")
        config = current_state.get('configuration', {})
        logger.info(f"   Sign-in Time: {config.get('signin_time', 'N/A')} IST")
        logger.info(f"   Sign-out Time: {config.get('signout_time', 'N/A')} IST")
        logger.info(f"   Test Mode: {'ENABLED' if config.get('test_mode') else 'DISABLED'}")
        logger.info(f"   Max Retry Attempts: {config.get('max_retry_attempts', 'N/A')}")
        
        logger.info(f"\n⏰ Schedule:")
        schedule_info = current_state.get('schedule', {})
        next_signin = schedule_info.get('next_signin')
        next_signout = schedule_info.get('next_signout')
        logger.info(f"   Next Sign-in: {next_signin if next_signin else 'Not scheduled'}")
        logger.info(f"   Next Sign-out: {next_signout if next_signout else 'Not scheduled'}")
        logger.info(f"   Daemon Running: {'✅ YES' if schedule_info.get('daemon_running') else '❌ NO'}")
        
        logger.info(f"\n📈 Statistics:")
        stats = current_state.get('statistics', {})
        logger.info(f"   Total Operations: {stats.get('total_operations', 0)}")
        logger.info(f"   Successful: {stats.get('successful_operations', 0)}")
        logger.info(f"   Failed: {stats.get('failed_operations', 0)}")
        logger.info(f"   Uptime: {stats.get('uptime_seconds', 0)} seconds")
        
        logger.info(f"\n🖥️  System Resources:")
        system = current_state.get('system', {})
        logger.info(f"   Memory Usage: {system.get('memory_usage_mb', 0)} MB")
        logger.info(f"   CPU Usage: {system.get('cpu_percent', 0)}%")
        logger.info(f"   Disk Usage: {system.get('disk_usage_percent', 0)}%")
        
        logger.info(f"\n📅 Today's Summary:")
        today_summary = current_state.get('today_summary', {})
        if today_summary:
            logger.info(f"   Date: {today_summary.get('date', 'N/A')}")
            logger.info(f"   Sign-in Status: {today_summary.get('signin_status', 'N/A')}")
            logger.info(f"   Sign-out Status: {today_summary.get('signout_status', 'N/A')}")
            logger.info(f"   Total Attempts: {today_summary.get('signin_attempts', 0)} + {today_summary.get('signout_attempts', 0)}")
        
        errors = current_state.get('errors', {})
        if errors.get('last_error'):
            logger.info(f"\n❌ Last Error:")
            logger.info(f"   Error: {errors.get('last_error', 'N/A')}")
            logger.info(f"   Time: {errors.get('last_error_time', 'N/A')}")
        
        logger.info("=" * 50)
        logger.info("💾 State file location: state/current_state.json")
        logger.info("📊 This data is perfect for building dashboards!")
        logger.info("=" * 50)
        return  # Don't show success/failure message
        
    else:
        logger.error("❌ Invalid choice!")
        return
    
    # Only show success/failure for immediate actions
    if choice in ["1", "2", "3"]:
        logger.info("=" * 50)
    if success:
            logger.info("🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
            logger.info("🎉 Automation completed successfully")
    else:
            logger.error("❌ AUTOMATION FAILED!")
            logger.info("❌ Automation failed")
            logger.info("=" * 50)
    
    # Log script exit (except for daemon mode)
    if choice != "4":
        state_tracker.update_status('idle', 'Script completed, waiting for next user action')
        logger.info("👋 Script execution completed")

if __name__ == "__main__":
    main()
