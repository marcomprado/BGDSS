"""
Base site module implementing Template Method pattern for site-specific scraping.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime

from src.models.site_config import SiteConfig
from src.models.scraping_task import ScrapingTask, TaskStatus
from src.scrapers.selenium_scraper import SeleniumScraper
from src.ai.navigator_agent import NavigatorAgent
from src.utils.logger import logger
from src.utils.exceptions import ScrapingError


class BaseSiteModule(ABC):
    """
    Abstract base class for site-specific scraping modules.
    Implements Template Method pattern for consistent scraping workflow.
    """
    
    def __init__(self, site_config: SiteConfig):
        self.site_config = site_config
        self.scraper = None
        self.navigator = NavigatorAgent()
        self.session_data = {}
        self.extracted_items = []
        
        logger.info(f"Initialized {self.__class__.__name__} for {site_config.name}")
    
    def execute_scraping_task(self, task: ScrapingTask) -> ScrapingTask:
        """
        Template Method: Execute complete scraping workflow.
        This method defines the algorithm structure and calls hook methods.
        """
        task.start()
        
        try:
            logger.info(f"Starting scraping task for {self.site_config.name}")
            
            self._pre_scraping_setup(task)
            
            if not self._initialize_scraper():
                raise ScrapingError("Failed to initialize scraper")
            
            if not self._navigate_to_site(task.target_url or self.site_config.base_url):
                raise ScrapingError("Failed to navigate to site")
            
            self._handle_initial_page_interactions()
            
            if self.site_config.auth_config.required:
                if not self._perform_authentication():
                    raise ScrapingError("Authentication failed")
            
            self._pre_data_extraction_setup()
            
            extracted_data = self._extract_data()
            
            for item in extracted_data:
                task.add_extracted_item(item)
                self.extracted_items.append(item)
            
            if self._should_download_files():
                self._download_files(task)
            
            if self._should_handle_pagination():
                self._handle_pagination(task)
            
            self._post_data_extraction_processing(task)
            
            self._cleanup_session()
            
            task.complete()
            logger.info(f"Scraping task completed successfully for {self.site_config.name}")
            
        except Exception as e:
            logger.error(f"Scraping task failed: {e}")
            self._handle_scraping_error(e, task)
        
        finally:
            self._final_cleanup()
        
        return task
    
    def _initialize_scraper(self) -> bool:
        """Initialize the scraper instance."""
        try:
            self.scraper = SeleniumScraper(self.site_config, headless=True)
            self.scraper.start_session()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            return False
    
    def _navigate_to_site(self, url: str) -> bool:
        """Navigate to the target site."""
        try:
            return self.scraper.navigate_to(url)
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def _cleanup_session(self) -> None:
        """Clean up scraping session."""
        if self.scraper:
            self.scraper.end_session()
    
    def _final_cleanup(self) -> None:
        """Final cleanup after task completion."""
        if self.scraper:
            try:
                self.scraper.cleanup()
            except:
                pass
    
    def _handle_scraping_error(self, error: Exception, task: ScrapingTask) -> None:
        """Handle scraping errors."""
        from src.models.scraping_task import TaskError
        
        task_error = TaskError(
            error_type=type(error).__name__,
            error_message=str(error),
            recoverable=self._is_error_recoverable(error)
        )
        
        task.fail(task_error)
        
        if task.is_retriable():
            logger.info("Task marked for retry")
            task.retry()
    
    def _is_error_recoverable(self, error: Exception) -> bool:
        """Determine if error is recoverable."""
        recoverable_errors = [
            'TimeoutException',
            'NoSuchElementException',
            'WebDriverException'
        ]
        
        return type(error).__name__ in recoverable_errors
    
    @abstractmethod
    def _pre_scraping_setup(self, task: ScrapingTask) -> None:
        """
        Hook: Perform site-specific setup before scraping starts.
        Override in subclasses for custom initialization.
        """
        pass
    
    @abstractmethod
    def _handle_initial_page_interactions(self) -> None:
        """
        Hook: Handle initial page interactions (popups, cookies, etc.).
        Override in subclasses for site-specific interactions.
        """
        pass
    
    @abstractmethod
    def _perform_authentication(self) -> bool:
        """
        Hook: Perform site-specific authentication.
        Override in subclasses if authentication is required.
        """
        return True
    
    @abstractmethod
    def _pre_data_extraction_setup(self) -> None:
        """
        Hook: Setup before data extraction (navigation, form filling, etc.).
        Override in subclasses for site-specific preparation.
        """
        pass
    
    @abstractmethod
    def _extract_data(self) -> List[Dict[str, Any]]:
        """
        Hook: Extract data from the current page(s).
        Override in subclasses with site-specific extraction logic.
        """
        pass
    
    def _should_download_files(self) -> bool:
        """Determine if files should be downloaded."""
        return self.site_config.download_files
    
    def _download_files(self, task: ScrapingTask) -> None:
        """Download files if configured."""
        if not self.site_config.file_download_selector:
            return
        
        try:
            download_links = self.scraper.find_elements(
                self.site_config.file_download_selector.value
            )
            
            for link in download_links[:10]:  
                try:
                    url = link.get_attribute('href')
                    if url:
                        filename = url.split('/')[-1] or f"download_{int(datetime.now().timestamp())}"
                        save_path = Path(f"downloads/raw/{filename}")
                        
                        result = self.scraper.download_file(url, save_path)
                        result.task_id = task.task_id
                        
                        task.metrics.files_downloaded += 1
                        logger.info(f"Downloaded: {filename}")
                        
                except Exception as e:
                    logger.warning(f"Failed to download file: {e}")
                    
        except Exception as e:
            logger.error(f"File download process failed: {e}")
    
    def _should_handle_pagination(self) -> bool:
        """Determine if pagination should be handled."""
        return self.site_config.pagination_config.enabled
    
    def _handle_pagination(self, task: ScrapingTask) -> None:
        """Handle pagination if enabled."""
        if not self.site_config.pagination_config.enabled:
            return
        
        pagination = self.site_config.pagination_config
        current_page = 1
        
        while current_page < pagination.max_pages:
            try:
                if not self._navigate_to_next_page():
                    logger.info("No more pages available")
                    break
                
                current_page += 1
                task.metrics.pages_scraped += 1
                
                new_data = self._extract_data()
                
                if not new_data and pagination.stop_on_no_results:
                    logger.info("No data on page, stopping pagination")
                    break
                
                for item in new_data:
                    task.add_extracted_item(item)
                    self.extracted_items.append(item)
                
                import time
                time.sleep(pagination.wait_between_pages)
                
            except Exception as e:
                logger.warning(f"Pagination error on page {current_page}: {e}")
                break
    
    def _navigate_to_next_page(self) -> bool:
        """Navigate to the next page."""
        pagination = self.site_config.pagination_config
        
        if pagination.next_button_selector:
            return self.scraper.click_element(pagination.next_button_selector.value)
        
        return False
    
    def _post_data_extraction_processing(self, task: ScrapingTask) -> None:
        """Hook: Post-process extracted data."""
        self._validate_extracted_data()
        self._enrich_data_with_metadata()
    
    def _validate_extracted_data(self) -> None:
        """Validate extracted data quality."""
        if not self.extracted_items:
            logger.warning("No data was extracted")
            return
        
        for rule in self.site_config.extraction_rules:
            if rule.required:
                missing_count = sum(1 for item in self.extracted_items if rule.name not in item)
                if missing_count > 0:
                    logger.warning(f"Required field '{rule.name}' missing in {missing_count} items")
    
    def _enrich_data_with_metadata(self) -> None:
        """Enrich extracted data with metadata."""
        for item in self.extracted_items:
            item['_scraped_at'] = datetime.now().isoformat()
            item['_source_site'] = self.site_config.name
            item['_scraper_version'] = "1.0"
    
    def get_site_health_status(self) -> Dict[str, Any]:
        """Check if the site is accessible and working."""
        try:
            if not self.scraper:
                self._initialize_scraper()
            
            if not self._navigate_to_site(self.site_config.base_url):
                return {'status': 'unhealthy', 'reason': 'Navigation failed'}
            
            page_source = self.scraper.get_page_source()
            
            if len(page_source) < 100:
                return {'status': 'unhealthy', 'reason': 'Empty or minimal page content'}
            
            key_elements_found = 0
            for selector_name, selector in self.site_config.selectors.items():
                if self.scraper.find_element(selector.value):
                    key_elements_found += 1
            
            health_score = key_elements_found / max(len(self.site_config.selectors), 1)
            
            return {
                'status': 'healthy' if health_score > 0.5 else 'degraded',
                'health_score': health_score,
                'elements_found': key_elements_found,
                'total_elements': len(self.site_config.selectors),
                'page_size': len(page_source),
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'reason': str(e),
                'checked_at': datetime.now().isoformat()
            }
        finally:
            self._final_cleanup()
    
    def dry_run(self) -> Dict[str, Any]:
        """Perform a dry run to test the module configuration."""
        try:
            logger.info(f"Starting dry run for {self.site_config.name}")
            
            validation_issues = self.site_config.validate()
            if validation_issues:
                return {
                    'success': False,
                    'issues': validation_issues,
                    'recommendation': 'Fix configuration issues before running'
                }
            
            if not self._initialize_scraper():
                return {
                    'success': False,
                    'issues': ['Failed to initialize scraper'],
                    'recommendation': 'Check WebDriver installation'
                }
            
            if not self._navigate_to_site(self.site_config.base_url):
                return {
                    'success': False,
                    'issues': ['Failed to navigate to site'],
                    'recommendation': 'Check URL and network connectivity'
                }
            
            found_elements = {}
            for name, selector in self.site_config.selectors.items():
                element = self.scraper.find_element(selector.value, wait_time=2)
                found_elements[name] = element is not None
            
            return {
                'success': True,
                'site_accessible': True,
                'elements_found': found_elements,
                'recommendations': self._generate_optimization_recommendations(found_elements)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'recommendation': 'Check site configuration and network connectivity'
            }
        finally:
            self._final_cleanup()
    
    def _generate_optimization_recommendations(self, elements_found: Dict[str, bool]) -> List[str]:
        """Generate optimization recommendations based on dry run results."""
        recommendations = []
        
        missing_elements = [name for name, found in elements_found.items() if not found]
        
        if missing_elements:
            recommendations.append(f"Update selectors for missing elements: {', '.join(missing_elements)}")
        
        if len(missing_elements) > len(elements_found) / 2:
            recommendations.append("Consider updating site configuration - many elements not found")
        
        if self.site_config.wait_time < 5:
            recommendations.append("Consider increasing wait time for better element detection")
        
        return recommendations
    
    def get_extracted_data_summary(self) -> Dict[str, Any]:
        """Get summary of extracted data."""
        if not self.extracted_items:
            return {'total_items': 0, 'fields': [], 'sample': None}
        
        all_fields = set()
        for item in self.extracted_items:
            all_fields.update(item.keys())
        
        return {
            'total_items': len(self.extracted_items),
            'fields': list(all_fields),
            'sample': self.extracted_items[0] if self.extracted_items else None,
            'field_coverage': {
                field: sum(1 for item in self.extracted_items if field in item and item[field])
                for field in all_fields
            }
        }