"""
Site configuration data models using dataclasses.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class SelectorConfig:
    """Configuration for HTML element selectors."""
    
    type: str  
    value: str
    attribute: Optional[str] = None  
    index: Optional[int] = None  
    wait_condition: str = 'presence'  
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'type': self.type,
            'value': self.value,
            'attribute': self.attribute,
            'index': self.index,
            'wait_condition': self.wait_condition
        }


@dataclass
class AuthConfig:
    """Configuration for site authentication."""
    
    required: bool = False
    method: str = 'form'  
    username_selector: Optional[SelectorConfig] = None
    password_selector: Optional[SelectorConfig] = None
    submit_selector: Optional[SelectorConfig] = None
    credentials_env_prefix: Optional[str] = None  
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'required': self.required,
            'method': self.method,
            'username_selector': self.username_selector.to_dict() if self.username_selector else None,
            'password_selector': self.password_selector.to_dict() if self.password_selector else None,
            'submit_selector': self.submit_selector.to_dict() if self.submit_selector else None,
            'credentials_env_prefix': self.credentials_env_prefix
        }


@dataclass
class PaginationConfig:
    """Configuration for handling pagination."""
    
    enabled: bool = False
    next_button_selector: Optional[SelectorConfig] = None
    page_number_selector: Optional[SelectorConfig] = None
    max_pages: int = 10
    wait_between_pages: float = 2.0
    stop_on_no_results: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'enabled': self.enabled,
            'next_button_selector': self.next_button_selector.to_dict() if self.next_button_selector else None,
            'page_number_selector': self.page_number_selector.to_dict() if self.page_number_selector else None,
            'max_pages': self.max_pages,
            'wait_between_pages': self.wait_between_pages,
            'stop_on_no_results': self.stop_on_no_results
        }


@dataclass
class DataExtractionRule:
    """Rule for extracting specific data from a page."""
    
    name: str
    selector: SelectorConfig
    data_type: str = 'text'  
    post_process: Optional[str] = None  
    required: bool = True
    default_value: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'selector': self.selector.to_dict(),
            'data_type': self.data_type,
            'post_process': self.post_process,
            'required': self.required,
            'default_value': self.default_value
        }


@dataclass
class SiteConfig:
    """Complete configuration for a website scraping task."""
    
    name: str
    base_url: str
    description: Optional[str] = None
    
    selectors: Dict[str, SelectorConfig] = field(default_factory=dict)
    
    auth_config: AuthConfig = field(default_factory=lambda: AuthConfig())
    
    pagination_config: PaginationConfig = field(default_factory=lambda: PaginationConfig())
    
    extraction_rules: List[DataExtractionRule] = field(default_factory=list)
    
    wait_time: float = 5.0
    timeout: float = 30.0
    retry_attempts: int = 3
    
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    
    javascript_enabled: bool = True
    
    download_files: bool = False
    file_download_selector: Optional[SelectorConfig] = None
    
    custom_scripts: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_selector(self, name: str, selector: SelectorConfig) -> None:
        """Add a named selector to the configuration."""
        self.selectors[name] = selector
        self.updated_at = datetime.now()
    
    def add_extraction_rule(self, rule: DataExtractionRule) -> None:
        """Add a data extraction rule."""
        self.extraction_rules.append(rule)
        self.updated_at = datetime.now()
    
    def get_selector(self, name: str) -> Optional[SelectorConfig]:
        """Get a selector by name."""
        return self.selectors.get(name)
    
    def validate(self) -> List[str]:
        """Validate the configuration and return list of issues."""
        issues = []
        
        if not self.name:
            issues.append("Site name is required")
        
        if not self.base_url:
            issues.append("Base URL is required")
        
        if self.auth_config.required:
            if not self.auth_config.username_selector:
                issues.append("Username selector required for authentication")
            if not self.auth_config.password_selector:
                issues.append("Password selector required for authentication")
        
        if self.pagination_config.enabled and not self.pagination_config.next_button_selector:
            issues.append("Next button selector required for pagination")
        
        for rule in self.extraction_rules:
            if rule.required and rule.default_value is None:
                if not rule.selector:
                    issues.append(f"Selector required for extraction rule: {rule.name}")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'base_url': self.base_url,
            'description': self.description,
            'selectors': {k: v.to_dict() for k, v in self.selectors.items()},
            'auth_config': self.auth_config.to_dict(),
            'pagination_config': self.pagination_config.to_dict(),
            'extraction_rules': [rule.to_dict() for rule in self.extraction_rules],
            'wait_time': self.wait_time,
            'timeout': self.timeout,
            'retry_attempts': self.retry_attempts,
            'headers': self.headers,
            'cookies': self.cookies,
            'javascript_enabled': self.javascript_enabled,
            'download_files': self.download_files,
            'file_download_selector': self.file_download_selector.to_dict() if self.file_download_selector else None,
            'custom_scripts': self.custom_scripts,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }