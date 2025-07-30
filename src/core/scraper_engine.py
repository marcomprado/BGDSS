"""
Scraper engine for orchestrating scraping processes with threading and monitoring.
"""

import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

from src.models.scraping_task import ScrapingTask, TaskStatus, TaskPriority
from src.models.site_config import SiteConfig
from src.modules.site_factory import factory as site_factory
from src.core.file_manager import FileManager
from src.utils.logger import logger
from src.utils.exceptions import ScrapingError


class EngineStatus(Enum):
    """Engine status enumeration."""
    
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class EngineMetrics:
    """Engine performance metrics."""
    
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_queued: int = 0
    tasks_in_progress: int = 0
    total_processing_time: float = 0.0
    average_task_time: float = 0.0
    success_rate: float = 0.0
    start_time: Optional[datetime] = None
    
    def calculate_success_rate(self) -> None:
        """Calculate success rate."""
        total_completed = self.tasks_completed + self.tasks_failed
        if total_completed > 0:
            self.success_rate = self.tasks_completed / total_completed
    
    def calculate_average_time(self) -> None:
        """Calculate average task processing time."""
        if self.tasks_completed > 0:
            self.average_task_time = self.total_processing_time / self.tasks_completed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'tasks_queued': self.tasks_queued,
            'tasks_in_progress': self.tasks_in_progress,
            'total_processing_time': self.total_processing_time,
            'average_task_time': self.average_task_time,
            'success_rate': self.success_rate,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }


@dataclass
class WorkerInfo:
    """Information about a worker thread."""
    
    worker_id: str
    thread: threading.Thread
    current_task: Optional[ScrapingTask] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'worker_id': self.worker_id,
            'current_task_id': self.current_task.task_id if self.current_task else None,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'is_alive': self.thread.is_alive()
        }


