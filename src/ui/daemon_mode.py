"""
Daemon mode interface for Web Scraper AI.
"""

import time
import signal
import sys
from typing import Optional

from src.core.application import WebScraperApplication
from src.utils.logger import logger


class DaemonMode:
    """Daemon mode runner."""
    
    def __init__(self, app: WebScraperApplication):
        self.app = app
        self.running = True
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down daemon...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Handle SIGUSR1 for status reporting (Unix only)
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, self._status_signal_handler)
    
    def _status_signal_handler(self, signum, frame):
        """Handle status signal (SIGUSR1)."""
        try:
            status = self.app.get_application_status()
            logger.info(f"Daemon Status - Running: {status['running']}, "
                       f"Active Tasks: {status.get('engine_status', {}).get('active_tasks', 0)}")
        except Exception as e:
            logger.error(f"Failed to get daemon status: {e}")
    
    def run(self) -> int:
        """Run daemon mode."""
        try:
            self._show_daemon_info()
            
            logger.info("Daemon mode started - running continuously...")
            
            # Main daemon loop
            while self.running:
                try:
                    # Perform periodic tasks
                    self._periodic_maintenance()
                    
                    # Sleep for a short interval
                    time.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Error in daemon loop: {e}")
                    time.sleep(30)  # Wait longer on error
            
            logger.info("Daemon mode shutting down...")
            return 0
            
        except KeyboardInterrupt:
            logger.info("Daemon interrupted by user")
            return 130
        except Exception as e:
            logger.error(f"Daemon mode error: {e}")
            return 1
    
    def _show_daemon_info(self) -> None:
        """Show daemon startup information."""
        print("🔄 Web Scraper AI - Daemon Mode")
        print("=" * 40)
        print("Running in background mode...")
        print("Send SIGTERM or SIGINT to stop gracefully")
        if hasattr(signal, 'SIGUSR1'):
            print("Send SIGUSR1 for status information")
        print("Check logs for detailed information")
        print("=" * 40)
    
    def _periodic_maintenance(self) -> None:
        """Perform periodic maintenance tasks."""
        try:
            # Log current status every 5 minutes (30 cycles of 10 seconds)
            if not hasattr(self, '_status_counter'):
                self._status_counter = 0
            
            self._status_counter += 1
            
            if self._status_counter >= 30:  # 5 minutes
                self._log_status()
                self._status_counter = 0
            
            # Perform cleanup every hour (360 cycles of 10 seconds)
            if not hasattr(self, '_cleanup_counter'):
                self._cleanup_counter = 0
            
            self._cleanup_counter += 1
            
            if self._cleanup_counter >= 360:  # 1 hour
                self._perform_maintenance()
                self._cleanup_counter = 0
                
        except Exception as e:
            logger.error(f"Error in periodic maintenance: {e}")
    
    def _log_status(self) -> None:
        """Log current application status."""
        try:
            status = self.app.get_application_status()
            metrics = self.app.get_metrics()
            
            logger.info("=== Daemon Status Report ===")
            logger.info(f"Application Running: {status['running']}")
            logger.info(f"Site Configs Loaded: {status['site_configs_loaded']}")
            
            if status.get('engine_status'):
                engine = status['engine_status']
                logger.info(f"Engine Status: {engine['status']}")
                logger.info(f"Active Tasks: {engine['active_tasks']}")
                logger.info(f"Queue Size: {engine['queue_size']}")
                logger.info(f"Completed Tasks: {engine['completed_tasks']}")
            
            if 'engine' in metrics:
                engine_metrics = metrics['engine']
                logger.info(f"Success Rate: {engine_metrics.get('success_rate', 0):.2%}")
                logger.info(f"Average Task Time: {engine_metrics.get('average_task_time', 0):.2f}s")
            
            logger.info("=== End Status Report ===")
            
        except Exception as e:
            logger.error(f"Failed to log status: {e}")
    
    def _perform_maintenance(self) -> None:
        """Perform scheduled maintenance."""
        try:
            logger.info("Starting scheduled maintenance...")
            
            # Cleanup old data
            cleanup_results = self.app.cleanup_old_data()
            logger.info(f"Maintenance cleanup completed: {cleanup_results}")
            
            # Optional: Create backup (commented out to avoid too many backups)
            # backup_info = self.app.create_backup("Scheduled daemon backup")
            # logger.info(f"Scheduled backup created: {backup_info['backup_id']}")
            
            logger.info("Scheduled maintenance completed")
            
        except Exception as e:
            logger.error(f"Maintenance failed: {e}")
    
    def stop(self) -> None:
        """Stop the daemon."""
        logger.info("Stopping daemon mode...")
        self.running = False