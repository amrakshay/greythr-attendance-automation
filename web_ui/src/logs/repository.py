"""
Logs repository for managing system logs
"""

import logging
import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

import aiofiles

logger = logging.getLogger('webui.logs.repository')

class LogsRepository:
    """Repository for managing system logs"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.logs_dir = self.project_path / "logs"
        
    async def get_recent_logs(self, limit: int = 500, level: Optional[str] = None, 
                            date_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get recent log entries"""
        try:
            if not self.logs_dir.exists():
                return {'logs': [], 'total': 0}
            
            all_logs = []
            
            # Get all log files sorted by modification time
            log_files = []
            for file_path in self.logs_dir.glob("*.log"):
                try:
                    stat = file_path.stat()
                    log_files.append((file_path, stat.st_mtime))
                except OSError:
                    continue
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x[1], reverse=True)
            
            # Read logs from files
            for file_path, _ in log_files[:10]:  # Limit to 10 most recent files
                try:
                    file_logs = await self._read_log_file(file_path, date_filter)
                    all_logs.extend(file_logs)
                except Exception as e:
                    logger.error(f"Error reading log file {file_path}: {e}")
                    continue
            
            # Sort all logs by timestamp (newest first)
            all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Filter by level if specified
            if level:
                level_upper = level.upper()
                all_logs = [log for log in all_logs if log.get('level', '').upper() == level_upper]
            
            # Apply limit
            if limit > 0:
                all_logs = all_logs[:limit]
            
            return {
                'logs': all_logs,
                'total': len(all_logs),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return {'logs': [], 'total': 0, 'error': str(e)}
    
    async def _read_log_file(self, file_path: Path, date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Read logs from a specific file"""
        logs = []
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
                
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                log_entry = self._parse_log_line(line)
                if log_entry:
                    # Apply date filter if specified
                    if date_filter:
                        log_date = log_entry.get('timestamp', '')[:10]  # Get YYYY-MM-DD part
                        if log_date != date_filter:
                            continue
                    
                    logs.append(log_entry)
                        
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")
            
        return logs
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line into structured data"""
        try:
            # Pattern for typical log format: 2024-01-01 12:00:00,123 - LEVEL - module - message
            pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s*-\s*(\w+)\s*-\s*([^-]+)\s*-\s*(.*)$'
            match = re.match(pattern, line)
            
            if match:
                timestamp_str, level, module, message = match.groups()
                
                # Parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    iso_timestamp = timestamp.isoformat()
                except:
                    iso_timestamp = timestamp_str
                
                return {
                    'timestamp': iso_timestamp,
                    'level': level.strip(),
                    'module': module.strip(),
                    'message': message.strip(),
                    'raw_line': line
                }
            else:
                # For lines that don't match the pattern, treat as raw message
                return {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'module': 'unknown',
                    'message': line,
                    'raw_line': line
                }
            
        except Exception as e:
            logger.error(f"Error parsing log line: {e}")
            return None