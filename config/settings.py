"""
Application settings and configuration management.
Loads environment variables and provides centralized configuration access.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dotenv import load_dotenv

from src.utils.exceptions import ConfigurationError
from src.utils.logger import logger


class Settings:
    """Singleton class for managing application settings."""
    
    _instance: Optional['Settings'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'Settings':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._load_environment()
            self._initialize_settings()
            self._validate_settings()
            self._initialized = True
    
    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
        else:
            logger.warning("No .env file found, using system environment variables")
    
    def _initialize_settings(self) -> None:
        """Initialize all settings with defaults."""
        # AI Provider Configuration
        self.OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
        self.AI_PROVIDER: str = os.getenv('AI_PROVIDER', 'openai')  # openai, openrouter
        self.AI_BASE_URL: Optional[str] = os.getenv('AI_BASE_URL')  # Custom base URL for AI provider
        self.AI_PROVIDER_CONFIG: Optional[str] = os.getenv('AI_PROVIDER_CONFIG')  # JSON string with provider-specific config
        self.AI_PROVIDER_PREFERENCE: str = os.getenv('AI_PROVIDER_PREFERENCE', '')  # Specific provider preference for OpenRouter
        
        # AI Model Configuration (no defaults - must be set in .env)
        self.OPENAI_MODEL: Optional[str] = os.getenv('OPENAI_MODEL')
        self.OPENAI_MAX_TOKENS: int = int(os.getenv('OPENAI_MAX_TOKENS', '25000'))
        self.OPENAI_TEMPERATURE: float = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        
        self.WEBDRIVER_PATH: str = os.getenv('WEBDRIVER_PATH', 'auto')
        
        self.DOWNLOAD_TIMEOUT: int = int(os.getenv('DOWNLOAD_TIMEOUT', '30'))
        
        self.LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
        
        self.BASE_DIR: Path = Path(__file__).parent.parent
        self.DOWNLOADS_DIR: Path = self.BASE_DIR / 'downloads'
        self.RAW_DOWNLOADS_DIR: Path = self.DOWNLOADS_DIR / 'raw'
        self.PROCESSED_DOWNLOADS_DIR: Path = self.DOWNLOADS_DIR / 'processed'
        self.TEMP_DIR: Path = self.DOWNLOADS_DIR / 'temp'
        self.LOGS_DIR: Path = self.BASE_DIR / 'logs'
        self.DRIVERS_DIR: Path = self.BASE_DIR / 'drivers'
        
        self.DEFAULT_WAIT_TIME: int = int(os.getenv('DEFAULT_WAIT_TIME', '10'))
        self.MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
        self.RETRY_DELAY: int = int(os.getenv('RETRY_DELAY', '5'))
        
        self.CHROME_OPTIONS: list = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ]
        
        self.FILE_UPLOAD_MAX_SIZE: int = int(os.getenv('FILE_UPLOAD_MAX_SIZE', '10485760'))  
        self.SUPPORTED_FILE_TYPES: list = ['.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx']
        
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.DOWNLOADS_DIR,
            self.RAW_DOWNLOADS_DIR,
            self.PROCESSED_DOWNLOADS_DIR,
            self.TEMP_DIR,
            self.LOGS_DIR,
            self.DRIVERS_DIR
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def _validate_settings(self) -> None:
        """Validate required settings."""
        # OpenAI API key is optional - only warn if not present
        if not self.OPENAI_API_KEY:
            logger.warning(
                "OpenAI API key not found - AI features will be disabled. "
                "Set OPENAI_API_KEY in .env file to enable AI functionality."
            )
        
        logger.set_level(self.LOG_LEVEL)
        
        logger.info("Settings validated successfully")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        return getattr(self, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        setattr(self, key, value)
        logger.debug(f"Setting updated: {key} = {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Export settings as dictionary (excluding sensitive data)."""
        settings_dict = {}
        for key in dir(self):
            if key.startswith('_') or callable(getattr(self, key)):
                continue
            
            value = getattr(self, key)
            
            if key == 'OPENAI_API_KEY' and value:
                settings_dict[key] = f"***{value[-4:]}"
            elif isinstance(value, Path):
                settings_dict[key] = str(value)
            else:
                settings_dict[key] = value
        
        return settings_dict
    
    def reload(self) -> None:
        """Reload settings from environment."""
        self._initialized = False
        self.__init__()
        logger.info("Settings reloaded")


settings = Settings()