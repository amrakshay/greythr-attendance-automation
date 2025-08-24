"""
Logs repository for managing system logs
"""

import logging
import re
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
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
                all_logs = [log for log in all_logs if log.get('level', '').lower() == level.lower()]
            
            # Apply limit
            if limit > 0:
                all_logs = all_logs[:limit]
            
            return {
                'logs': all_logs,
                'total': len(all_logs),
                'generated_at': datetime.now().isoformat(),
                'filters': {
                    'level': level,
                    'date': date_filter,
                    'limit': limit
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return {'logs': [], 'total': 0, 'error': str(e)}
    
    async def _read_log_file(self, file_path: Path, date_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Read and parse a single log file"""
        logs = []
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
                
            lines = content.strip().split('\n')
            for line in lines:
                if not line.strip():
                    continue
                
                try:
                    log_entry = self._parse_log_line(line)
                    if log_entry:
                        # Apply date filter if specified
                        if date_filter:
                            log_date = log_entry.get('timestamp', '')[:10]  # Get YYYY-MM-DD part
                            if log_date != date_filter:
                                continue
                        
                        log_entry['file'] = file_path.name
                        logs.append(log_entry)
                except Exception as e:
                    # If parsing fails, include as raw log
                    logs.append({
                        'timestamp': datetime.now().isoformat(),
                        'level': 'UNKNOWN',
                        'message': line.strip(),
                        'file': file_path.name,
                        'raw': True
                    })
            
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")
        
        return logs
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line into structured data"""
        try:
            # Common log patterns
            patterns = [
                # Standard Python logging format: YYYY-MM-DD HH:MM:SS,mmm - LEVEL - MESSAGE
                r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - (\w+) - (.+)$',
                # ISO timestamp format: YYYY-MM-DDTHH:MM:SS - LEVEL - MESSAGE
                r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\.\d]*) - (\w+) - (.+)$',
                # Simple timestamp: YYYY-MM-DD HH:MM:SS LEVEL MESSAGE
                r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (.+)$',
                # Syslog style: MMM DD HH:MM:SS LEVEL MESSAGE
                r'^(\w{3} \d{1,2} \d{2}:\d{2}:\d{2}) (\w+) (.+)$',
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    timestamp_str, level, message = match.groups()
                    
                    # Parse timestamp
                    try:
                        if 'T' in timestamp_str:
                            # ISO format
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        elif ',' in timestamp_str:
                            # Python logging format
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        elif len(timestamp_str) == 19:  # YYYY-MM-DD HH:MM:SS
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        else:
                            # Syslog format - assume current year
                            current_year = datetime.now().year
                            timestamp = datetime.strptime(f"{current_year} {timestamp_str}", '%Y %b %d %H:%M:%S')
                    except ValueError:
                        # Fallback to current time
                        timestamp = datetime.now()
                    
                    return {
                        'timestamp': timestamp.isoformat(),
                        'level': level.upper(),
                        'message': message.strip(),
                        'raw_line': line.strip()
                    }
            
            # If no pattern matches, treat as unstructured log
            return {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': line.strip(),
                'raw_line': line.strip(),
                'unstructured': True
            }
            
        except Exception as e:
            logger.error(f"Error parsing log line: {e}")
            return None
    
    async def search_logs(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Search logs for specific terms"""
        try:
            # Get all recent logs
            all_logs = await self.get_recent_logs(limit=10000)  # Get more logs for search
            
            # Filter logs by search query
            matching_logs = []
            query_lower = query.lower()
            
            for log in all_logs.get('logs', []):
                message = log.get('message', '').lower()
                if query_lower in message:
                    # Highlight search terms
                    highlighted_message = re.sub(
                        re.escape(query), 
                        f"<mark>{query}</mark>", 
                        log.get('message', ''), 
                        flags=re.IGNORECASE
                    )
                    
                    enhanced_log = log.copy()
                    enhanced_log['highlighted_message'] = highlighted_message
                    matching_logs.append(enhanced_log)
            
            # Apply limit
            if limit > 0:
                matching_logs = matching_logs[:limit]
            
            return {
                'logs': matching_logs,
                'total': len(matching_logs),
                'query': query,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return {'logs': [], 'total': 0, 'error': str(e)}
    
    async def get_log_statistics(self) -> Dict[str, Any]:
        """Get log statistics"""
        try:
            if not self.logs_dir.exists():
                return {'total_files': 0, 'total_size': 0, 'level_counts': {}}
            
            total_files = 0
            total_size = 0
            level_counts = {}
            file_info = []
            
            # Analyze log files
            for file_path in self.logs_dir.glob("*.log"):
                try:
                    stat = file_path.stat()
                    total_files += 1
                    total_size += stat.st_size
                    
                    file_info.append({
                        'name': file_path.name,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                    
                    # Sample file for level analysis (only read first 1000 lines)
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = []
                            for i in range(1000):
                                line = await f.readline()
                                if not line:
                                    break
                                lines.append(line)
                        
                        for line in lines:
                            log_entry = self._parse_log_line(line)
                            if log_entry:
                                level = log_entry.get('level', 'UNKNOWN')
                                level_counts[level] = level_counts.get(level, 0) + 1
                    except Exception:
                        continue
                        
                except OSError:
                    continue
            
            # Sort files by modification time
            file_info.sort(key=lambda x: x['modified'], reverse=True)
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'level_counts': level_counts,
                'files': file_info[:10],  # Most recent 10 files
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {'error': str(e)}
    
    async def clear_logs(self, older_than_days: Optional[int] = None) -> Dict[str, Any]:
        """Clear log files"""
        try:
            if not self.logs_dir.exists():
                return {'deleted_files': 0, 'message': 'Logs directory does not exist'}
            
            deleted_files = 0
            deleted_size = 0
            cutoff_date = None
            
            if older_than_days:
                cutoff_date = datetime.now() - timedelta(days=older_than_days)
            
            for file_path in self.logs_dir.glob("*.log"):
                try:
                    if cutoff_date:
                        stat = file_path.stat()
                        file_date = datetime.fromtimestamp(stat.st_mtime)
                        if file_date > cutoff_date:
                            continue  # Skip newer files
                    
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_files += 1
                    deleted_size += file_size
                    
                except OSError as e:
                    logger.error(f"Error deleting log file {file_path}: {e}")
                    continue
            
            return {
                'deleted_files': deleted_files,
                'deleted_size': deleted_size,
                'deleted_size_mb': round(deleted_size / 1024 / 1024, 2),
                'cutoff_date': cutoff_date.isoformat() if cutoff_date else None,
                'message': f"Deleted {deleted_files} log files"
            }
            
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
            return {'error': str(e)}
    
    async def get_log_files(self) -> List[Dict[str, Any]]:
        """Get list of available log files"""
        try:
            if not self.logs_dir.exists():
                return []
            
            files = []
            for file_path in self.logs_dir.glob("*.log"):
                try:
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / 1024 / 1024, 2),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'readable': os.access(file_path, os.R_OK)
                    })
                except OSError:
                    continue
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"Error getting log files: {e}")
            return []
