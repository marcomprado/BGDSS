"""
Example site module showing how to create site-specific implementations.
This serves as a template and documentation for creating new site modules.
"""

from typing import Dict, List, Optional, Any
import time
import re

from src.modules.base_site_module import BaseSiteModule
from src.models.site_config import SiteConfig
from src.models.scraping_task import ScrapingTask
from src.utils.logger import logger


class ExampleSiteModule(BaseSiteModule):
    """
    Example implementation of a site-specific module.
    
    This module demonstrates how to:
    1. Override template methods for site-specific behavior
    2. Handle site-specific authentication
    3. Implement custom data extraction logic
    4. Handle site-specific pagination
    """
    
    MODULE_NAME = "example_site"
    MODULE_DESCRIPTION = "Example module for demonstration and template purposes"
    MODULE_VERSION = "1.0"
    SUPPORTED_DOMAINS = ["example.com", "demo.example.com"]
    
    def __init__(self, site_config: SiteConfig):
        super().__init__(site_config)
        self.api_endpoints = {
            'search': '/api/search',
            'details': '/api/details',
            'download': '/api/download'
        }
        self.session_cookies = {}
        
    def _pre_scraping_setup(self, task: ScrapingTask) -> None:
        """Site-specific setup before scraping."""
        logger.info(f"Setting up Example Site scraping for task: {task.task_id}")
        
        task.parameters.update({
            'site_type': 'example',
            'api_version': '2.0',
            'custom_headers': {
                'User-Agent': 'ExampleBot/1.0',
                'Accept': 'application/json'
            }
        })
        
        self.session_data = {
            'search_attempts': 0,
            'max_retries': 3,
            'rate_limit_delay': 2
        }
    
    def _handle_initial_page_interactions(self) -> None:
        """Handle Example Site specific initial interactions."""
        try:
            self._handle_gdpr_banner()
            
            self._handle_location_prompt()
            
            self._dismiss_promotional_overlay()
            
            self._set_preferred_language()
            
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Error in Example Site initial interactions: {e}")
    
    def _handle_gdpr_banner(self) -> None:
        """Handle GDPR consent banner specific to Example Site."""
        gdpr_selectors = [
            'button[data-testid="gdpr-accept"]',
            'button#accept-all-cookies',
            '.cookie-banner button.accept'
        ]
        
        for selector in gdpr_selectors:
            if self.scraper.click_element(selector):
                logger.info("Accepted GDPR banner on Example Site")
                time.sleep(1)
                break
    
    def _handle_location_prompt(self) -> None:
        """Handle location permission prompt."""
        location_selectors = [
            'button[data-testid="location-deny"]',
            'button:contains("Not now")',
            '.location-prompt .deny-button'
        ]
        
        for selector in location_selectors:
            if self.scraper.click_element(selector):
                logger.info("Denied location prompt")
                break
    
    def _dismiss_promotional_overlay(self) -> None:
        """Dismiss promotional overlay if present."""
        overlay_selectors = [
            '.promo-overlay .close-button',
            'button[data-dismiss="promo"]',
            '.modal-overlay button.close'
        ]
        
        for selector in overlay_selectors:
            if self.scraper.click_element(selector):
                logger.info("Dismissed promotional overlay")
                break
    
    def _set_preferred_language(self) -> None:
        """Set preferred language if language selector is present."""
        try:
            language_selector = self.scraper.find_element('.language-selector')
            if language_selector:
                english_option = self.scraper.find_element('option[value="en"]')
                if english_option:
                    english_option.click()
                    logger.info("Set language to English")
        except:
            pass
    
    def _perform_authentication(self) -> bool:
        """Perform Example Site specific authentication."""
        if not self.site_config.auth_config.required:
            return True
        
        try:
            logger.info("Starting Example Site authentication")
            
            login_button = self.scraper.find_element('button[data-testid="login-button"]')
            if not login_button:
                logger.error("Login button not found")
                return False
            
            login_button.click()
            time.sleep(2)
            
            username = self._get_credential('username')
            password = self._get_credential('password')
            
            if not username or not password:
                logger.error("Credentials not found in environment")
                return False
            
            self.scraper.fill_input('input[name="email"]', username)
            self.scraper.fill_input('input[name="password"]', password)
            
            self.scraper.click_element('button[type="submit"]')
            
            time.sleep(5)
            
            if self._verify_login_success():
                logger.info("Example Site authentication successful")
                self._save_session_cookies()
                return True
            else:
                logger.error("Authentication verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Example Site authentication failed: {e}")
            return False
    
    def _verify_login_success(self) -> bool:
        """Verify if login was successful for Example Site."""
        try:
            success_indicators = [
                '.user-menu',
                '[data-testid="user-avatar"]',
                'button:contains("Logout")'
            ]
            
            for indicator in success_indicators:
                if self.scraper.find_element(indicator):
                    return True
            
            current_url = self.scraper.get_current_url()
            return 'dashboard' in current_url or 'profile' in current_url
            
        except Exception as e:
            logger.error(f"Login verification failed: {e}")
            return False
    
    def _save_session_cookies(self) -> None:
        """Save session cookies for later use."""
        try:
            cookies = self.scraper.get_cookies()
            self.session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
            logger.debug(f"Saved {len(self.session_cookies)} session cookies")
        except Exception as e:
            logger.warning(f"Failed to save session cookies: {e}")
    
    def _pre_data_extraction_setup(self) -> None:
        """Setup specific to Example Site before data extraction."""
        try:
            self._navigate_to_data_section()
            
            self._apply_filters()
            
            self._set_items_per_page()
            
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Pre-extraction setup failed: {e}")
    
    def _navigate_to_data_section(self) -> None:
        """Navigate to the main data section."""
        data_section_link = self.scraper.find_element('a[href*="/data"]')
        if data_section_link:
            data_section_link.click()
            time.sleep(3)
            logger.info("Navigated to data section")
    
    def _apply_filters(self) -> None:
        """Apply site-specific filters to refine results."""
        try:
            filter_button = self.scraper.find_element('button[data-testid="filter-toggle"]')
            if filter_button:
                filter_button.click()
                time.sleep(1)
                
                date_filter = self.scraper.find_element('select[name="date_range"]')
                if date_filter:
                    self.scraper.execute_javascript(
                        "arguments[0].value = 'last_30_days';", date_filter
                    )
                
                apply_filter = self.scraper.find_element('button[data-testid="apply-filters"]')
                if apply_filter:
                    apply_filter.click()
                    time.sleep(3)
                    
                logger.info("Applied data filters")
                
        except Exception as e:
            logger.warning(f"Failed to apply filters: {e}")
    
    def _set_items_per_page(self) -> None:
        """Set maximum items per page for efficient scraping."""
        try:
            items_per_page = self.scraper.find_element('select[name="per_page"]')
            if items_per_page:
                self.scraper.execute_javascript(
                    "arguments[0].value = '100';", items_per_page
                )
                time.sleep(1)
                logger.info("Set items per page to 100")
        except:
            pass
    
    def _extract_data(self) -> List[Dict[str, Any]]:
        """Extract data using Example Site specific methods."""
        extracted_items = []
        
        try:
            data_containers = self.scraper.find_elements('.data-item')
            
            logger.info(f"Found {len(data_containers)} data items")
            
            for container in data_containers:
                try:
                    item_data = self._extract_item_from_container(container)
                    if item_data:
                        extracted_items.append(item_data)
                        
                except Exception as e:
                    logger.warning(f"Failed to extract item: {e}")
                    continue
            
            additional_data = self._extract_summary_statistics()
            if additional_data:
                extracted_items.extend(additional_data)
            
            logger.info(f"Successfully extracted {len(extracted_items)} items")
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
        
        return extracted_items
    
    def _extract_item_from_container(self, container) -> Optional[Dict[str, Any]]:
        """Extract data from a single item container."""
        try:
            title_element = container.find_element_by_css_selector('.item-title')
            description_element = container.find_element_by_css_selector('.item-description')
            date_element = container.find_element_by_css_selector('.item-date')
            link_element = container.find_element_by_css_selector('a.item-link')
            
            item_data = {
                'title': title_element.text.strip() if title_element else '',
                'description': description_element.text.strip() if description_element else '',
                'date': date_element.get_attribute('datetime') if date_element else '',
                'url': link_element.get_attribute('href') if link_element else '',
                'item_id': container.get_attribute('data-id') or '',
                'extraction_timestamp': time.time()
            }
            
            price_element = container.find_element_by_css_selector('.item-price')
            if price_element:
                price_text = price_element.text.strip()
                item_data['price'] = self._extract_price(price_text)
            
            category_element = container.find_element_by_css_selector('.item-category')
            if category_element:
                item_data['category'] = category_element.text.strip()
            
            return item_data
            
        except Exception as e:
            logger.debug(f"Error extracting from container: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text."""
        try:
            price_match = re.search(r'(\d+\.?\d*)', price_text.replace(',', ''))
            return float(price_match.group(1)) if price_match else None
        except:
            return None
    
    def _extract_summary_statistics(self) -> List[Dict[str, Any]]:
        """Extract summary statistics from the page."""
        try:
            stats_container = self.scraper.find_element('.statistics-panel')
            if not stats_container:
                return []
            
            stats = {}
            
            stat_elements = stats_container.find_elements_by_css_selector('.stat-item')
            for stat_element in stat_elements:
                label = stat_element.find_element_by_css_selector('.stat-label').text
                value = stat_element.find_element_by_css_selector('.stat-value').text
                stats[label.lower().replace(' ', '_')] = value
            
            if stats:
                return [{
                    'type': 'summary_statistics',
                    'data': stats,
                    'extracted_at': time.time()
                }]
            
        except Exception as e:
            logger.debug(f"Failed to extract summary statistics: {e}")
        
        return []
    
    def _navigate_to_next_page(self) -> bool:
        """Navigate to next page using Example Site specific method."""
        try:
            next_button = self.scraper.find_element('button[data-testid="next-page"]')
            
            if not next_button or not next_button.is_enabled():
                return False
            
            next_button.click()
            
            time.sleep(3)
            
            self.scraper.wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to navigate to next page: {e}")
            return False
    
    def supports_advanced_search(self) -> bool:
        """Check if this module supports advanced search features."""
        return True
    
    def supports_bulk_download(self) -> bool:
        """Check if this module supports bulk file downloads."""
        return True
    
    def get_rate_limit_delay(self) -> float:
        """Get recommended delay between requests for this site."""
        return 2.0  
    
    def get_optimal_batch_size(self) -> int:
        """Get optimal batch size for processing items."""
        return 50
    
    def validate_site_accessibility(self) -> Dict[str, Any]:
        """Validate if the site is accessible and working properly."""
        try:
            if not self.scraper:
                self._initialize_scraper()
            
            if not self._navigate_to_site(self.site_config.base_url):
                return {
                    'accessible': False,
                    'error': 'Failed to navigate to site',
                    'recommendations': ['Check URL and network connectivity']
                }
            
            page_title = self.scraper.execute_javascript("return document.title;")
            if not page_title or 'error' in page_title.lower():
                return {
                    'accessible': False,
                    'error': 'Site appears to be down or showing error page',
                    'recommendations': ['Try again later', 'Check site status']
                }
            
            key_elements = [
                '.main-content',
                '.navigation',
                '.data-section'
            ]
            
            missing_elements = []
            for selector in key_elements:
                if not self.scraper.find_element(selector):
                    missing_elements.append(selector)
            
            return {
                'accessible': True,
                'page_title': page_title,
                'missing_elements': missing_elements,
                'recommendations': [
                    'Site is accessible',
                    f'Missing elements: {missing_elements}' if missing_elements else 'All key elements found'
                ]
            }
            
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e),
                'recommendations': ['Check configuration and try again']
            }
        finally:
            self._final_cleanup()