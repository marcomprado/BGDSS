"""
MDS Saldo Detalhado Scraper - Direct Selenium Data Extraction

This scraper targets the Brazilian Ministry of Social Development (MDS) system
to extract detailed account balance data (saldo detalhado por conta) using direct Selenium automation.

Target URL: https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*tbmepQbsdfmbtQbhbtNC&event=*fyjcjs
"""

import time
import os
import csv
import glob
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import pandas as pd

from src.utils.logger import logger
from config.webdriver_config import create_configured_driver
from config.settings import settings


class MDSSaldoScraper:
    """
    MDS Saldo Detalhado scraper implementing Selenium automation for government site.
    Handles year/month/UF/municipality filters and CSV report generation.
    """
    
    def __init__(self):
        self.base_url = "https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*tbmepQbsdfmbtQbhbtNC&event=*fyjcjs"
        # Usar caminho do settings para compatibilidade com executável
        self.download_base_path = settings.RAW_DOWNLOADS_DIR / "mds_saldo"
        self.driver = None
        self.wait = None
        self.wait_timeout = 30
        self.ajax_wait_time = 5  # Seconds to wait for AJAX requests
        self.session_start_time = None
        
    def execute_scraping(self, config: Dict[str, Any], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Execute scraping for MDS Saldo Detalhado based on configuration.
        
        Args:
            config: Dictionary with year_config, month, uf, and municipality settings
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict with success status, files downloaded, and statistics
        """
        start_time = datetime.now()
        downloaded_files = []
        errors = []
        total_records = 0
        total_no_data = 0
        
        try:
            self.session_start_time = datetime.now()
            logger.info(f"Starting MDS Saldo scraping with config: {config}")
            
            # Initialize browser
            self._initialize_browser()
            
            # Process based on configuration
            year_config = config.get('year_config', {})
            month_config = config.get('month', {})
            uf = config.get('uf')
            municipality = config.get('municipality')
            
            # Get year list based on configuration
            years_to_process = self._get_years_list(year_config)
            
            # Get month list based on configuration  
            months_to_process = self._get_months_list(month_config)
            
            logger.info(f"Processing {len(years_to_process)} years and {len(months_to_process)} months")
            
            # Process each year/month combination
            for year_idx, year in enumerate(years_to_process):
                for month_idx, month in enumerate(months_to_process):
                    
                    if progress_callback:
                        progress_callback(
                            "querying_balance", 
                            f"Ano {year}, Mês {month} ({year_idx+1}/{len(years_to_process)}, {month_idx+1}/{len(months_to_process)})"
                        )
                    
                    logger.info(f"Processing year {year}, month {month}")
                    
                    result = self._process_single_year_month(
                        year, month, uf, municipality, progress_callback
                    )
                    downloaded_files.extend(result.get('files', []))
                    total_records += result.get('records', 0)
                    total_no_data += result.get('no_data_count', 0)
                    errors.extend(result.get('errors', []))
            
            # Calculate statistics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Calculate total size
            total_size_mb = 0
            for file_path in downloaded_files:
                if os.path.exists(file_path):
                    total_size_mb += os.path.getsize(file_path) / (1024 * 1024)
            
            return {
                'success': len(errors) == 0 and (len(downloaded_files) > 0 or total_no_data > 0),
                'files_downloaded': downloaded_files,
                'total_records': total_records,
                'total_no_data': total_no_data,
                'total_size_mb': round(total_size_mb, 2),
                'duration_minutes': round(duration / 60, 2),
                'download_path': str(self.download_base_path),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Fatal error during MDS Saldo scraping: {str(e)}")
            return {
                'success': False,
                'files_downloaded': downloaded_files,
                'total_records': total_records,
                'total_no_data': total_no_data,
                'errors': [str(e)],
                'download_path': str(self.download_base_path)
            }
        finally:
            self._cleanup()
    
    def _get_years_list(self, year_config: Dict[str, Any]) -> List[int]:
        """Get list of years to process based on configuration."""
        if year_config.get('type') == 'single':
            return [year_config['year']]
        elif year_config.get('type') == 'range':
            return list(range(year_config['start_year'], year_config['end_year'] + 1))
        elif year_config.get('type') == 'multiple':
            return year_config['years']
        elif year_config.get('type') == 'all':
            # Default range from 2011 to current year
            current_year = datetime.now().year
            return list(range(2011, current_year + 1))
        else:
            return [datetime.now().year]  # Fallback to current year
    
    def _get_months_list(self, month_config: Dict[str, Any]) -> List[int]:
        """Get list of months to process based on configuration."""
        if isinstance(month_config, dict):
            if month_config.get('type') == 'single':
                return [month_config['month']]
            elif month_config.get('type') == 'multiple':
                return month_config['months']
            elif month_config.get('type') == 'all':
                return list(range(1, 13))  # All months 1-12
        else:
            # Legacy support for integer month values
            if month_config == 13:
                return list(range(1, 13))  # All months
            elif 1 <= month_config <= 12:
                return [month_config]
        
        return [1]  # Fallback to January
    
    def _initialize_browser(self):
        """Initialize Selenium WebDriver with government site profile."""
        try:
            logger.info("Initializing browser for MDS Saldo site")
            
            # Create download directory
            self.download_base_path.mkdir(parents=True, exist_ok=True)
            
            # Create driver with government sites profile
            self.driver = create_configured_driver(
                profile='government_sites',
                headless=False,  # MDS site may require visible browser
                download_dir=str(self.download_base_path)
            )
            
            self.wait = WebDriverWait(self.driver, self.wait_timeout)
            self.driver.implicitly_wait(10)
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    def _navigate_to_site(self) -> bool:
        """Navigate to MDS Saldo Detalhado site."""
        try:
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for page to load completely
            time.sleep(3)
            
            # Check if main form is present
            self.wait.until(
                EC.presence_of_element_located((By.ID, "form"))
            )
            
            logger.info("Successfully navigated to MDS Saldo site")
            return True
            
        except TimeoutException:
            logger.error("Timeout waiting for MDS Saldo site to load")
            return False
        except Exception as e:
            logger.error(f"Error navigating to site: {str(e)}")
            return False
    
    def _navigate_to_site_with_retry(self, max_attempts: int = 3) -> bool:
        """Navigate to MDS Saldo site with retry mechanism for site instability."""
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Navigation attempt {attempt}/{max_attempts}")
                
                if self._navigate_to_site():
                    logger.info(f"Successfully navigated to site on attempt {attempt}")
                    return True
                else:
                    if attempt < max_attempts:
                        wait_time = attempt  # Progressive delay: 1s, 2s, 3s
                        logger.warning(f"Navigation attempt {attempt} failed. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_attempts} navigation attempts failed")
                        return False
                        
            except Exception as e:
                if attempt < max_attempts:
                    wait_time = attempt  # Progressive delay: 1s, 2s, 3s
                    logger.warning(f"Navigation attempt {attempt} failed with error: {str(e)}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_attempts} navigation attempts failed. Final error: {str(e)}")
                    return False
        
        return False
    
    def _check_browser_health(self) -> bool:
        """Check if browser is still responsive and functional."""
        try:
            # Try to get current URL - this will fail if browser crashed
            current_url = self.driver.current_url
            
            # Try to find basic page elements
            self.driver.find_element(By.TAG_NAME, "body")
            
            # Check if we're still on the expected site
            if "mds.gov.br" in current_url:
                return True
            else:
                logger.warning(f"Browser redirected to unexpected URL: {current_url}")
                return False
                
        except Exception as e:
            logger.warning(f"Browser health check failed: {str(e)}")
            return False
    
    def _recover_browser_session(self) -> bool:
        """Attempt to recover browser session after crash or failure."""
        try:
            logger.info("Attempting browser session recovery")
            
            # Close current driver if it exists
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
            
            # Reinitialize browser
            self._initialize_browser()
            
            # Navigate back to site
            if self._navigate_to_site_with_retry(max_attempts=2):
                logger.info("Browser session recovered successfully")
                return True
            else:
                logger.error("Failed to navigate to site during recovery")
                return False
                
        except Exception as e:
            logger.error(f"Browser recovery failed: {str(e)}")
            return False
    
    def _process_single_year_month(
        self, 
        year: int, 
        month: int, 
        uf: str, 
        municipality: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process scraping for a single year/month combination."""
        files = []
        errors = []
        records = 0
        no_data_count = 0
        
        try:
            # Navigate to site with retry mechanism
            if not self._navigate_to_site_with_retry():
                raise Exception("Failed to navigate to MDS Saldo site after multiple attempts")
            
            # Fill filters
            self._fill_year_filter(str(year))
            self._fill_month_filter(month)
            self._fill_esfera_administrativa()  # Automatically set to MUNICIPAL
            self._fill_uf_filter(uf)
            
            # Handle municipality selection
            if municipality.startswith('ALL_'):
                # Process all municipalities for the state
                municipalities = self._get_all_municipalities()
                logger.info(f"Processing {len(municipalities)} municipalities for {uf}")
                
                for mun_idx, (mun_name, mun_value) in enumerate(municipalities):
                    
                    if progress_callback:
                        progress_callback(
                            "collecting_data", 
                            f"Município {mun_name} ({mun_idx+1}/{len(municipalities)})"
                        )
                    
                    logger.info(f"Processing municipality: {mun_name}")
                    result = self._process_single_municipality(
                        year, month, uf, mun_name, mun_value
                    )
                    files.extend(result.get('files', []))
                    records += result.get('records', 0)
                    no_data_count += result.get('no_data_count', 0)
                    errors.extend(result.get('errors', []))
                    
                    # Add progress callback for no data scenarios
                    if result.get('no_data_count', 0) > 0 and progress_callback:
                        progress_callback("no_data_available", f"Município {mun_name} - sem dados disponíveis")
                    
                    # Re-navigate for next municipality (except for last one)
                    if mun_idx < len(municipalities) - 1:
                        if not self._navigate_to_site_with_retry():
                            logger.error(f"Failed to re-navigate for municipality {mun_idx+2}")
                            continue
                        self._fill_year_filter(str(year))
                        self._fill_month_filter(month)
                        self._fill_esfera_administrativa()
                        self._fill_uf_filter(uf)
            else:
                # Process single municipality
                if progress_callback:
                    progress_callback("collecting_data", f"Município {municipality}")
                
                result = self._process_single_municipality(
                    year, month, uf, municipality, None
                )
                files.extend(result.get('files', []))
                records += result.get('records', 0)
                no_data_count += result.get('no_data_count', 0)
                errors.extend(result.get('errors', []))
                
                # Add progress callback for no data scenarios
                if result.get('no_data_count', 0) > 0 and progress_callback:
                    progress_callback("no_data_available", f"Município {municipality} - sem dados disponíveis")
            
            return {
                'files': files,
                'records': records,
                'no_data_count': no_data_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error processing year {year}, month {month}: {str(e)}")
            errors.append(f"Year {year}, Month {month}: {str(e)}")
            return {
                'files': files,
                'records': records,
                'no_data_count': no_data_count,
                'errors': errors
            }
    
    def _process_single_municipality(
        self, 
        year: int,
        month: int, 
        uf: str, 
        municipality: str,
        municipality_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a single municipality for specific year/month."""
        try:
            # Fill municipality filter
            if municipality_value:
                self._fill_municipality_filter_by_value(municipality_value)
            else:
                self._fill_municipality_filter_by_name(municipality)
            
            # Click search button
            self._click_search_button()
            
            # Wait for results
            time.sleep(3)  # Give time for results to load
            
            # Download CSV report
            download_result = self._download_csv_report(year, month, uf, municipality)
            
            if isinstance(download_result, dict):
                if download_result["status"] == "success":
                    # Count records in CSV
                    file_path = download_result["file_path"]
                    records = self._count_csv_records(file_path)
                    return {
                        'files': [file_path],
                        'records': records,
                        'errors': [],
                        'no_data_count': 0
                    }
                elif download_result["status"] == "no_data":
                    return {
                        'files': [],
                        'records': 0,
                        'errors': [],
                        'no_data_count': 1,
                        'no_data_reason': download_result["message"]
                    }
                else:
                    # Various error types: download_error, browser_error, timeout_error, error
                    return {
                        'files': [],
                        'records': 0,
                        'errors': [f"{municipality} ({year}/{month}): {download_result['message']}"],
                        'no_data_count': 0
                    }
            else:
                # Fallback for unexpected return format
                return {
                    'files': [],
                    'records': 0,
                    'errors': [f"Unexpected error for {municipality} ({year}/{month})"],
                    'no_data_count': 0
                }
                
        except Exception as e:
            logger.error(f"Error processing municipality {municipality}: {str(e)}")
            return {
                'files': [],
                'records': 0,
                'errors': [str(e)],
                'no_data_count': 0
            }
    
    def _fill_year_filter(self, year: str):
        """Fill the year dropdown filter."""
        try:
            logger.info(f"Filling year filter: {year}")
            
            # Wait for year select to be present
            year_select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:ano"))
            )
            
            # Create Select object
            year_select = Select(year_select_element)
            
            # Select by value
            year_select.select_by_value(year)
            
            # Wait for AJAX to complete
            self._wait_for_ajax()
            
            logger.info(f"Year filter set to {year}")
            
        except Exception as e:
            logger.error(f"Error filling year filter: {str(e)}")
            raise
    
    def _fill_month_filter(self, month: int):
        """Fill the month dropdown filter using Portuguese month names."""
        try:
            # Map numeric months to Portuguese month names
            month_names = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
            
            if month not in month_names:
                raise ValueError(f"Invalid month number: {month}. Must be 1-12.")
                
            month_name = month_names[month]
            logger.info(f"Filling month filter: {month} ({month_name})")
            
            # Wait for month select to be present
            month_select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:mes"))
            )
            
            # Create Select object
            month_select = Select(month_select_element)
            
            # Select by visible text (Portuguese month name)
            month_select.select_by_visible_text(month_name)
            
            # Wait for AJAX to complete
            self._wait_for_ajax()
            
            logger.info(f"Month filter set to {month_name}")
            
        except Exception as e:
            logger.error(f"Error filling month filter: {str(e)}")
            raise
    
    def _fill_esfera_administrativa(self):
        """Fill the esfera administrativa dropdown - automatically set to MUNICIPAL."""
        try:
            logger.info("Setting esfera administrativa to MUNICIPAL")
            
            # Wait for esfera administrativa select to be present
            esfera_select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:esferaAdministrativa"))
            )
            
            # Create Select object
            esfera_select = Select(esfera_select_element)
            
            # Select MUNICIPAL (value = "M")
            esfera_select.select_by_value("M")
            
            # Wait for AJAX to complete
            self._wait_for_ajax()
            
            logger.info("Esfera administrativa set to MUNICIPAL")
            
        except Exception as e:
            logger.error(f"Error filling esfera administrativa: {str(e)}")
            raise
    
    def _fill_uf_filter(self, uf: str):
        """Fill the UF (state) dropdown filter."""
        try:
            logger.info(f"Filling UF filter: {uf}")
            
            # Wait for UF select to be present
            uf_select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:uf"))
            )
            
            # Create Select object
            uf_select = Select(uf_select_element)
            
            # Select by value
            uf_select.select_by_value(uf.upper())
            
            # Wait for AJAX to complete (municipalities will be loaded)
            self._wait_for_ajax()
            
            logger.info(f"UF filter set to {uf}")
            
        except Exception as e:
            logger.error(f"Error filling UF filter: {str(e)}")
            raise
    
    def _fill_municipality_filter_by_name(self, municipality: str):
        """Fill the municipality dropdown filter by visible text."""
        try:
            logger.info(f"Filling municipality filter: {municipality}")
            
            # Wait for municipality select to be present and populated
            time.sleep(2)  # Give time for municipalities to load
            
            municipality_select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:municipio"))
            )
            
            # Create Select object
            municipality_select = Select(municipality_select_element)
            
            # Try to select by visible text (case insensitive)
            found = False
            for option in municipality_select.options:
                if option.text.upper() == municipality.upper():
                    municipality_select.select_by_visible_text(option.text)
                    found = True
                    break
            
            if not found:
                logger.warning(f"Municipality {municipality} not found, trying partial match")
                # Try partial match
                for option in municipality_select.options:
                    if municipality.upper() in option.text.upper():
                        municipality_select.select_by_visible_text(option.text)
                        found = True
                        break
            
            if not found:
                raise Exception(f"Municipality {municipality} not found in dropdown")
            
            # Wait for AJAX to complete
            self._wait_for_ajax()
            
            logger.info(f"Municipality filter set to {municipality}")
            
        except Exception as e:
            logger.error(f"Error filling municipality filter: {str(e)}")
            raise
    
    def _fill_municipality_filter_by_value(self, value: str):
        """Fill the municipality dropdown filter by value."""
        try:
            logger.info(f"Filling municipality filter by value: {value}")
            
            # Wait for municipality select to be present
            time.sleep(2)  # Give time for municipalities to load
            
            municipality_select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:municipio"))
            )
            
            # Create Select object
            municipality_select = Select(municipality_select_element)
            
            # Select by value
            municipality_select.select_by_value(value)
            
            # Wait for AJAX to complete
            self._wait_for_ajax()
            
            logger.info(f"Municipality filter set to value {value}")
            
        except Exception as e:
            logger.error(f"Error filling municipality filter by value: {str(e)}")
            raise
    
    def _get_all_municipalities(self) -> List[tuple]:
        """Get all municipalities from the dropdown."""
        try:
            municipality_select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "form:municipio"))
            )
            
            municipality_select = Select(municipality_select_element)
            
            municipalities = []
            for option in municipality_select.options:
                # Skip empty option
                if option.get_attribute('value') and option.text != "-- Selecione --":
                    municipalities.append((option.text, option.get_attribute('value')))
            
            return municipalities
            
        except Exception as e:
            logger.error(f"Error getting municipalities list: {str(e)}")
            return []
    
    def _wait_for_ajax(self):
        """Wait for AJAX requests to complete."""
        try:
            # Wait for modal to appear and disappear
            try:
                # Check if modal is present
                modal = self.driver.find_element(By.ID, "processando")
                if modal:
                    # Wait for modal to disappear
                    self.wait.until(
                        EC.invisibility_of_element_located((By.ID, "processando"))
                    )
            except NoSuchElementException:
                # Modal not present, just wait a bit
                pass
            
            # Additional wait for safety
            time.sleep(self.ajax_wait_time)
            
        except TimeoutException:
            logger.warning("Timeout waiting for AJAX to complete")
        except Exception as e:
            logger.warning(f"Error waiting for AJAX: {str(e)}")
    
    def _click_search_button(self):
        """Click the search button."""
        try:
            logger.info("Clicking search button")
            
            # Find and click search button
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "form:pesquisar"))
            )
            
            search_button.click()
            
            # Wait for results to load
            self._wait_for_ajax()
            
            logger.info("Search executed successfully")
            
        except Exception as e:
            logger.error(f"Error clicking search button: {str(e)}")
            raise
    
    def _download_csv_report(self, year: int, month: int, uf: str, municipality: str) -> Optional[str]:
        """Download the CSV report with robust error handling and recovery."""
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Attempting to download CSV report (attempt {attempt}/{max_attempts})")
                
                # Check if browser is still responsive before proceeding
                if not self._check_browser_health():
                    logger.warning("Browser appears unresponsive, attempting recovery")
                    if not self._recover_browser_session():
                        logger.error("Browser recovery failed")
                        if attempt < max_attempts:
                            continue
                        else:
                            return None
                
                # Check if CSV button is present and data is available
                try:
                    csv_button = self.wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "input[value='Gerar Relatório CSV']")
                        )
                    )
                except TimeoutException:
                    logger.info("CSV button not found - no data available for this period")
                    return {"status": "no_data", "message": "No data available for this time period"}
                
                # Ensure button is clickable and visible
                try:
                    csv_button = self.wait.until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "input[value='Gerar Relatório CSV']")
                        )
                    )
                except TimeoutException:
                    logger.warning(f"CSV button not clickable on attempt {attempt}")
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    else:
                        return {"status": "timeout_error", "message": "CSV button not clickable - page may have issues"}
                
                # Use JavaScript click as fallback to avoid potential click issues
                try:
                    csv_button.click()
                except Exception as click_error:
                    logger.warning(f"Standard click failed: {click_error}. Trying JavaScript click.")
                    self.driver.execute_script("arguments[0].click();", csv_button)
                
                logger.info("CSV download initiated successfully")
                
                # Wait longer for download to start, as government sites can be slow
                time.sleep(3)
                
                # Verify download with extended timeout
                downloaded_file = self._wait_for_download(timeout=45)
                
                if downloaded_file:
                    # Move and rename file
                    final_path = self._organize_downloaded_file(
                        downloaded_file, year, month, uf, municipality
                    )
                    logger.info(f"CSV downloaded successfully: {final_path}")
                    return {"status": "success", "file_path": final_path}
                else:
                    logger.warning(f"CSV download failed on attempt {attempt} - file not found")
                    if attempt < max_attempts:
                        time.sleep(2)
                        continue
                    else:
                        logger.error("All download attempts failed")
                        return {"status": "download_error", "message": "File download failed after all attempts"}
                        
            except Exception as e:
                logger.error(f"Error downloading CSV on attempt {attempt}: {str(e)}")
                
                # Check if this is a browser crash (ChromeDriver stacktrace)
                if "chromedriver" in str(e).lower() or "stacktrace" in str(e).lower():
                    logger.error("Detected ChromeDriver crash, attempting browser recovery")
                    if not self._recover_browser_session():
                        logger.error("Browser recovery failed after crash")
                        return {"status": "browser_error", "message": "Browser crashed and recovery failed"}
                
                if attempt < max_attempts:
                    logger.info(f"Retrying download in 3 seconds... ({attempt}/{max_attempts})")
                    time.sleep(3)
                else:
                    logger.error("All download attempts failed with errors")
                    return {"status": "error", "message": f"Download failed with error: {str(e)}"}
        
        return {"status": "error", "message": "Download failed after all attempts"}
    
    def _wait_for_download(self, timeout: int = 30) -> Optional[str]:
        """Aguarda o download do arquivo CSV ser concluído."""
        start_time = time.time()
        
        # Chrome está baixando em downloads/raw/, não em downloads/raw/mds_saldo/
        actual_download_dir = self.download_base_path.parent  # Isso dará downloads/raw/
        
        while time.time() - start_time < timeout:
            # Busca arquivos CSV no diretório real de download
            csv_files = list(actual_download_dir.glob("*.csv"))
            
            if csv_files:
                # Retorna o arquivo mais recente (último baixado)
                newest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
                return str(newest_file)
            
            time.sleep(1)
        
        return None
    
    def _organize_downloaded_file(
        self, 
        temp_file: str, 
        year: int,
        month: int, 
        uf: str, 
        municipality: str
    ) -> str:
        """Organize downloaded file into proper directory structure."""
        try:
            # Create directory structure - only year folders
            final_dir = self.download_base_path / str(year)
            final_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp - includes UF, municipality, year and month
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"saldo_detalhado_{uf}_{municipality.replace(' ', '_')}_{year}_{month:02d}_{timestamp}.csv"
            final_path = final_dir / filename
            
            # Move file (usar shutil.move para mover entre diretórios diferentes)
            import shutil
            shutil.move(temp_file, str(final_path))
            
            return str(final_path)
            
        except Exception as e:
            logger.error(f"Error organizing downloaded file: {str(e)}")
            return temp_file
    
    def _count_csv_records(self, file_path: str) -> int:
        """Conta registros no arquivo CSV com parsing robusto."""
        try:
            # First try with semicolon separator (standard for MDS)
            try:
                df = pd.read_csv(file_path, encoding='latin-1', sep=';', skiprows=1, on_bad_lines='skip')
                if len(df) > 0:
                    logger.info(f"Successfully counted {len(df)} records using semicolon separator")
                    return len(df)
            except Exception as e1:
                logger.debug(f"Semicolon separator failed: {str(e1)}")
            
            # Try with comma separator
            try:
                df = pd.read_csv(file_path, encoding='latin-1', sep=',', skiprows=1, on_bad_lines='skip')
                if len(df) > 0:
                    logger.info(f"Successfully counted {len(df)} records using comma separator")
                    return len(df)
            except Exception as e2:
                logger.debug(f"Comma separator failed: {str(e2)}")
            
            # Try automatic delimiter detection
            try:
                df = pd.read_csv(file_path, encoding='latin-1', sep=None, engine='python', skiprows=1, on_bad_lines='skip')
                if len(df) > 0:
                    logger.info(f"Successfully counted {len(df)} records using automatic delimiter detection")
                    return len(df)
            except Exception as e3:
                logger.debug(f"Auto delimiter detection failed: {str(e3)}")
            
            # Fallback: count non-empty lines manually
            with open(file_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
                # Skip header lines and count non-empty data lines
                data_lines = [line.strip() for line in lines[1:] if line.strip()]
                logger.info(f"Fallback line counting: {len(data_lines)} non-empty lines")
                return len(data_lines)
                
        except Exception as e:
            logger.warning(f"Could not count CSV records with any method: {str(e)}")
            return 0
    
    def _cleanup(self):
        """Clean up browser and resources."""
        try:
            if self.driver:
                logger.info("Closing browser")
                self.driver.quit()
                self.driver = None
                self.wait = None
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")