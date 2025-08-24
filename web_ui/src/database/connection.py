"""
Database/File system connection management
Since GreytHR uses JSON files, this module handles file system operations
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiofiles
import glob

logger = logging.getLogger('webui.database')

class FileSystemRepository:
    """Base repository class for file system operations"""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        
    async def read_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read JSON file asynchronously"""
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None
                
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    async def write_json_file(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """Write JSON file asynchronously"""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(data, indent=2, default=str))
            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False
    
    async def read_text_file(self, file_path: Path) -> Optional[str]:
        """Read text file asynchronously"""
        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return None
                
            async with aiofiles.open(file_path, 'r') as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return None
    
    def list_files(self, directory: Path, pattern: str = "*") -> List[Path]:
        """List files in directory with pattern"""
        try:
            if not directory.exists():
                logger.warning(f"Directory not found: {directory}")
                return []
                
            files = list(directory.glob(pattern))
            return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {e}")
            return []

class StateRepository(FileSystemRepository):
    """Repository for state file operations"""
    
    def __init__(self, project_path: Path):
        super().__init__(project_path)
        self.state_dir = self.base_path / "state"
        
    async def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get current system state"""
        state_file = self.state_dir / "current_state.json"
        return await self.read_json_file(state_file)
    
    async def update_state(self, state_data: Dict[str, Any]) -> bool:
        """Update current system state"""
        state_file = self.state_dir / "current_state.json"
        return await self.write_json_file(state_file, state_data)

class ActivitiesRepository(FileSystemRepository):
    """Repository for activities/attendance data operations"""
    
    def __init__(self, project_path: Path):
        super().__init__(project_path)
        self.activities_dir = self.base_path / "activities"
        
    async def get_activity_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """Get activity data for specific date"""
        activity_file = self.activities_dir / f"attendance_{date}.json"
        return await self.read_json_file(activity_file)
    
    async def list_activity_files(self) -> List[str]:
        """List all activity files"""
        files = self.list_files(self.activities_dir, "attendance_*.json")
        # Extract dates from filenames
        dates = []
        for file in files:
            filename = file.name
            if filename.startswith("attendance_") and filename.endswith(".json"):
                date_str = filename[11:-5]  # Remove "attendance_" and ".json"
                dates.append(date_str)
        return sorted(dates, reverse=True)
    
    async def get_activities_in_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get activities in date range"""
        activities = []
        dates = await self.list_activity_files()
        
        for date in dates:
            if start_date <= date <= end_date:
                activity = await self.get_activity_by_date(date)
                if activity:
                    activities.append(activity)
        
        return activities

class LogsRepository(FileSystemRepository):
    """Repository for log file operations"""
    
    def __init__(self, project_path: Path):
        super().__init__(project_path)
        self.logs_dir = self.base_path / "logs"
        
    async def list_log_files(self) -> List[Dict[str, Any]]:
        """List all log files with metadata"""
        files = self.list_files(self.logs_dir, "*.log")
        log_files = []
        
        for file in files:
            try:
                stat = file.stat()
                log_files.append({
                    "filename": file.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "path": str(file)
                })
            except Exception as e:
                logger.error(f"Error getting file stats for {file}: {e}")
        
        return log_files
    
    async def read_log_file(self, filename: str, lines: Optional[int] = None) -> Optional[str]:
        """Read log file content"""
        log_file = self.logs_dir / filename
        
        if not log_file.exists():
            return None
            
        try:
            if lines is None:
                return await self.read_text_file(log_file)
            else:
                # Read last N lines
                async with aiofiles.open(log_file, 'r') as f:
                    content = await f.read()
                    lines_list = content.split('\n')
                    return '\n'.join(lines_list[-lines:]) if lines_list else ""
        except Exception as e:
            logger.error(f"Error reading log file {filename}: {e}")
            return None
    
    async def tail_log_file(self, filename: str, lines: int = 50) -> Optional[str]:
        """Get last N lines from log file"""
        return await self.read_log_file(filename, lines)

# Factory functions for dependency injection
def create_state_repository(project_path: Path) -> StateRepository:
    """Create StateRepository instance"""
    return StateRepository(project_path)

def create_activities_repository(project_path: Path) -> ActivitiesRepository:
    """Create ActivitiesRepository instance"""
    return ActivitiesRepository(project_path)

def create_logs_repository(project_path: Path) -> LogsRepository:
    """Create LogsRepository instance"""
    return LogsRepository(project_path)
