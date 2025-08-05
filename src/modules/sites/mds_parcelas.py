"""
MDS Parcelas Pagas Scraper - Direct Selenium Data Extraction

This scraper targets the Brazilian Ministry of Social Development (MDS) system
to extract municipal payment data (parcelas pagas) using direct Selenium automation.

Target URL: https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*dpotvmubsQbsdfmbtQbhbtNC&event=*fyjcjs
"""

import time
import os
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd

from src.utils.logger import logger
from config.webdriver_config import create_configured_driver


class MDSParcelasScraper:
    """
    Direct Selenium scraper for MDS Parcelas Pagas (Municipal Payment Installments).
    Extracts payment data from Brazilian Ministry of Social Development portal.
    """
    
    def __init__(self):
        self.base_url = "https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*dpotvmubsQbsdfmbtQbhbtNC&event=*fyjcjs"
        self.download_base_path = Path("downloads/mds_parcelas_pagas")
        self.driver = None
        self.wait_timeout = 15
        
    def execute_scraping(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute scraping with direct Selenium automation.
        
        Args:
            config: Contains 'year', 'municipality', and other parameters
            
        Returns:
            Dict with success status, files downloaded, and other metrics
        """
        start_time = datetime.now()
        year = config.get('year', datetime.now().year)
        municipality = config.get('municipality', 'ALL_MG')
        
        # Create download directory
        download_path = self._prepare_download_path(year, municipality)
        
        extracted_data = []
        downloaded_files = []
        errors = []
        
        try:
            logger.info(f"Starting MDS Parcelas scraping - Year: {year}, Municipality: {municipality}")
            
            # Initialize browser
            self._initialize_browser(str(download_path), config.get('headless', False))
            
            # Navigate to the MDS portal
            self.driver.get(self.base_url)
            self._wait_for_page_load()
            
            if municipality == 'ALL_MG':
                # Process all municipalities in Minas Gerais
                municipalities = self._get_mg_municipalities()
                logger.info(f"Found {len(municipalities)} municipalities in MG")
                
                for i, mun_name in enumerate(municipalities, 1):
                    try:
                        logger.info(f"Processing municipality {i}/{len(municipalities)}: {mun_name}")
                        mun_data = self._extract_municipality_data(year, mun_name)
                        if mun_data:
                            extracted_data.extend(mun_data)
                        
                        # Small delay between municipalities
                        time.sleep(1)
                        
                    except Exception as e:
                        error_msg = f"Error processing {mun_name}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
            else:
                # Process single municipality
                mun_data = self._extract_municipality_data(year, municipality)
                if mun_data:
                    extracted_data.extend(mun_data)
            
            # Save extracted data to files
            if extracted_data:
                downloaded_files = self._save_data_files(extracted_data, download_path, year, municipality)
            
            # Calculate results
            duration = (datetime.now() - start_time).total_seconds() / 60
            total_size_mb = sum(os.path.getsize(f) for f in downloaded_files if os.path.exists(f)) / (1024 * 1024)
            
            return {
                'success': True,
                'site': 'mds_parcelas',
                'files_downloaded': len(downloaded_files),
                'downloaded_files': downloaded_files,
                'duration_minutes': duration,
                'download_path': str(download_path),
                'total_size_mb': total_size_mb,
                'records_extracted': len(extracted_data),
                'year': year,
                'municipality': municipality,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"MDS Parcelas scraping failed: {e}")
            duration = (datetime.now() - start_time).total_seconds() / 60
            errors.append(str(e))
            
            return {
                'success': False,
                'site': 'mds_parcelas',
                'error': str(e),
                'duration_minutes': duration,
                'year': year,
                'municipality': municipality,
                'files_downloaded': len(downloaded_files),
                'downloaded_files': downloaded_files,
                'errors': errors
            }
        finally:
            self._cleanup()
    
    def _initialize_browser(self, download_path: str, headless: bool = False):
        """Initialize the web browser with download settings"""
        try:
            self.driver = create_configured_driver(
                profile='comprehensive_scraping',
                download_path=download_path,
                headless=headless,
                javascript_enabled=True,
                disable_images=True  # Speed up loading for data extraction
            )
            self.driver.set_page_load_timeout(30)
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            self.driver = None
    
    def _wait_for_page_load(self):
        """Wait for page to fully load"""
        try:
            WebDriverWait(self.driver, self.wait_timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)
        except TimeoutException:
            logger.warning("Page load timeout - continuing anyway")
    
    def _prepare_download_path(self, year: int, municipality: str) -> Path:
        """Create and return the download directory path"""
        year_path = self.download_base_path / str(year)
        
        if municipality == 'ALL_MG':
            mun_path = year_path / "todos_municipios_mg"
        else:
            # Clean municipality name for filesystem
            clean_name = municipality.replace(' ', '_').replace('/', '_')
            mun_path = year_path / clean_name
            
        mun_path.mkdir(parents=True, exist_ok=True)
        return mun_path
    
    def _get_mg_municipalities(self) -> List[str]:
        """Get list of all municipalities in Minas Gerais from the form"""
        try:
            # Look for state/UF dropdown first
            self._select_state_mg()
            
            # Wait for municipality dropdown to populate
            time.sleep(3)
            
            # Find municipality dropdown
            municipality_selectors = [
                "select[name*='municipio']",
                "select[id*='municipio']",
                "#municipio",
                ".municipio select",
                "select option[value*='MG']"
            ]
            
            municipality_select = None
            for selector in municipality_selectors:
                try:
                    municipality_select = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not municipality_select:
                raise NoSuchElementException("Could not find municipality dropdown")
            
            # Extract all municipality options
            select = Select(municipality_select)
            municipalities = []
            
            for option in select.options:
                value = option.get_attribute('value')
                text = option.text.strip()
                
                # Skip empty options and "Todos" option
                if value and text and text.lower() not in ['todos', 'selecione', '']:
                    municipalities.append(text)
            
            logger.info(f"Found {len(municipalities)} municipalities in MG")
            return municipalities
            
        except Exception as e:
            logger.error(f"Failed to get MG municipalities: {e}")
            # Return some common MG municipalities as fallback
            return [
                'BELO HORIZONTE', 'UBERLANDIA', 'CONTAGEM', 'JUIZ DE FORA',
                'BETIM', 'MONTES CLAROS', 'RIBEIRAO DAS NEVES', 'UBERABA',
                'GOVERNADOR VALADARES', 'IPATINGA'
            ]
    
    def _select_state_mg(self):
        """Select Minas Gerais in the state dropdown"""
        try:
            # Common selectors for state/UF dropdown
            state_selectors = [
                "select[name*='uf']",
                "select[id*='uf']",
                "select[name*='estado']",
                "#uf",
                ".estado select"
            ]
            
            state_select = None
            for selector in state_selectors:
                try:
                    state_select = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not state_select:
                logger.warning("Could not find state dropdown - assuming MG is pre-selected")
                return
            
            # Select Minas Gerais
            select = Select(state_select)
            mg_options = ['MG', 'MINAS GERAIS', 'Minas Gerais']
            
            for mg_option in mg_options:
                try:
                    select.select_by_visible_text(mg_option)
                    logger.info(f"Selected state: {mg_option}")
                    return
                except:
                    try:
                        select.select_by_value(mg_option)
                        logger.info(f"Selected state by value: {mg_option}")
                        return
                    except:
                        continue
            
            logger.warning("Could not select MG in state dropdown")
            
        except Exception as e:
            logger.error(f"Failed to select state MG: {e}")
    
    def _extract_municipality_data(self, year: int, municipality: str) -> List[Dict[str, Any]]:
        """Extract payment data for a specific municipality and year"""
        try:
            logger.info(f"Extracting data for {municipality} - {year}")
            
            # Reset form or navigate back to main form
            self._reset_form()
            
            # Select year
            self._select_year(year)
            
            # Select state (MG)
            self._select_state_mg()
            
            # Select municipality
            self._select_municipality(municipality)
            
            # Submit form and extract data
            self._submit_form()
            
            # Wait for results to load
            time.sleep(5)
            
            # Extract table data
            data = self._extract_table_data(municipality, year)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to extract data for {municipality}: {e}")
            return []
    
    def _reset_form(self):
        """Reset or refresh the form"""
        try:
            # Try to find and click reset button
            reset_selectors = [
                "input[type='reset']",
                "button[type='reset']",
                ".reset",
                ".limpar"
            ]
            
            for selector in reset_selectors:
                try:
                    reset_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    reset_btn.click()
                    time.sleep(1)
                    return
                except:
                    continue
            
            # If no reset button, refresh the page
            self.driver.refresh()
            self._wait_for_page_load()
            
        except Exception as e:
            logger.error(f"Failed to reset form: {e}")
    
    def _select_year(self, year: int):
        """Select year in the form"""
        try:
            year_selectors = [
                "select[name*='ano']",
                "select[id*='ano']",
                "select[name*='year']",
                "#ano"
            ]
            
            for selector in year_selectors:
                try:
                    year_select = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    select = Select(year_select)
                    select.select_by_visible_text(str(year))
                    logger.info(f"Selected year: {year}")
                    return
                    
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"Failed to select year with selector {selector}: {e}")
                    continue
            
            logger.warning(f"Could not find year dropdown to select {year}")
            
        except Exception as e:
            logger.error(f"Failed to select year {year}: {e}")
    
    def _select_municipality(self, municipality: str):
        """Select municipality in the dropdown"""
        try:
            municipality_selectors = [
                "select[name*='municipio']",
                "select[id*='municipio']",
                "#municipio"
            ]
            
            for selector in municipality_selectors:
                try:
                    mun_select = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    select = Select(mun_select)
                    
                    # Try exact match first
                    try:
                        select.select_by_visible_text(municipality)
                        logger.info(f"Selected municipality: {municipality}")
                        return
                    except:
                        # Try partial match
                        for option in select.options:
                            if municipality.upper() in option.text.upper():
                                select.select_by_visible_text(option.text)
                                logger.info(f"Selected municipality (partial match): {option.text}")
                                return
                        
                        raise Exception(f"Municipality {municipality} not found in dropdown")
                        
                except TimeoutException:
                    continue
            
            logger.error(f"Could not find municipality dropdown")
            
        except Exception as e:
            logger.error(f"Failed to select municipality {municipality}: {e}")
    
    def _submit_form(self):
        """Submit the form to get results"""
        try:
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                ".submit",
                ".consultar",
                "input[value*='Consultar']",
                "button:contains('Consultar')"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    submit_btn.click()
                    logger.info("Form submitted successfully")
                    return
                    
                except TimeoutException:
                    continue
            
            logger.warning("Could not find submit button - trying Enter key")
            # Try pressing Enter on any input field
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            if inputs:
                inputs[0].send_keys(Keys.RETURN)
            
        except Exception as e:
            logger.error(f"Failed to submit form: {e}")
    
    def _extract_table_data(self, municipality: str, year: int) -> List[Dict[str, Any]]:
        """Extract data from results table"""
        try:
            # Wait for results table to appear
            table_selectors = [
                "table",
                ".resultado table",
                "#resultado table",
                ".tabela",
                ".dados table"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    table = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not table:
                logger.warning("No results table found")
                return []
            
            # Extract table headers
            headers = []
            header_rows = table.find_elements(By.TAG_NAME, "th")
            if not header_rows:
                # Try first row as headers
                first_row = table.find_element(By.TAG_NAME, "tr")
                header_rows = first_row.find_elements(By.TAG_NAME, "td")
            
            for header in header_rows:
                headers.append(header.text.strip())
            
            # Extract data rows
            data_rows = []
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= len(headers):
                    row_data = {
                        'municipio': municipality,
                        'ano': year,
                        'data_extracao': datetime.now().isoformat()
                    }
                    
                    for i, cell in enumerate(cells[:len(headers)]):
                        if i < len(headers):
                            row_data[headers[i]] = cell.text.strip()
                    
                    data_rows.append(row_data)
            
            logger.info(f"Extracted {len(data_rows)} records for {municipality}")
            return data_rows
            
        except Exception as e:
            logger.error(f"Failed to extract table data: {e}")
            return []
    
    def _save_data_files(self, data: List[Dict[str, Any]], download_path: Path, year: int, municipality: str) -> List[str]:
        """Save extracted data to CSV and Excel files"""
        saved_files = []
        
        try:
            if not data:
                return saved_files
            
            # Create base filename
            if municipality == 'ALL_MG':
                base_name = f"mds_parcelas_mg_{year}"
            else:
                clean_mun = municipality.replace(' ', '_').replace('/', '_')
                base_name = f"mds_parcelas_{clean_mun}_{year}"
            
            # Save as CSV
            csv_file = download_path / f"{base_name}.csv"
            df = pd.DataFrame(data)
            df.to_csv(csv_file, index=False, encoding='utf-8')
            saved_files.append(str(csv_file))
            logger.info(f"Saved CSV file: {csv_file}")
            
            # Save as Excel
            excel_file = download_path / f"{base_name}.xlsx"
            df.to_excel(excel_file, index=False, engine='openpyxl')
            saved_files.append(str(excel_file))
            logger.info(f"Saved Excel file: {excel_file}")
            
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save data files: {e}")
            return saved_files
    
    def get_site_status(self) -> Dict[str, Any]:
        """Check if the MDS site is accessible"""
        try:
            import requests
            
            response = requests.get(self.base_url, timeout=10)
            
            return {
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'checked_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'accessible': False,
                'error': str(e),
                'checked_at': datetime.now().isoformat()
            }


