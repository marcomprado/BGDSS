"""
Logging module for Web Scraper AI application.
Implements singleton pattern with colored console output and file rotation.
"""

import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
import threading
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[91m'  # Bright Red
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # Create a copy of the record to avoid affecting other handlers
        record_copy = logging.LogRecord(
            record.name,
            record.levelno,
            record.pathname,
            record.lineno,
            record.msg,
            record.args,
            record.exc_info,
            record.funcName
        )
        record_copy.created = record.created
        record_copy.msecs = record.msecs
        # Copy additional attributes that might exist
        for attr in ['stack_info', 'sinfo']:
            if hasattr(record, attr):
                setattr(record_copy, attr, getattr(record, attr))
        
        # Add context to message
        context = get_context()
        if context:
            record_copy.msg = f"{context} {record_copy.msg}"
        
        # Apply colors to the copy
        levelname = record_copy.levelname
        if levelname in self.COLORS:
            record_copy.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        if levelname in ['ERROR', 'CRITICAL']:
            # Add red color to the message itself for errors
            record_copy.msg = f"{self.COLORS['ERROR']}{record_copy.msg}{self.RESET}"
            
        return super().format(record_copy)


class Logger:
    """Singleton logger class for the application."""
    
    _instance: Optional['Logger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls) -> 'Logger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
            self.silent_mode = False
            self.original_console_level = logging.WARNING
    
    def _setup_logger(self) -> None:
        """Initialize the logger with console and file handlers."""
        self._logger = logging.getLogger('WebScraperAI')
        self._logger.setLevel(logging.DEBUG)
        
        if self._logger.handlers:
            return
        
        self.logs_dir = Path(__file__).parent.parent.parent / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        
        # Console handler - only for critical info during scraping
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Reduced verbosity for terminal
        console_formatter = ColoredFormatter(
            '%(levelname)s: %(message)s'  # Simplified format
        )
        console_handler.setFormatter(console_formatter)
        
        # Main log file - comprehensive logging
        log_filename = self.logs_dir / f'web_scraper_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=10 * 1024 * 1024,  
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)
        self.session_id = None
        
        # Store console handler reference for silent mode control
        self.console_handler = console_handler
    
    def set_level(self, level: str) -> None:
        """Set the logging level."""
        level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_mapping:
            self._logger.setLevel(level_mapping[level.upper()])
            for handler in self._logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                    handler.setLevel(level_mapping[level.upper()])
    
    def enable_silent_mode(self) -> None:
        """Enable silent mode - no console output during processing."""
        if hasattr(self, 'console_handler'):
            self.original_console_level = self.console_handler.level
            self.console_handler.setLevel(logging.CRITICAL)  # Only critical errors to console
            self.silent_mode = True
    
    def disable_silent_mode(self) -> None:
        """Disable silent mode - restore normal console output."""
        if hasattr(self, 'console_handler'):
            self.console_handler.setLevel(self.original_console_level)
            self.silent_mode = False
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message."""
        self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message."""
        self._logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message."""
        self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message."""
        self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message."""
        self._logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with traceback."""
        self._logger.exception(message, *args, **kwargs)
    
    def start_session(self, session_type: str = "scraping") -> str:
        """Start a new logging session with dedicated files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"{session_type}_{timestamp}"
        
        # Create session-specific log file
        session_filename = self.logs_dir / f'{self.session_id}.log'
        session_handler = RotatingFileHandler(
            session_filename,
            maxBytes=50 * 1024 * 1024,  # 50MB per session
            backupCount=3,
            encoding='utf-8'
        )
        session_handler.setLevel(logging.DEBUG)
        session_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        session_handler.setFormatter(session_formatter)
        
        # Add session handler
        self._logger.addHandler(session_handler)
        
        # Create error-only file for this session
        error_filename = self.logs_dir / f'{self.session_id}_errors.log'
        error_handler = RotatingFileHandler(
            error_filename,
            maxBytes=10 * 1024 * 1024,
            backupCount=2,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(session_formatter)
        self._logger.addHandler(error_handler)
        
        self.info(f"=== SESSÃO INICIADA: {self.session_id} ===")
        return self.session_id
    
    def end_session(self) -> None:
        """End current logging session and remove session handlers."""
        if self.session_id:
            self.info(f"=== SESSÃO FINALIZADA: {self.session_id} ===")
            
            # Remove session-specific handlers
            handlers_to_remove = []
            for handler in self._logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    if self.session_id in str(handler.baseFilename):
                        handlers_to_remove.append(handler)
            
            for handler in handlers_to_remove:
                handler.close()
                self._logger.removeHandler(handler)
            
            self.session_id = None
    
    def progress_info(self, message: str, *args, **kwargs) -> None:
        """Log progress information - only to file, not console."""
        # Create a temporary handler that only writes to file
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(logging.CRITICAL)  # Temporarily disable console
        
        self._logger.info(message, *args, **kwargs)
        
        # Restore console handler level
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(logging.WARNING)
    
    def download_progress(self, filename: str, current: int, total: int, speed: str = "") -> None:
        """Log download progress details."""
        percentage = (current / total * 100) if total > 0 else 0
        self.progress_info(f"Download: {filename} - {current}/{total} ({percentage:.1f}%) {speed}")


# Global logger instance
logger = Logger()

# Thread-local storage for context
_local = threading.local()

def set_context(site: str = None, year: str = None, month: str = None):
    """Set logging context for current thread."""
    _local.site = site
    _local.year = year  
    _local.month = month

def get_context() -> str:
    """Get current logging context."""
    parts = []
    if hasattr(_local, 'site') and _local.site:
        parts.append(f"Site:{_local.site}")
    if hasattr(_local, 'year') and _local.year:
        parts.append(f"Ano:{_local.year}")
    if hasattr(_local, 'month') and _local.month:
        parts.append(f"Mes:{_local.month}")
    return f"[{' '.join(parts)}]" if parts else ""