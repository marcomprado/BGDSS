"""
Base abstract scraper class defining the interface for all scrapers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import time

from src.models.site_config import SiteConfig
from src.models.scraping_task import ScrapingTask
from src.models.download_result import DownloadResult
from src.utils.logger import logger
from src.utils.exceptions import ScrapingError


class BaseScraper(ABC):
    """Abstract base class for all web scrapers."""
    
    def __init__(self, config: Optional[SiteConfig] = None):
        self.config = config
        self.session_active = False
        self.current_url = None
        self.download_count = 0
        self.error_count = 0
        self.start_time = None
        
        logger.info(f"{self.__class__.__name__} initialized")
    
    @abstractmethod
    def initialize_driver(self) -> None:
        """Initialize the web driver/session."""
        pass
    
    @abstractmethod
    def navigate_to(self, url: str) -> bool:
        """Navigate to a specific URL."""
        pass
    
    @abstractmethod
    def get_page_source(self) -> str:
        """Get the current page HTML source."""
        pass
    
    @abstractmethod
    def find_element(self, selector: str, wait_time: Optional[float] = None) -> Any:
        """Find a single element on the page."""
        pass
    
    @abstractmethod
    def find_elements(self, selector: str, wait_time: Optional[float] = None) -> List[Any]:
        """Find multiple elements on the page."""
        pass
    
    @abstractmethod
    def click_element(self, selector: str) -> bool:
        """Click on an element."""
        pass
    
    @abstractmethod
    def fill_input(self, selector: str, value: str) -> bool:
        """Fill an input field with a value."""
        pass
    
    @abstractmethod
    def download_file(self, url: str, save_path: Path) -> DownloadResult:
        """Download a file from URL."""
        pass
    
    @abstractmethod
    def take_screenshot(self, save_path: Path) -> bool:
        """Take a screenshot of the current page."""
        pass
    
    @abstractmethod
    def execute_javascript(self, script: str) -> Any:
        """Execute JavaScript code on the page."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources and close the driver."""
        pass
    
    def start_session(self) -> None:
        """Start a new scraping session."""
        try:
            self.start_time = datetime.now()
            self.initialize_driver()
            self.session_active = True
            logger.info("Scraping session started")
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise ScrapingError(f"Failed to start session: {e}")
    
    def end_session(self) -> Dict[str, Any]:
        """End the scraping session and return statistics."""
        if not self.session_active:
            return {}
        
        try:
            self.cleanup()
            self.session_active = False
            
            duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            
            stats = {
                'duration_seconds': duration,
                'pages_visited': 1,  
                'downloads': self.download_count,
                'errors': self.error_count,
                'final_url': self.current_url
            }
            
            logger.info(f"Session ended. Stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return {'error': str(e)}
    
    def execute_task(self, task: ScrapingTask) -> ScrapingTask:
        """Execute a complete scraping task."""
        task.start()
        
        try:
            if not self.session_active:
                self.start_session()
            
            if not self.navigate_to(task.target_url):
                raise ScrapingError(f"Failed to navigate to {task.target_url}")
            
            if self.config and self.config.auth_config.required:
                self._handle_authentication()
            
            extracted_data = self._extract_data()
            for item in extracted_data:
                task.add_extracted_item(item)
            
            if self.config and self.config.download_files:
                self._download_files(task)
            
            if self.config and self.config.pagination_config.enabled:
                self._handle_pagination(task)
            
            task.complete()
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            from src.models.scraping_task import TaskError
            error = TaskError(
                error_type=type(e).__name__,
                error_message=str(e),
                recoverable=True
            )
            task.fail(error)
            
            if task.is_retriable():
                task.retry()
        
        return task
    
    def _handle_authentication(self) -> None:
        """Handle website authentication if required."""
        if not self.config or not self.config.auth_config.required:
            return
        
        auth = self.config.auth_config
        
        logger.info("Handling authentication")
        
        if auth.username_selector:
            username = self._get_credential('username')
            self.fill_input(auth.username_selector.value, username)
        
        if auth.password_selector:
            password = self._get_credential('password')
            self.fill_input(auth.password_selector.value, password)
        
        if auth.submit_selector:
            self.click_element(auth.submit_selector.value)
            time.sleep(3)  
        
        logger.info("Authentication completed")
    
    def _get_credential(self, credential_type: str) -> str:
        """Get credential from environment or config."""
        import os
        
        if self.config.auth_config.credentials_env_prefix:
            env_key = f"{self.config.auth_config.credentials_env_prefix}_{credential_type.upper()}"
            return os.getenv(env_key, '')
        
        return ''
    
    def _extract_data(self) -> List[Dict[str, Any]]:
        """Extract data based on extraction rules."""
        if not self.config or not self.config.extraction_rules:
            return []
        
        extracted_items = []
        
        for rule in self.config.extraction_rules:
            try:
                if rule.selector:
                    elements = self.find_elements(rule.selector.value)
                    
                    for element in elements:
                        value = self._extract_value_from_element(element, rule)
                        
                        if value or not rule.required:
                            extracted_items.append({
                                rule.name: value or rule.default_value
                            })
                        
            except Exception as e:
                logger.warning(f"Failed to extract {rule.name}: {e}")
                if rule.required and rule.default_value is None:
                    raise
        
        return extracted_items
    
    def _extract_value_from_element(self, element: Any, rule: Any) -> Any:
        """Extract value from element based on rule configuration."""
        return None
    
    def _download_files(self, task: ScrapingTask) -> None:
        """Download files found on the page."""
        if not self.config or not self.config.file_download_selector:
            return
        
        try:
            download_links = self.find_elements(self.config.file_download_selector.value)
            
            for link in download_links:
                try:
                    url = self._get_download_url(link)
                    if url:
                        filename = url.split('/')[-1] or f"download_{int(time.time())}"
                        save_path = settings.RAW_DOWNLOADS_DIR / filename
                        
                        result = self.download_file(url, save_path)
                        result.task_id = task.task_id
                        
                        self.download_count += 1
                        task.metrics.files_downloaded += 1
                        
                        logger.info(f"Downloaded: {filename}")
                        
                except Exception as e:
                    logger.error(f"Failed to download file: {e}")
                    self.error_count += 1
                    
        except Exception as e:
            logger.error(f"Error in file download process: {e}")
    
    def _get_download_url(self, element: Any) -> Optional[str]:
        """Extract download URL from element."""
        return None
    
    def _handle_pagination(self, task: ScrapingTask) -> None:
        """Handle pagination if enabled."""
        if not self.config or not self.config.pagination_config.enabled:
            return
        
        pagination = self.config.pagination_config
        current_page = 1
        
        while current_page < pagination.max_pages:
            try:
                if pagination.next_button_selector:
                    next_button = self.find_element(
                        pagination.next_button_selector.value,
                        wait_time=5
                    )
                    
                    if not next_button:
                        logger.info("No more pages found")
                        break
                    
                    self.click_element(pagination.next_button_selector.value)
                    time.sleep(pagination.wait_between_pages)
                    
                    current_page += 1
                    task.metrics.pages_scraped += 1
                    
                    new_data = self._extract_data()
                    
                    if not new_data and pagination.stop_on_no_results:
                        logger.info("No results on page, stopping pagination")
                        break
                    
                    for item in new_data:
                        task.add_extracted_item(item)
                else:
                    break
                    
            except Exception as e:
                logger.warning(f"Pagination error on page {current_page}: {e}")
                break
    
    def wait(self, seconds: float) -> None:
        """Wait for specified seconds."""
        time.sleep(seconds)
    
    def get_current_url(self) -> Optional[str]:
        """Get the current page URL."""
        return self.current_url
    
    def is_ready(self) -> bool:
        """Check if scraper is ready to use."""
        return self.session_active
    
    def handle_popup(self) -> bool:
        """Handle popup windows if any."""
        return True
    
    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the page."""
        self.execute_javascript("window.scrollTo(0, document.body.scrollHeight);")
        
    def scroll_to_element(self, selector: str) -> bool:
        """Scroll to a specific element."""
        try:
            self.execute_javascript(
                f"document.querySelector('{selector}').scrollIntoView(true);"
            )
            return True
        except:
            return False


from config.settings import settings