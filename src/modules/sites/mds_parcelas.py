"""
MDS Parcelas Pagas Scraper - Direct Selenium Data Extraction

This scraper targets the Brazilian Ministry of Social Development (MDS) system
to extract municipal payment data (parcelas pagas) using direct Selenium automation.

Target URL: https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*dpotvmubsQbsdfmbtQbhbtNC&event=*fyjcjs
"""

import time
import os
import csv
import glob
from typing import Dict, List, Any, Optional
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


class MDSParcelasScraper:
    """
    MDS Parcelas Pagas scraper implementing Selenium automation for government site.
    Handles year/UF/municipality filters and CSV report generation.
    """
    
    def __init__(self):
        self.base_url = "https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*dpotvmubsQbsdfmbtQbhbtNC&event=*fyjcjs"
        # Usar caminho do settings para compatibilidade com executável
        self.download_base_path = settings.RAW_DOWNLOADS_DIR / "mds_parcelas"
        self.driver = None
        self.wait = None
        self.wait_timeout = 30
        self.ajax_wait_time = 5  # Seconds to wait for AJAX requests
        self.session_start_time = None
        
    def execute_scraping(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute scraping for MDS Parcelas Pagas based on configuration.
        
        Args:
            config: Dictionary with year_config, uf, and municipality settings
            
        Returns:
            Dict with success status, files downloaded, and statistics
        """
        start_time = datetime.now()
        downloaded_files = []
        errors = []
        total_records = 0
        
        try:
            self.session_start_time = datetime.now()
            logger.info(f"Starting MDS Parcelas scraping with config: {config}")
            
            # Initialize browser
            self._initialize_browser()
            
            # Process based on year configuration
            year_config = config.get('year_config', {})
            uf = config.get('uf')
            municipality = config.get('municipality')
            
            if year_config.get('type') == 'single':
                # Single year processing
                result = self._process_single_year(
                    year_config['year'], 
                    uf, 
                    municipality
                )
                downloaded_files.extend(result.get('files', []))
                total_records += result.get('records', 0)
                errors.extend(result.get('errors', []))
                
            elif year_config.get('type') == 'range':
                # Year range processing
                start_year = year_config['start_year']
                end_year = year_config['end_year']
                for year in range(start_year, end_year + 1):
                    logger.info(f"Processing year {year}")
                    result = self._process_single_year(year, uf, municipality)
                    downloaded_files.extend(result.get('files', []))
                    total_records += result.get('records', 0)
                    errors.extend(result.get('errors', []))
                    
            elif year_config.get('type') == 'multiple':
                # Multiple specific years
                for year in year_config['years']:
                    logger.info(f"Processing year {year}")
                    result = self._process_single_year(year, uf, municipality)
                    downloaded_files.extend(result.get('files', []))
                    total_records += result.get('records', 0)
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
                'success': len(errors) == 0 and len(downloaded_files) > 0,
                'files_downloaded': downloaded_files,
                'total_records': total_records,
                'total_size_mb': round(total_size_mb, 2),
                'duration_minutes': round(duration / 60, 2),
                'download_path': str(self.download_base_path),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Fatal error during MDS Parcelas scraping: {str(e)}")
            return {
                'success': False,
                'files_downloaded': downloaded_files,
                'total_records': total_records,
                'errors': [str(e)],
                'download_path': str(self.download_base_path)
            }
        finally:
            self._cleanup()
    
    def _initialize_browser(self):
        """Initialize Selenium WebDriver with government site profile."""
        try:
            logger.info("Initializing browser for MDS site")
            
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
        """Navigate to MDS Parcelas Pagas site."""
        try:
            logger.info(f"Navigating to {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for page to load completely
            time.sleep(3)
            
            # Check if main form is present
            self.wait.until(
                EC.presence_of_element_located((By.ID, "form"))
            )
            
            logger.info("Successfully navigated to MDS site")
            return True
            
        except TimeoutException:
            logger.error("Timeout waiting for MDS site to load")
            return False
        except Exception as e:
            logger.error(f"Error navigating to site: {str(e)}")
            return False
    
    def _process_single_year(self, year: int, uf: str, municipality: str) -> Dict[str, Any]:
        """Process scraping for a single year."""
        files = []
        errors = []
        records = 0
        
        try:
            # Navigate to site
            if not self._navigate_to_site():
                raise Exception("Failed to navigate to MDS site")
            
            # Fill year filter
            self._fill_year_filter(str(year))
            
            # Fill UF filter
            self._fill_uf_filter(uf)
            
            # Handle municipality selection
            if municipality.startswith('ALL_'):
                # Process all municipalities for the state
                municipalities = self._get_all_municipalities()
                logger.info(f"Processing {len(municipalities)} municipalities for {uf}")
                
                for mun_name, mun_value in municipalities:
                    logger.info(f"Processing municipality: {mun_name}")
                    result = self._process_single_municipality(
                        year, uf, mun_name, mun_value
                    )
                    files.extend(result.get('files', []))
                    records += result.get('records', 0)
                    errors.extend(result.get('errors', []))
                    
                    # Re-navigate for next municipality
                    if municipalities.index((mun_name, mun_value)) < len(municipalities) - 1:
                        self._navigate_to_site()
                        self._fill_year_filter(str(year))
                        self._fill_uf_filter(uf)
            else:
                # Process single municipality
                result = self._process_single_municipality(
                    year, uf, municipality, None
                )
                files.extend(result.get('files', []))
                records += result.get('records', 0)
                errors.extend(result.get('errors', []))
            
            return {
                'files': files,
                'records': records,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error processing year {year}: {str(e)}")
            errors.append(f"Year {year}: {str(e)}")
            return {
                'files': files,
                'records': records,
                'errors': errors
            }
    
    def _process_single_municipality(
        self, 
        year: int, 
        uf: str, 
        municipality: str,
        municipality_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a single municipality."""
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
            file_path = self._download_csv_report(year, uf, municipality)
            
            if file_path:
                # Count records in CSV
                records = self._count_csv_records(file_path)
                return {
                    'files': [file_path],
                    'records': records,
                    'errors': []
                }
            else:
                return {
                    'files': [],
                    'records': 0,
                    'errors': [f"Failed to download CSV for {municipality}"]
                }
                
        except Exception as e:
            logger.error(f"Error processing municipality {municipality}: {str(e)}")
            return {
                'files': [],
                'records': 0,
                'errors': [str(e)]
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
    
    def _download_csv_report(self, year: int, uf: str, municipality: str) -> Optional[str]:
        """Download the CSV report."""
        try:
            logger.info("Attempting to download CSV report")
            
            
            # Find and click CSV button
            csv_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "input[value='Gerar Relatório CSV']")
                )
            )
            
            csv_button.click()
            
            # Aguarda o download iniciar e completar
            time.sleep(2)  # Pequena espera inicial para o download começar
            
            # Verifica arquivo baixado com timeout adequado
            downloaded_file = self._wait_for_download()
            
            if downloaded_file:
                # Move and rename file
                final_path = self._organize_downloaded_file(
                    downloaded_file, year, uf, municipality
                )
                logger.info(f"CSV downloaded successfully: {final_path}")
                return final_path
            else:
                logger.error("CSV download failed - file not found")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading CSV: {str(e)}")
            return None
    
    def _wait_for_download(self, timeout: int = 30) -> Optional[str]:
        """Aguarda o download do arquivo CSV ser concluído."""
        start_time = time.time()
        
        # Chrome está baixando corretamente no diretório configurado
        actual_download_dir = self.download_base_path  # Usa downloads/raw/mds_parcelas/
        
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
        uf: str, 
        municipality: str
    ) -> str:
        """Organize downloaded file into proper directory structure."""
        try:
            # Create directory structure - only year folder
            final_dir = self.download_base_path / str(year)
            final_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp - includes UF and municipality
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parcelas_pagas_{uf}_{municipality.replace(' ', '_')}_{year}_{timestamp}.csv"
            final_path = final_dir / filename
            
            # Move file (usar shutil.move para mover entre diretórios diferentes)
            import shutil
            shutil.move(temp_file, str(final_path))
            
            return str(final_path)
            
        except Exception as e:
            logger.error(f"Error organizing downloaded file: {str(e)}")
            return temp_file
    
    def _count_csv_records(self, file_path: str) -> int:
        """Conta registros no arquivo CSV."""
        try:
            # CSV do MDS usa ponto-e-vírgula como separador e tem cabeçalho descritivo
            df = pd.read_csv(file_path, encoding='latin-1', sep=';', skiprows=1)
            return len(df)
        except Exception as e:
            logger.warning(f"Could not count CSV records: {str(e)}")
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