class ScraperEngine:
    """Main scraping engine with threading and orchestration."""
    
    def __init__(self, 
                 max_workers: int = 3,
                 max_queue_size: int = 100,
                 task_timeout: int = 3600):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.task_timeout = task_timeout
        
        self.status = EngineStatus.IDLE
        self.metrics = EngineMetrics()
        
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_queue_size)
        self.completed_tasks: Dict[str, ScrapingTask] = {}
        self.active_tasks: Dict[str, ScrapingTask] = {}
        
        self.workers: Dict[str, WorkerInfo] = {}
        self.executor: Optional[ThreadPoolExecutor] = None
        
        self.file_manager = FileManager()
        
        self._shutdown_event = threading.Event()
        self._pause_event = threading.Event()
        
        self.progress_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        
        logger.info(f"ScraperEngine initialized (max_workers: {max_workers})")
    
    def start(self) -> None:
        """Start the scraping engine."""
        if self.status == EngineStatus.RUNNING:
            logger.warning("Engine is already running")
            return
        
        try:
            self.status = EngineStatus.RUNNING
            self.metrics.start_time = datetime.now()
            
            self.executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="ScraperWorker"
            )
            
            self._start_monitoring_thread()
            
            logger.info("ScraperEngine started successfully")
            
        except Exception as e:
            self.status = EngineStatus.ERROR
            logger.error(f"Failed to start engine: {e}")
            raise ScrapingError(f"Engine startup failed: {e}")
    
    def stop(self, timeout: int = 30) -> None:
        """Stop the scraping engine gracefully."""
        if self.status not in [EngineStatus.RUNNING, EngineStatus.PAUSED]:
            return
        
        logger.info("Stopping scraping engine...")
        self.status = EngineStatus.STOPPING
        
        self._shutdown_event.set()
        
        if self.executor:
            self.executor.shutdown(wait=True, timeout=timeout)
        
        for worker_info in self.workers.values():
            if worker_info.thread.is_alive():
                worker_info.thread.join(timeout=5)
        
        self.status = EngineStatus.IDLE
        logger.info("ScraperEngine stopped")
    
    def pause(self) -> None:
        """Pause the engine."""
        if self.status == EngineStatus.RUNNING:
            self.status = EngineStatus.PAUSED
            self._pause_event.set()
            logger.info("Engine paused")
    
    def resume(self) -> None:
        """Resume the engine."""
        if self.status == EngineStatus.PAUSED:
            self.status = EngineStatus.RUNNING
            self._pause_event.clear()
            logger.info("Engine resumed")
    
    def submit_task(self, task: ScrapingTask) -> bool:
        """Submit a task to the queue."""
        if self.status not in [EngineStatus.RUNNING, EngineStatus.PAUSED]:
            logger.error("Cannot submit task - engine not running")
            return False
        
        try:
            priority = -task.priority.value  
            
            self.task_queue.put((priority, task.created_at, task), timeout=5)
            self.metrics.tasks_queued += 1
            
            logger.info(f"Task submitted: {task.task_id}")
            return True
            
        except queue.Full:
            logger.error("Task queue is full")
            return False
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            return False
    
    def submit_bulk_tasks(self, tasks: List[ScrapingTask]) -> Dict[str, bool]:
        """Submit multiple tasks in bulk."""
        results = {}
        
        for task in tasks:
            results[task.task_id] = self.submit_task(task)
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Bulk submission: {successful}/{len(tasks)} tasks queued")
        
        return results
    
    def create_and_submit_task(self,
                              site_config: SiteConfig,
                              target_url: Optional[str] = None,
                              priority: TaskPriority = TaskPriority.NORMAL,
                              parameters: Optional[Dict[str, Any]] = None) -> ScrapingTask:
        """Create and submit a new scraping task."""
        task = ScrapingTask(
            site_config_name=site_config.name,
            target_url=target_url or site_config.base_url,
            priority=priority,
            parameters=parameters or {}
        )
        
        if self.submit_task(task):
            return task
        else:
            raise ScrapingError("Failed to submit task to queue")
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a specific task."""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].status
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id].status
        else:
            return None
    
    def get_task(self, task_id: str) -> Optional[ScrapingTask]:
        """Get a task by ID."""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        elif task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        else:
            return None
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task if possible."""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.cancel()
            logger.info(f"Task cancelled: {task_id}")
            return True
        
        return False
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.task_queue.qsize()
    
    def get_metrics(self) -> EngineMetrics:
        """Get current engine metrics."""
        self.metrics.tasks_queued = self.get_queue_size()
        self.metrics.tasks_in_progress = len(self.active_tasks)
        self.metrics.calculate_success_rate()
        self.metrics.calculate_average_time()
        
        return self.metrics
    
    def get_worker_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all workers."""
        return {worker_id: worker.to_dict() for worker_id, worker in self.workers.items()}
    
    def _start_monitoring_thread(self) -> None:
        """Start monitoring thread for task processing."""
        monitor_thread = threading.Thread(
            target=self._monitor_and_process_tasks,
            name="EngineMonitor",
            daemon=True
        )
        monitor_thread.start()
    
    def _monitor_and_process_tasks(self) -> None:
        """Monitor and process tasks from the queue."""
        logger.info("Task monitoring started")
        
        while not self._shutdown_event.is_set():
            try:
                if self.status == EngineStatus.PAUSED:
                    self._pause_event.wait(timeout=1)
                    continue
                
                if self.status != EngineStatus.RUNNING:
                    break
                
                try:
                    priority, created_at, task = self.task_queue.get(timeout=1)
                    
                    if task.status == TaskStatus.CANCELLED:
                        self.task_queue.task_done()
                        continue
                    
                    future = self.executor.submit(self._process_task, task)
                    
                    self.task_queue.task_done()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error in task monitoring: {e}")
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Critical error in task monitor: {e}")
                time.sleep(5)
        
        logger.info("Task monitoring stopped")
    
    def _process_task(self, task: ScrapingTask) -> ScrapingTask:
        """Process a single task."""
        worker_id = threading.current_thread().name
        start_time = time.time()
        
        try:
            logger.info(f"Processing task {task.task_id} on worker {worker_id}")
            
            self.active_tasks[task.task_id] = task
            
            self._update_worker_info(worker_id, task)
            
            site_config = self._get_site_config(task.site_config_name)
            if not site_config:
                raise ScrapingError(f"Site config not found: {task.site_config_name}")
            
            module = site_factory.create_module(site_config)
            
            processed_task = module.execute_scraping_task(task)
            
            if processed_task.status == TaskStatus.COMPLETED:
                self._handle_successful_task(processed_task)
            elif processed_task.status == TaskStatus.FAILED and processed_task.is_retriable():
                logger.info(f"Retrying task: {task.task_id}")
                self.submit_task(processed_task)
            else:
                self._handle_failed_task(processed_task)
            
            processing_time = time.time() - start_time
            self.metrics.total_processing_time += processing_time
            
            return processed_task
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            
            from src.models.scraping_task import TaskError
            error = TaskError(
                error_type=type(e).__name__,
                error_message=str(e),
                recoverable=False
            )
            task.fail(error)
            
            self._handle_failed_task(task)
            return task
            
        finally:
            self.active_tasks.pop(task.task_id, None)
            self._update_worker_activity(worker_id)
    
    def _get_site_config(self, config_name: str) -> Optional[SiteConfig]:
        """Get site configuration by name."""
        # This would typically load from a configuration store
        # For now, return None to indicate configuration loading needed
        logger.warning(f"Site config loading not implemented for: {config_name}")
        return None
    
    def _handle_successful_task(self, task: ScrapingTask) -> None:
        """Handle a successfully completed task."""
        self.completed_tasks[task.task_id] = task
        self.metrics.tasks_completed += 1
        
        if task.extracted_data:
            self.file_manager.organize_downloads(task.task_id)
        
        for callback in self.completion_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Completion callback failed: {e}")
        
        logger.info(f"Task completed successfully: {task.task_id}")
    
    def _handle_failed_task(self, task: ScrapingTask) -> None:
        """Handle a failed task."""
        self.completed_tasks[task.task_id] = task
        self.metrics.tasks_failed += 1
        
        logger.error(f"Task failed: {task.task_id} - {task.errors[-1].error_message if task.errors else 'Unknown error'}")
    
    def _update_worker_info(self, worker_id: str, task: ScrapingTask) -> None:
        """Update worker information."""
        if worker_id not in self.workers:
            self.workers[worker_id] = WorkerInfo(
                worker_id=worker_id,
                thread=threading.current_thread()
            )
        
        worker = self.workers[worker_id]
        worker.current_task = task
        worker.last_activity = datetime.now()
    
    def _update_worker_activity(self, worker_id: str) -> None:
        """Update worker activity timestamp."""
        if worker_id in self.workers:
            worker = self.workers[worker_id]
            worker.current_task = None
            worker.last_activity = datetime.now()
            
            if hasattr(worker, 'tasks_completed'):
                worker.tasks_completed += 1
    
    def add_progress_callback(self, callback: Callable) -> None:
        """Add a progress callback function."""
        self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable) -> None:
        """Add a completion callback function."""
        self.completion_callbacks.append(callback)
    
    def get_active_tasks(self) -> Dict[str, ScrapingTask]:
        """Get all currently active tasks."""
        return self.active_tasks.copy()
    
    def get_completed_tasks(self) -> Dict[str, ScrapingTask]:
        """Get all completed tasks."""
        return self.completed_tasks.copy()
    
    def clear_completed_tasks(self) -> int:
        """Clear completed tasks from memory."""
        count = len(self.completed_tasks)
        self.completed_tasks.clear()
        logger.info(f"Cleared {count} completed tasks from memory")
        return count
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive engine status."""
        return {
            'status': self.status.value,
            'metrics': self.get_metrics().to_dict(),
            'workers': self.get_worker_info(),
            'queue_size': self.get_queue_size(),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks)
        }
    
    def export_task_history(self, 
                           include_data: bool = False,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Export task history for analysis."""
        history = []
        
        for task in self.completed_tasks.values():
            if start_date and task.created_at < start_date:
                continue
            if end_date and task.created_at > end_date:
                continue
            
            task_data = task.to_dict()
            
            if not include_data:
                task_data.pop('extracted_data', None)
            
            history.append(task_data)
        
        return history
    
    def cleanup_old_tasks(self, days_old: int = 7) -> int:
        """Remove old completed tasks from memory."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        tasks_to_remove = []
        for task_id, task in self.completed_tasks.items():
            if task.updated_at < cutoff_date:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.completed_tasks[task_id]
        
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
        return len(tasks_to_remove)