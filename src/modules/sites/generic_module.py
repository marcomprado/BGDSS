"""
Generic site module that can work with most websites.
Serves as a template and fallback for sites without specific modules.
"""

from typing import Dict, List, Optional, Any
import time
import re

from src.modules.base_site_module import BaseSiteModule
from src.models.site_config import SiteConfig
from src.models.scraping_task import ScrapingTask
from src.utils.logger import logger


class GenericSiteModule(BaseSiteModule):
    """
    Generic site module that implements common scraping patterns.
    Can be used as a template for creating site-specific modules.
    """
    
    MODULE_NAME = "generic"
    MODULE_DESCRIPTION = "Generic module for common website scraping patterns"
    MODULE_VERSION = "1.0"
    SUPPORTED_DOMAINS = []  
    
    def __init__(self, site_config: SiteConfig):
        super().__init__(site_config)
        self.current_page_data = {}
        self.pagination_state = {'current_page': 1, 'has_next': True}
    
    def _pre_scraping_setup(self, task: ScrapingTask) -> None:
        """Setup before scraping starts."""
        logger.info(f"Starting generic scraping for {self.site_config.name}")
        
        task.parameters['module_type'] = 'generic'
        task.parameters['site_domain'] = self._extract_domain(self.site_config.base_url)
        
        self.session_data = {
            'start_time': time.time(),
            'pages_processed': 0,
            'items_extracted': 0
        }
    
    def _handle_initial_page_interactions(self) -> None:
        """Handle common initial page interactions."""
        try:
            self._handle_cookie_consent()
            self._handle_age_verification()
            self._handle_newsletter_popup()
            self._wait_for_page_load()
            
        except Exception as e:
            logger.warning(f"Error in initial page interactions: {e}")
    
    def _handle_cookie_consent(self) -> None:
        """Handle cookie consent popups."""
        cookie_selectors = [
            'button[id*="accept"]',
            'button[class*="accept"]',
            'button[class*="cookie"]',
            'button:contains("Accept")',
            'button:contains("Aceitar")',
            'a[class*="accept"]',
            '[data-cy="accept"]',
            '[data-testid="accept"]'
        ]
        
        for selector in cookie_selectors:
            try:
                if self.scraper.click_element(selector):
                    logger.info("Handled cookie consent")
                    time.sleep(1)
                    break
            except:
                continue
    
    def _handle_age_verification(self) -> None:
        """Handle age verification popups."""
        age_selectors = [
            'button:contains("Yes")',
            'button:contains("Sim")',
            'button:contains("I am 18")',
            'button[class*="age-confirm"]',
            'input[type="checkbox"][name*="age"]'
        ]
        
        for selector in age_selectors:
            try:
                if self.scraper.click_element(selector):
                    logger.info("Handled age verification")
                    time.sleep(1)
                    break
            except:
                continue
    
    def _handle_newsletter_popup(self) -> None:
        """Handle newsletter signup popups."""
        close_selectors = [
            'button[class*="close"]',
            'button[class*="dismiss"]',
            'button:contains("×")',
            'button:contains("Close")',
            'button:contains("No thanks")',
            '[data-dismiss="modal"]'
        ]
        
        for selector in close_selectors:
            try:
                if self.scraper.click_element(selector):
                    logger.info("Closed newsletter popup")
                    time.sleep(1)
                    break
            except:
                continue
    
    def _wait_for_page_load(self) -> None:
        """Wait for page to fully load."""
        try:
            self.scraper.execute_javascript("""
                return document.readyState === 'complete' && 
                       jQuery.active === 0
            """)
        except:
            pass
        
        time.sleep(2)  
    
    def _perform_authentication(self) -> bool:
        """Perform authentication if required."""
        if not self.site_config.auth_config.required:
            return True
        
        try:
            auth = self.site_config.auth_config
            
            logger.info("Attempting authentication")
            
            if auth.username_selector:
                username = self._get_credential('username')
                if not self.scraper.fill_input(auth.username_selector.value, username):
                    logger.error("Failed to fill username")
                    return False
            
            if auth.password_selector:
                password = self._get_credential('password')
                if not self.scraper.fill_input(auth.password_selector.value, password):
                    logger.error("Failed to fill password")
                    return False
            
            if auth.submit_selector:
                if not self.scraper.click_element(auth.submit_selector.value):
                    logger.error("Failed to click submit button")
                    return False
            
            time.sleep(3)
            
            if self._verify_authentication():
                logger.info("Authentication successful")
                return True
            else:
                logger.error("Authentication verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _verify_authentication(self) -> bool:
        """Verify if authentication was successful."""
        try:
            current_url = self.scraper.get_current_url()
            
            if any(indicator in current_url.lower() for indicator in ['login', 'signin', 'auth']):
                return False
            
            success_indicators = ['dashboard', 'profile', 'account', 'logout']
            page_source = self.scraper.get_page_source().lower()
            
            return any(indicator in page_source for indicator in success_indicators)
            
        except:
            return True  
    
    def _pre_data_extraction_setup(self) -> None:
        """Setup before data extraction."""
        self._scroll_to_load_content()
        
        self._handle_lazy_loading()
        
        time.sleep(1)
    
    def _scroll_to_load_content(self) -> None:
        """Scroll page to trigger lazy loading."""
        try:
            self.scraper.execute_javascript("""
                window.scrollTo(0, document.body.scrollHeight/2);
            """)
            time.sleep(1)
            
            self.scraper.execute_javascript("""
                window.scrollTo(0, document.body.scrollHeight);
            """)
            time.sleep(2)
            
            self.scraper.execute_javascript("""
                window.scrollTo(0, 0);
            """)
            
        except Exception as e:
            logger.warning(f"Error scrolling page: {e}")
    
    def _handle_lazy_loading(self) -> None:
        """Handle lazy loading elements."""
        try:
            lazy_selectors = [
                'img[data-src]',
                '[data-lazy]',
                '.lazy',
                '[loading="lazy"]'
            ]
            
            for selector in lazy_selectors:
                elements = self.scraper.find_elements(selector)
                for element in elements[:5]:  
                    try:
                        self.scraper.execute_javascript(
                            "arguments[0].scrollIntoView(true);", element
                        )
                        time.sleep(0.5)
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"Error handling lazy loading: {e}")
    
    def _extract_data(self) -> List[Dict[str, Any]]:
        """Extract data based on site configuration."""
        extracted_items = []
        
        try:
            if not self.site_config.extraction_rules:
                logger.warning("No extraction rules defined, using generic extraction")
                return self._generic_data_extraction()
            
            for rule in self.site_config.extraction_rules:
                try:
                    if rule.selector:
                        elements = self.scraper.find_elements(rule.selector.value)
                        
                        for element in elements:
                            value = self._extract_value_from_element(element, rule)
                            
                            if value or not rule.required:
                                item_data = {rule.name: value or rule.default_value}
                                
                                self._enrich_item_data(item_data, element)
                                
                                extracted_items.append(item_data)
                                
                except Exception as e:
                    logger.warning(f"Failed to extract {rule.name}: {e}")
                    if rule.required:
                        logger.error(f"Required field {rule.name} extraction failed")
            
            self.session_data['items_extracted'] = len(extracted_items)
            
            logger.info(f"Extracted {len(extracted_items)} items from current page")
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
        
        return extracted_items
    
    def _generic_data_extraction(self) -> List[Dict[str, Any]]:
        """Generic data extraction when no rules are specified."""
        try:
            page_source = self.scraper.get_page_source()
            
            text_content = self.scraper.execute_javascript("""
                return document.body.innerText || document.body.textContent || '';
            """)
            
            links = self.scraper.find_elements('a[href]')
            images = self.scraper.find_elements('img[src]')
            
            return [{
                'page_title': self.scraper.execute_javascript("return document.title;"),
                'page_url': self.scraper.get_current_url(),
                'text_length': len(text_content) if text_content else 0,
                'link_count': len(links),
                'image_count': len(images),
                'extraction_method': 'generic',
                'extracted_at': time.time()
            }]
            
        except Exception as e:
            logger.error(f"Generic extraction failed: {e}")
            return []
    
    def _enrich_item_data(self, item_data: Dict[str, Any], element: Any) -> None:
        """Enrich extracted item with additional metadata."""
        try:
            item_data['_element_tag'] = element.tag_name
            item_data['_element_classes'] = element.get_attribute('class') or ''
            item_data['_element_id'] = element.get_attribute('id') or ''
            
        except Exception as e:
            logger.debug(f"Failed to enrich item data: {e}")
    
    def _extract_value_from_element(self, element: Any, rule: Any) -> Any:
        """Extract value from element based on rule."""
        try:
            if rule.data_type == 'text':
                value = element.text.strip()
            elif rule.data_type == 'href':
                value = element.get_attribute('href')
            elif rule.data_type == 'src':
                value = element.get_attribute('src')
            elif rule.data_type == 'value':
                value = element.get_attribute('value')
            elif rule.data_type == 'html':
                value = element.get_attribute('innerHTML')
            else:
                value = element.get_attribute(rule.selector.attribute or 'innerText')
            
            if rule.post_process and value:
                value = self._apply_post_processing(value, rule.post_process)
            
            return value
            
        except Exception:
            return None
    
    def _apply_post_processing(self, value: str, process_type: str) -> str:
        """Apply post-processing to extracted value."""
        if not value:
            return value
        
        try:
            if process_type == 'strip':
                return value.strip()
            elif process_type == 'lower':
                return value.lower()
            elif process_type == 'upper':
                return value.upper()
            elif process_type == 'numbers_only':
                return ''.join(re.findall(r'\d+', value))
            elif process_type == 'clean_whitespace':
                return ' '.join(value.split())
            elif process_type == 'remove_html':
                return re.sub(r'<[^>]+>', '', value)
            else:
                return value
                
        except Exception as e:
            logger.warning(f"Post-processing failed for {process_type}: {e}")
            return value
    
    def _get_credential(self, credential_type: str) -> str:
        """Get credential from environment."""
        import os
        
        if self.site_config.auth_config.credentials_env_prefix:
            env_key = f"{self.site_config.auth_config.credentials_env_prefix}_{credential_type.upper()}"
            return os.getenv(env_key, '')
        
        return ''
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc.lower()
        except:
            return ""
    
    def supports_file_download(self) -> bool:
        """Check if module supports file downloads."""
        return True
    
    def supports_pagination(self) -> bool:
        """Check if module supports pagination."""
        return True
    
    def supports_authentication(self) -> bool:
        """Check if module supports authentication."""
        return True
    
    def get_module_capabilities(self) -> Dict[str, bool]:
        """Get module capabilities."""
        return {
            'file_download': self.supports_file_download(),
            'pagination': self.supports_pagination(),
            'authentication': self.supports_authentication(),
            'javascript_rendering': True,
            'form_filling': True,
            'screenshot_capture': True
        }