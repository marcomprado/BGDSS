"""
Scraping task data models using dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""
    
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


class TaskPriority(Enum):
    """Enumeration of task priorities."""
    
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskMetrics:
    """Metrics for tracking task performance."""
    
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    pages_scraped: int = 0
    items_extracted: int = 0
    files_downloaded: int = 0
    errors_encountered: int = 0
    retries_attempted: int = 0
    bandwidth_used_mb: float = 0.0
    
    def calculate_duration(self) -> None:
        """Calculate duration from start and end times."""
        if self.start_time and self.end_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'pages_scraped': self.pages_scraped,
            'items_extracted': self.items_extracted,
            'files_downloaded': self.files_downloaded,
            'errors_encountered': self.errors_encountered,
            'retries_attempted': self.retries_attempted,
            'bandwidth_used_mb': self.bandwidth_used_mb
        }


@dataclass
class TaskError:
    """Error information for failed tasks."""
    
    error_type: str
    error_message: str
    error_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    recoverable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'error_type': self.error_type,
            'error_message': self.error_message,
            'error_trace': self.error_trace,
            'timestamp': self.timestamp.isoformat(),
            'recoverable': self.recoverable
        }


@dataclass
class ScrapingTask:
    """Complete representation of a scraping task."""
    
    task_id: str = field(default_factory=lambda: str(uuid4()))
    
    site_config_name: str = ""
    target_url: str = ""
    
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    
    created_by: str = "system"
    assigned_to: Optional[str] = None
    
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    extracted_data: List[Dict[str, Any]] = field(default_factory=list)
    
    output_format: str = "json"  
    output_path: Optional[Path] = None
    
    metrics: TaskMetrics = field(default_factory=TaskMetrics)
    
    errors: List[TaskError] = field(default_factory=list)
    
    parent_task_id: Optional[str] = None
    child_task_ids: List[str] = field(default_factory=list)
    
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    max_retries: int = 3
    current_retry: int = 0
    
    callback_url: Optional[str] = None
    
    def start(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.metrics.start_time = datetime.now()
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.metrics.end_time = datetime.now()
        self.metrics.calculate_duration()
        self.updated_at = datetime.now()
    
    def fail(self, error: TaskError) -> None:
        """Mark task as failed with error information."""
        self.status = TaskStatus.FAILED
        self.errors.append(error)
        self.metrics.end_time = datetime.now()
        self.metrics.calculate_duration()
        self.metrics.errors_encountered += 1
        self.updated_at = datetime.now()
    
    def retry(self) -> bool:
        """Attempt to retry the task."""
        if self.current_retry < self.max_retries:
            self.current_retry += 1
            self.status = TaskStatus.RETRY
            self.metrics.retries_attempted += 1
            self.updated_at = datetime.now()
            return True
        return False
    
    def cancel(self) -> None:
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
        self.metrics.end_time = datetime.now()
        self.metrics.calculate_duration()
        self.updated_at = datetime.now()
    
    def add_extracted_item(self, item: Dict[str, Any]) -> None:
        """Add an extracted data item."""
        self.extracted_data.append(item)
        self.metrics.items_extracted += 1
        self.updated_at = datetime.now()
    
    def add_child_task(self, child_task_id: str) -> None:
        """Add a child task ID."""
        self.child_task_ids.append(child_task_id)
        self.updated_at = datetime.now()
    
    def is_retriable(self) -> bool:
        """Check if task can be retried."""
        if self.status not in [TaskStatus.FAILED, TaskStatus.RETRY]:
            return False
        
        if self.current_retry >= self.max_retries:
            return False
        
        if self.errors and not self.errors[-1].recoverable:
            return False
        
        return True
    
    def get_progress_percentage(self) -> float:
        """Calculate task progress percentage."""
        if self.status == TaskStatus.COMPLETED:
            return 100.0
        elif self.status == TaskStatus.PENDING:
            return 0.0
        elif self.status in [TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return -1.0
        else:
            return 50.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'task_id': self.task_id,
            'site_config_name': self.site_config_name,
            'target_url': self.target_url,
            'status': self.status.value,
            'priority': self.priority.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'created_by': self.created_by,
            'assigned_to': self.assigned_to,
            'parameters': self.parameters,
            'extracted_data': self.extracted_data,
            'output_format': self.output_format,
            'output_path': str(self.output_path) if self.output_path else None,
            'metrics': self.metrics.to_dict(),
            'errors': [error.to_dict() for error in self.errors],
            'parent_task_id': self.parent_task_id,
            'child_task_ids': self.child_task_ids,
            'tags': self.tags,
            'metadata': self.metadata,
            'max_retries': self.max_retries,
            'current_retry': self.current_retry,
            'callback_url': self.callback_url,
            'progress_percentage': self.get_progress_percentage()
        }