"""
Resource utilities for PyInstaller executable compatibility.

This module provides functions to handle file paths and resources correctly
both in development environment and when packaged as executable.
"""

import os
import sys
from pathlib import Path
from typing import Union, Optional

from src.utils.logger import logger


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for both development and PyInstaller.
    
    Args:
        relative_path: Path relative to the application root
        
    Returns:
        Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        logger.debug(f"Running as PyInstaller executable, base path: {base_path}")
        return os.path.join(base_path, relative_path)
    except AttributeError:
        # Development environment
        base_path = get_application_root()
        logger.debug(f"Running in development, base path: {base_path}")
        return os.path.join(base_path, relative_path)


def get_application_root() -> str:
    """
    Get the application root directory.
    
    Returns:
        Application root directory path
    """
    if is_frozen():
        # When frozen (executable), use the directory containing the executable
        return os.path.dirname(sys.executable)
    else:
        # Development environment - get project root (where main.py is)
        main_py_path = Path(__file__).parent.parent.parent / 'main.py'
        if main_py_path.exists():
            return str(main_py_path.parent)
        else:
            # Fallback to current working directory
            return os.getcwd()


def get_user_data_path() -> str:
    """
    Get path for user data (downloads, logs, etc.) that persists outside executable.
    
    For executables, this should be in user's documents or app data folder.
    For development, this is the project directory.
    
    Returns:
        User data directory path
    """
    if is_frozen():
        # Executable - use user's documents folder
        if sys.platform == 'win32':
            # Windows: %USERPROFILE%/Documents/BGDSS
            documents_path = os.path.join(os.path.expanduser('~'), 'Documents', 'BGDSS')
        else:
            # macOS/Linux: ~/BGDSS
            documents_path = os.path.join(os.path.expanduser('~'), 'BGDSS')
        
        # Create directory if it doesn't exist
        os.makedirs(documents_path, exist_ok=True)
        logger.info(f"Using user data path (executable): {documents_path}")
        return documents_path
    else:
        # Development - use project directory
        app_root = get_application_root()
        logger.debug(f"Using user data path (development): {app_root}")
        return app_root


def is_frozen() -> bool:
    """
    Check if the application is running as a frozen executable (PyInstaller).
    
    Returns:
        True if running as executable, False if in development
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_bundled_driver_path(driver_name: str) -> Optional[str]:
    """
    Get path to bundled driver (like chromedriver) in executable.
    
    Args:
        driver_name: Name of the driver executable (e.g., 'chromedriver.exe')
        
    Returns:
        Path to bundled driver if found, None otherwise
    """
    if is_frozen():
        # Look for driver in the executable's temp directory
        try:
            driver_path = os.path.join(sys._MEIPASS, driver_name)
            if os.path.exists(driver_path):
                logger.info(f"Found bundled driver: {driver_path}")
                return driver_path
        except AttributeError:
            pass
    
    # Look in the application root
    app_root = get_application_root()
    driver_path = os.path.join(app_root, driver_name)
    if os.path.exists(driver_path):
        logger.info(f"Found driver in app root: {driver_path}")
        return driver_path
    
    # Look in drivers subdirectory
    drivers_dir = os.path.join(app_root, 'drivers')
    driver_path = os.path.join(drivers_dir, driver_name)
    if os.path.exists(driver_path):
        logger.info(f"Found driver in drivers directory: {driver_path}")
        return driver_path
    
    logger.warning(f"Bundled driver not found: {driver_name}")
    return None


def ensure_directory_exists(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure exists
        
    Returns:
        Path object for the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path_obj}")
    return path_obj


def get_config_path(config_filename: str) -> str:
    """
    Get path to configuration file.
    
    Args:
        config_filename: Name of the configuration file
        
    Returns:
        Absolute path to configuration file
    """
    if is_frozen():
        # In executable, config files should be bundled
        try:
            config_path = os.path.join(sys._MEIPASS, 'config', config_filename)
            if os.path.exists(config_path):
                return config_path
        except AttributeError:
            pass
    
    # Development or fallback - look in project config directory
    app_root = get_application_root()
    config_path = os.path.join(app_root, 'config', config_filename)
    
    if os.path.exists(config_path):
        return config_path
    else:
        logger.warning(f"Configuration file not found: {config_filename}")
        return config_path  # Return path anyway, calling code can handle missing file


def get_env_file_path() -> str:
    """
    Get path to .env file.
    
    For executables, .env should be in the same directory as the executable.
    For development, it's in the project root.
    
    Returns:
        Path to .env file
    """
    if is_frozen():
        # Executable - look next to the executable file
        exe_dir = os.path.dirname(sys.executable)
        env_path = os.path.join(exe_dir, '.env')
    else:
        # Development - project root
        app_root = get_application_root()
        env_path = os.path.join(app_root, '.env')
    
    logger.debug(f"Environment file path: {env_path}")
    return env_path


def get_relative_to_exe(relative_path: str) -> str:
    """
    Get path relative to executable location (useful for .env, config files).
    
    Args:
        relative_path: Path relative to executable
        
    Returns:
        Absolute path
    """
    if is_frozen():
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, relative_path)
    else:
        app_root = get_application_root()
        return os.path.join(app_root, relative_path)