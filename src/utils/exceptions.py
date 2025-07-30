"""
Custom exceptions for the Web Scraper AI application.
Following OOP principles with proper inheritance hierarchy.
"""

from typing import Optional, Dict, Any


class WebScraperBaseException(Exception):
    """Base exception class for all Web Scraper AI exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ScrapingError(WebScraperBaseException):
    """Exception raised for errors during web scraping operations."""
    
    def __init__(self, 
                 message: str, 
                 url: Optional[str] = None,
                 status_code: Optional[int] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.url = url
        self.status_code = status_code
        
        if details is None:
            details = {}
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code
            
        super().__init__(message, details)


class AIError(WebScraperBaseException):
    """Exception raised for errors related to AI/OpenAI operations."""
    
    def __init__(self,
                 message: str,
                 api_error: Optional[str] = None,
                 model: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.api_error = api_error
        self.model = model
        
        if details is None:
            details = {}
        if api_error:
            details['api_error'] = api_error
        if model:
            details['model'] = model
            
        super().__init__(message, details)


class FileProcessingError(WebScraperBaseException):
    """Exception raised for errors during file processing operations."""
    
    def __init__(self,
                 message: str,
                 file_path: Optional[str] = None,
                 file_type: Optional[str] = None,
                 operation: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.file_path = file_path
        self.file_type = file_type
        self.operation = operation
        
        if details is None:
            details = {}
        if file_path:
            details['file_path'] = file_path
        if file_type:
            details['file_type'] = file_type
        if operation:
            details['operation'] = operation
            
        super().__init__(message, details)


class ConfigurationError(WebScraperBaseException):
    """Exception raised for configuration-related errors."""
    
    def __init__(self,
                 message: str,
                 config_key: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.config_key = config_key
        
        if details is None:
            details = {}
        if config_key:
            details['config_key'] = config_key
            
        super().__init__(message, details)


class ValidationError(WebScraperBaseException):
    """Exception raised for validation errors."""
    
    def __init__(self,
                 message: str,
                 field: Optional[str] = None,
                 value: Optional[Any] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.field = field
        self.value = value
        
        if details is None:
            details = {}
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
            
        super().__init__(message, details)