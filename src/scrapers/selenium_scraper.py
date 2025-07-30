"""
Selenium-based web scraper implementation.
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

from src.scrapers.base_scraper import BaseScraper
from src.models.site_config import SiteConfig
from src.models.download_result import DownloadResult, FileMetadata
from src.utils.logger import logger
from src.utils.exceptions import ScrapingError
from config.settings import settings


class SeleniumScraper(BaseScraper):
    """Selenium WebDriver implementation of the base scraper."""
    
    def __init__(self, config: Optional[SiteConfig] = None, headless: bool = True):
        super().__init__(config)
        self.driver = None
        self.wait = None
        self.headless = headless
        self.download_dir = settings.RAW_DOWNLOADS_DIR
        
    def initialize_driver(self) -> None:
        """Initialize Chrome WebDriver with options."""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            for option in settings.CHROME_OPTIONS:
                chrome_options.add_argument(option)
            
            prefs = {
                'download.default_directory': str(self.download_dir),
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True,
                'profile.default_content_setting_values.automatic_downloads': 1
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            if settings.WEBDRIVER_PATH == 'auto':
                service = Service(ChromeDriverManager().install())
            else:
                service = Service(settings.WEBDRIVER_PATH)
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.maximize_window()
            
            default_wait = self.config.wait_time if self.config else settings.DEFAULT_WAIT_TIME
            self.wait = WebDriverWait(self.driver, default_wait)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise ScrapingError(f"WebDriver initialization failed: {e}")
    
    def navigate_to(self, url: str) -> bool:
        """Navigate to a URL."""
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            self.current_url = url
            
            time.sleep(2)
            
            self._handle_initial_popups()
            
            return True
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            self.error_count += 1
            return False
    
    def get_page_source(self) -> str:
        """Get the current page HTML source."""
        try:
            return self.driver.page_source
        except Exception as e:
            logger.error(f"Failed to get page source: {e}")
            raise ScrapingError(f"Failed to get page source: {e}")
    
    def find_element(self, selector: str, wait_time: Optional[float] = None) -> Any:
        """Find a single element using CSS selector."""
        try:
            wait_time = wait_time or (self.config.wait_time if self.config else 10)
            
            by_type, selector_value = self._parse_selector(selector)
            
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by_type, selector_value))
            )
            
            return element
            
        except TimeoutException:
            logger.warning(f"Element not found: {selector}")
            return None
        except Exception as e:
            logger.error(f"Error finding element: {e}")
            return None
    
    def find_elements(self, selector: str, wait_time: Optional[float] = None) -> List[Any]:
        """Find multiple elements using CSS selector."""
        try:
            wait_time = wait_time or (self.config.wait_time if self.config else 10)
            
            by_type, selector_value = self._parse_selector(selector)
            
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by_type, selector_value))
            )
            
            elements = self.driver.find_elements(by_type, selector_value)
            
            return elements
            
        except TimeoutException:
            logger.warning(f"Elements not found: {selector}")
            return []
        except Exception as e:
            logger.error(f"Error finding elements: {e}")
            return []
    
    def click_element(self, selector: str) -> bool:
        """Click on an element."""
        try:
            element = self.find_element(selector)
            if not element:
                return False
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(element)
            )
            
            element.click()
            
            logger.debug(f"Clicked element: {selector}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to click element {selector}: {e}")
            return False
    
    def fill_input(self, selector: str, value: str) -> bool:
        """Fill an input field."""
        try:
            element = self.find_element(selector)
            if not element:
                return False
            
            element.clear()
            element.send_keys(value)
            
            logger.debug(f"Filled input {selector} with value")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill input {selector}: {e}")
            return False
    
    def download_file(self, url: str, save_path: Path) -> DownloadResult:
        """Download a file from URL."""
        try:
            start_time = time.time()
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            if self.driver.get_cookies():
                cookie_string = '; '.join([f"{c['name']}={c['value']}" for c in self.driver.get_cookies()])
                headers['Cookie'] = cookie_string
            
            response = requests.get(url, headers=headers, stream=True, timeout=settings.DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            
            total_size = 0
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            download_duration = time.time() - start_time
            
            metadata = FileMetadata(
                size_bytes=total_size,
                mime_type=response.headers.get('content-type', ''),
                encoding=response.encoding
            )
            
            result = DownloadResult(
                source_url=url,
                file_name=save_path.name,
                raw_file_path=save_path,
                download_duration_seconds=download_duration,
                metadata=metadata
            )
            
            logger.info(f"File downloaded successfully: {save_path.name}")
            return result
            
        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            raise ScrapingError(f"Download failed: {e}", url=url)
    
    def take_screenshot(self, save_path: Path) -> bool:
        """Take a screenshot of the current page."""
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            self.driver.save_screenshot(str(save_path))
            logger.info(f"Screenshot saved: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False
    
    def execute_javascript(self, script: str) -> Any:
        """Execute JavaScript on the page."""
        try:
            return self.driver.execute_script(script)
        except Exception as e:
            logger.error(f"JavaScript execution failed: {e}")
            raise ScrapingError(f"JavaScript execution failed: {e}")
    
    def cleanup(self) -> None:
        """Clean up and close the driver."""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def _parse_selector(self, selector: str) -> tuple:
        """Parse selector string and return (By type, selector value)."""
        selector = selector.strip()
        
        if selector.startswith('//'):
            return (By.XPATH, selector)
        elif selector.startswith('#'):
            return (By.ID, selector[1:])
        elif selector.startswith('.'):
            return (By.CLASS_NAME, selector[1:])
        elif selector.startswith('name='):
            return (By.NAME, selector[5:])
        elif selector.startswith('tag='):
            return (By.TAG_NAME, selector[4:])
        else:
            return (By.CSS_SELECTOR, selector)
    
    def _handle_initial_popups(self) -> None:
        """Handle common popups like cookie consent."""
        try:
            cookie_selectors = [
                'button[id*="accept"]',
                'button[class*="accept"]',
                'button[class*="agree"]',
                'button[id*="cookie"]',
                'button:contains("Accept")',
                'a[id*="accept"]'
            ]
            
            for selector in cookie_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        element.click()
                        logger.info("Handled cookie popup")
                        time.sleep(1)
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"No popups to handle: {e}")
    
    def _extract_value_from_element(self, element: Any, rule: Any) -> Any:
        """Extract value from Selenium WebElement."""
        try:
            if rule.data_type == 'text':
                value = element.text.strip()
            elif rule.data_type == 'href':
                value = element.get_attribute('href')
            elif rule.data_type == 'src':
                value = element.get_attribute('src')
            elif rule.data_type == 'value':
                value = element.get_attribute('value')
            else:
                value = element.get_attribute(rule.selector.attribute or 'innerText')
            
            if rule.post_process and value:
                value = self._apply_post_processing(value, rule.post_process)
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to extract value: {e}")
            return None
    
    def _apply_post_processing(self, value: str, process_type: str) -> str:
        """Apply post-processing to extracted value."""
        if process_type == 'strip':
            return value.strip()
        elif process_type == 'lower':
            return value.lower()
        elif process_type == 'upper':
            return value.upper()
        elif process_type == 'numbers_only':
            import re
            return ''.join(re.findall(r'\d+', value))
        else:
            return value
    
    def _get_download_url(self, element: Any) -> Optional[str]:
        """Extract download URL from element."""
        try:
            return element.get_attribute('href') or element.get_attribute('src')
        except:
            return None
    
    def switch_to_iframe(self, iframe_selector: str) -> bool:
        """Switch context to an iframe."""
        try:
            iframe = self.find_element(iframe_selector)
            if iframe:
                self.driver.switch_to.frame(iframe)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to switch to iframe: {e}")
            return False
    
    def switch_to_default_content(self) -> None:
        """Switch back to default content from iframe."""
        try:
            self.driver.switch_to.default_content()
        except Exception as e:
            logger.error(f"Failed to switch to default content: {e}")
    
    def get_cookies(self) -> List[Dict[str, Any]]:
        """Get all cookies from current session."""
        try:
            return self.driver.get_cookies()
        except Exception as e:
            logger.error(f"Failed to get cookies: {e}")
            return []
    
    def add_cookie(self, cookie: Dict[str, Any]) -> bool:
        """Add a cookie to the session."""
        try:
            self.driver.add_cookie(cookie)
            return True
        except Exception as e:
            logger.error(f"Failed to add cookie: {e}")
            return False