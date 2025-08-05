"""
Portal Saude MG Script - Selenium Automation for Resolution PDFs

This script implements direct Selenium automation to extract PDF documents 
from the Minas Gerais health department portal following exact site specifications.

Target URL: https://portal-antigo.saude.mg.gov.br/deliberacoes/documents?by_year=0&by_month=&by_format=pdf&category_id=4795&ordering=newest&q=reso
"""

import time
import os
import re
import psutil
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

from src.utils.logger import logger
from config.webdriver_config import create_configured_driver


class PortalSaudeMGScraper:
    """
    Portal Saude MG scraper implementing exact site automation specifications.
    Handles year/month filters, infinite scroll, and specific PDF extraction patterns.
    """
    
    def __init__(self):
        self.base_url = "https://portal-antigo.saude.mg.gov.br/deliberacoes/documents?by_year=0&by_month=&by_format=pdf&category_id=4795&ordering=newest&q=reso"
        self.download_base_path = Path("downloads/raw/portal_saude_mg")
        self.driver = None
        self.wait_timeout_implicit = 10  # 10 seconds implicit timeout
        self.wait_timeout_explicit = 30  # 30 seconds explicit timeout
        self.session_start_time = None
        self.operation_times = {}  # Track timing for different operations
        
    def execute_scraping(self, ano: str, mes: str = None) -> Dict[str, Any]:
        """
        Execute scraping following exact Portal Saude MG specifications with crash recovery.
        
        Args:
            ano: String with year (ex: "2024")
            mes: String with month ("01" to "12") or None for all months
            
        Returns:
            Dict with success status, files downloaded, total files, and errors
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            start_time = datetime.now()
            downloaded_files = []
            errors = []
            
            try:
                self.session_start_time = datetime.now()
                logger.info(f"Starting Portal Saude MG scraping - Ano: {ano}, Mes: {mes or 'todos'} (Tentativa {retry_count + 1}/{max_retries})")
                self._log_system_resources("session_start")
                
                # 1. Initialize browser and navigate to initial page
                operation_start = self._start_operation_timer("browser_init")
                self._initialize_browser(ano, mes)
                self._end_operation_timer("browser_init", operation_start)
                
                # Navigate to base URL with retry logic
                operation_start = self._start_operation_timer("navigation")
                navigation_success = self._navigate_with_retry()
                self._end_operation_timer("navigation", operation_start)
                if not navigation_success:
                    raise Exception("Falha na navegação para a página inicial após múltiplas tentativas")
                
                # 2. Fill search filters with crash detection
                operation_start = self._start_operation_timer("fill_filters")
                logger.info("Preenchendo filtros de busca")
                self._fill_year_filter(ano)
                if mes:
                    self._fill_month_filter(mes)
                # Note: Search term 'reso' is already included in base URL, no need to fill
                self._end_operation_timer("fill_filters", operation_start)
                
                # 4. Execute search with enhanced monitoring
                operation_start = self._start_operation_timer("execute_search")
                logger.info("Executando busca")
                self._execute_search_with_monitoring()
                self._end_operation_timer("execute_search", operation_start)
                
                # 5. Load all results (infinite scroll) with crash detection
                operation_start = self._start_operation_timer("load_results")
                logger.info("Carregando todos os resultados com scroll infinito")
                self._load_all_results_with_monitoring()
                self._end_operation_timer("load_results", operation_start)
                self._log_system_resources("after_scroll")
                
                # 6. Collect all PDF links
                operation_start = self._start_operation_timer("collect_links")
                logger.info("Coletando todos os links de PDFs")
                pdf_links = self._collect_pdf_links()
                self._end_operation_timer("collect_links", operation_start)
                logger.info(f"Encontrados {len(pdf_links)} links de PDFs")
                
                # 7. Download all PDFs
                if pdf_links:
                    operation_start = self._start_operation_timer("download_pdfs")
                    downloaded_files = self._download_all_pdfs(pdf_links, ano, mes)
                    self._end_operation_timer("download_pdfs", operation_start)
                
                # 8. Calculate results
                duration = (datetime.now() - start_time).total_seconds() / 60
                total_size_mb = sum(os.path.getsize(f) for f in downloaded_files if os.path.exists(f)) / (1024 * 1024)
                
                result = {
                    "success": True,
                    "files_downloaded": downloaded_files,
                    "total_files": len(pdf_links),
                    "duration_minutes": duration,
                    "download_path": str(self._get_download_path(ano, mes)),
                    "total_size_mb": total_size_mb,
                    "errors": errors,
                    "retry_count": retry_count
                }
                
                # Log final session statistics
                self._log_session_summary(result, pdf_links)
                logger.info(f"Scraping concluído com sucesso: {len(downloaded_files)} arquivos baixados")
                return result
                
            except Exception as e:
                error_msg = f"Erro durante scraping (tentativa {retry_count + 1}): {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                
                # Take screenshot on error if possible
                self._take_error_screenshot()
                
                # Check if this looks like a browser crash
                is_browser_crash = self._detect_browser_crash(e)
                
                if is_browser_crash and retry_count < max_retries - 1:
                    logger.warning(f"Browser crash detectado, reiniciando para tentativa {retry_count + 2}")
                    self._force_cleanup()
                    time.sleep(5)  # Wait before retry
                    retry_count += 1
                    continue
                else:
                    # Final failure or non-crash error
                    return {
                        "success": False,
                        "files_downloaded": downloaded_files,
                        "total_files": 0,
                        "errors": errors,
                        "retry_count": retry_count
                    }
                    
            finally:
                self._cleanup()
        
        # If we get here, all retries failed
        return {
            "success": False,
            "files_downloaded": [],
            "total_files": 0,
            "errors": ["Todas as tentativas falharam após detecção de crashes"],
            "retry_count": max_retries
        }
    
    def _navigate_with_retry(self) -> bool:
        """Navigate to base URL with retry logic"""
        for attempt in range(3):
            try:
                logger.info(f"Navegando para a página inicial (tentativa {attempt + 1}/3)")
                self.driver.get(self.base_url)
                self._wait_for_page_load()
                
                # Verify page loaded correctly
                if self._verify_page_loaded():
                    return True
                else:
                    logger.warning("Página não carregou corretamente")
                    if attempt < 2:
                        time.sleep(3)
                        continue
                        
            except Exception as e:
                logger.warning(f"Erro na navegação (tentativa {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(3)
                    continue
                    
        return False
    
    def _verify_page_loaded(self) -> bool:
        """Verify that the page loaded correctly"""
        try:
            # Check for key elements that should be present
            year_select = self.driver.find_elements(By.CSS_SELECTOR, 'select[name="by_year"]')
            search_input = self.driver.find_elements(By.CSS_SELECTOR, 'input[name="q"]')
            
            if year_select and search_input:
                logger.debug("Elementos essenciais da página detectados")
                return True
            else:
                logger.warning("Elementos essenciais da página não encontrados")
                return False
                
        except Exception as e:
            logger.warning(f"Erro na verificação da página: {e}")
            return False
    
    def _execute_search_with_monitoring(self):
        """Execute search with browser monitoring"""
        try:
            # Monitor browser health before search
            if not self._check_browser_health():
                raise Exception("Browser não está respondendo antes da busca")
            
            self._execute_search()
            
            # Monitor browser health after search
            if not self._check_browser_health():
                raise Exception("Browser parou de responder após a busca")
                
        except Exception as e:
            logger.error(f"Erro na busca com monitoramento: {e}")
            raise
    
    def _load_all_results_with_monitoring(self):
        """Load all results with enhanced monitoring"""
        try:
            # Check browser health before starting scroll
            if not self._check_browser_health():
                raise Exception("Browser não está respondendo antes do scroll")
            
            self._load_all_results()
            
            # Final health check
            if not self._check_browser_health():
                logger.warning("Browser não está respondendo após scroll, mas continuando...")
                
        except Exception as e:
            logger.error(f"Erro no scroll com monitoramento: {e}")
            raise
    
    def _check_browser_health(self) -> bool:
        """Check if browser is still responsive"""
        try:
            if not self.driver:
                return False
            
            # Try a simple JavaScript execution
            result = self.driver.execute_script("return 'alive';")
            
            # Check current URL
            current_url = self.driver.current_url
            
            if result == 'alive' and current_url:
                return True
            else:
                logger.warning("Browser health check failed - não responsivo")
                return False
                
        except Exception as e:
            logger.warning(f"Browser health check failed: {e}")
            return False
    
    def _detect_browser_crash(self, exception: Exception) -> bool:
        """Detect if an exception indicates a browser crash"""
        error_str = str(exception).lower()
        crash_indicators = [
            'chrome not reachable',
            'session deleted',
            'session not created',
            'connection refused',
            'connection reset',
            'chrome crashed',
            'chromedriver crashed',
            'segmentation fault',
            'chrome failed to start',
            'browser has been closed',
            'no such session',
            'invalid session id'
        ]
        
        for indicator in crash_indicators:
            if indicator in error_str:
                logger.info(f"Crash detectado por indicador: {indicator}")
                return True
        
        # Also check if driver is no longer accessible
        try:
            if self.driver:
                self.driver.current_url
        except:
            logger.info("Crash detectado - driver não acessível")
            return True
            
        return False
    
    def _force_cleanup(self):
        """Force cleanup of browser resources"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass  # Ignore errors during forced cleanup
            self.driver = None
            
            # Additional cleanup - kill any remaining chrome processes
            import subprocess
            import platform
            
            try:
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["pkill", "-f", "chrome"], capture_output=True)
                elif platform.system() == "Linux":
                    subprocess.run(["pkill", "-f", "chrome"], capture_output=True)
                # Windows cleanup would go here if needed
            except:
                pass  # Ignore errors in process cleanup
                
            logger.info("Force cleanup executado")
            
        except Exception as e:
            logger.debug(f"Erro durante force cleanup: {e}")
    
    def _initialize_browser(self, ano: str, mes: str = None):
        """Initialize browser with proper configurations"""
        try:
            download_path = self._get_download_path(ano, mes)
            download_path.mkdir(parents=True, exist_ok=True)
            
            # Create browser with government sites profile for better stability
            self.driver = create_configured_driver(
                profile='government_sites',
                download_path=str(download_path),
                headless=True,  # Default headless for production
                javascript_enabled=True,
                disable_images=False
            )
            
            # Set timeouts as specified
            self.driver.implicitly_wait(self.wait_timeout_implicit)
            self.driver.set_page_load_timeout(self.wait_timeout_explicit)
            
            logger.info("Browser inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar browser: {e}")
            raise
    
    def _get_download_path(self, ano: str, mes: str = None) -> Path:
        """Get download path following specification: downloads/raw/portal_saude_mg/[ano]/[mes]/"""
        year_path = self.download_base_path / ano
        
        if mes:
            month_names = {
                "01": "janeiro", "02": "fevereiro", "03": "marco", "04": "abril",
                "05": "maio", "06": "junho", "07": "julho", "08": "agosto", 
                "09": "setembro", "10": "outubro", "11": "novembro", "12": "dezembro"
            }
            month_name = month_names.get(mes, mes)
            return year_path / f"{mes}_{month_name}"
        else:
            return year_path / "todos_meses"
    
    def _wait_for_page_load(self):
        """Wait for page to fully load with explicit timeout"""
        try:
            WebDriverWait(self.driver, self.wait_timeout_explicit).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  # Additional wait for dynamic content
            logger.debug("Página carregada completamente")
        except TimeoutException:
            logger.warning("Timeout no carregamento da página - continuando")
    
    def _fill_year_filter(self, ano: str):
        """Fill year filter using exact selector: select[name="by_year"]"""
        try:
            logger.info(f"Selecionando ano: {ano}")
            
            # Find year selector
            year_select = WebDriverWait(self.driver, self.wait_timeout_explicit).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'select[name="by_year"]'))
            )
            
            # Select the year
            select = Select(year_select)
            select.select_by_value(ano)
            
            logger.info(f"Ano {ano} selecionado com sucesso")
            time.sleep(1)  # Wait for any AJAX updates
            
        except TimeoutException:
            error_msg = "Timeout: Seletor de ano não encontrado"
            logger.error(error_msg)
            raise NoSuchElementException(error_msg)
        except Exception as e:
            error_msg = f"Erro ao selecionar ano {ano}: {str(e)}"
            logger.error(error_msg)
            raise
    
    def _fill_month_filter(self, mes: str):
        """Fill month filter using exact selector: select[name="by_month"]"""
        try:
            logger.info(f"Selecionando mês: {mes}")
            
            # Find month selector
            month_select = WebDriverWait(self.driver, self.wait_timeout_explicit).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'select[name="by_month"]'))
            )
            
            # Select the month (values are "01" to "12")
            select = Select(month_select)
            select.select_by_value(mes)
            
            logger.info(f"Mês {mes} selecionado com sucesso")
            time.sleep(1)  # Wait for any AJAX updates
            
        except TimeoutException:
            error_msg = "Timeout: Seletor de mês não encontrado"
            logger.error(error_msg)
            raise NoSuchElementException(error_msg)
        except Exception as e:
            error_msg = f"Erro ao selecionar mês {mes}: {str(e)}"
            logger.error(error_msg)
            raise
    
    # REMOVED: _fill_search_term method - no longer needed since 'reso' is in base URL
    # This method was causing stale element reference errors after year/month selection
    # def _fill_search_term(self):
    #     """Fill search term with fixed value 'Resolução' using input[name="q"]"""
    #     # This method is no longer used - search term is already in the URL
    
    def _execute_search(self):
        """Execute search by submitting the form (filters already applied, search term in URL)"""
        search_strategies = [
            ('form_submit', self._search_with_form_submit_simple),
            ('submit_button', self._search_with_submit_button),
            ('javascript', self._search_with_javascript_simple)
        ]
        
        for strategy_name, strategy_func in search_strategies:
            try:
                logger.info(f"Tentando estratégia de busca: {strategy_name}")
                success = strategy_func()
                if success:
                    logger.info(f"Busca executada com sucesso usando: {strategy_name}")
                    # Wait for search results with multiple validation checks
                    if self._wait_for_search_results():
                        return
                    else:
                        logger.warning(f"Estratégia {strategy_name} executou mas não carregou resultados")
                        continue
                else:
                    logger.warning(f"Estratégia {strategy_name} falhou")
                    continue
                    
            except Exception as e:
                logger.warning(f"Estratégia {strategy_name} gerou erro: {e}")
                continue
        
        # If all strategies failed, take screenshot and raise error
        self._take_error_screenshot()
        raise Exception("Todas as estratégias de busca falharam")
    
    def _search_with_enter(self) -> bool:
        """Execute search using Enter key"""
        try:
            search_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="q"]'))
            )
            search_input.send_keys(Keys.RETURN)
            time.sleep(2)  # Give time for submission
            return True
        except Exception as e:
            logger.debug(f"Enter key strategy failed: {e}")
            return False
    
    def _search_with_submit_button(self) -> bool:
        """Execute search using submit button"""
        try:
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]'))
            )
            submit_button.click()
            time.sleep(2)
            return True
        except Exception as e:
            logger.debug(f"Submit button strategy failed: {e}")
            return False
    
    def _search_with_form_submit(self) -> bool:
        """Execute search by submitting the form"""
        try:
            search_input = self.driver.find_element(By.CSS_SELECTOR, 'input[name="q"]')
            form = search_input.find_element(By.XPATH, './ancestor::form')
            form.submit()
            time.sleep(2)
            return True
        except Exception as e:
            logger.debug(f"Form submit strategy failed: {e}")
            return False
    
    def _search_with_javascript(self) -> bool:
        """Execute search using JavaScript"""
        try:
            self.driver.execute_script("""
                var form = document.querySelector('input[name="q"]').closest('form');
                if (form) {
                    form.submit();
                    return true;
                }
                return false;
            """)
            time.sleep(2)
            return True
        except Exception as e:
            logger.debug(f"JavaScript strategy failed: {e}")
            return False
    
    def _search_with_form_submit_simple(self) -> bool:
        """Execute search by finding and submitting the form directly (avoiding stale elements)"""
        try:
            # Find form by class or general form selector, avoiding specific input elements
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            for form in forms:
                try:
                    # Try to find a form that contains year/month selectors (our target form)
                    year_select = form.find_elements(By.CSS_SELECTOR, 'select[name="by_year"]')
                    if year_select:
                        logger.debug("Found form with year selector, submitting")
                        form.submit()
                        time.sleep(3)
                        return True
                except:
                    continue
            
            logger.debug("No suitable form found")
            return False
        except Exception as e:
            logger.debug(f"Form submit simple strategy failed: {e}")
            return False
    
    def _search_with_javascript_simple(self) -> bool:
        """Execute search using JavaScript to find form without touching search input"""
        try:
            result = self.driver.execute_script("""
                // Find form containing year selector instead of search input
                var yearSelect = document.querySelector('select[name="by_year"]');
                if (yearSelect) {
                    var form = yearSelect.closest('form');
                    if (form) {
                        form.submit();
                        return true;
                    }
                }
                return false;
            """)
            
            if result:
                time.sleep(3)
                return True
            else:
                return False
        except Exception as e:
            logger.debug(f"JavaScript simple strategy failed: {e}")
            return False
    
    def _wait_for_search_results(self) -> bool:
        """Wait for search results to appear with multiple validation methods"""
        try:
            # Strategy 1: Wait for results container
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h2.title, .search-results, .results"))
                )
                logger.debug("Resultados detectados por container")
                time.sleep(3)  # Additional wait for dynamic content
                return True
            except TimeoutException:
                logger.debug("Container de resultados não encontrado")
            
            # Strategy 2: Wait for specific content elements
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h2.title > a"))
                )
                logger.debug("Links de resultados detectados")
                time.sleep(3)
                return True
            except TimeoutException:
                logger.debug("Links de resultados não encontrados")
            
            # Strategy 3: Check for page change or new content
            try:
                # Wait for page to stabilize
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                # Check if URL changed (indicating search was processed)
                current_url = self.driver.current_url
                if "q=" in current_url or "search" in current_url.lower():
                    logger.debug("URL indica que busca foi processada")
                    time.sleep(5)  # Longer wait for results to populate
                    return True
                    
            except TimeoutException:
                logger.debug("Página não estabilizou")
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao aguardar resultados da busca: {e}")
            return False
    
    def _load_all_results(self):
        """Load all results using optimized infinite scroll with timeout protection"""
        try:
            logger.info("Iniciando scroll infinito para carregar todos os resultados")
            
            scroll_count = 0
            max_scrolls = 50  # Reduced safety limit
            consecutive_no_content = 0  # Track consecutive scrolls without new content
            stable_content_checks = 0
            max_scroll_time = 300  # 5 minutes maximum scroll time
            scroll_start_time = time.time()
            
            # Pre-scroll validation - ensure we have initial content
            initial_content = self._count_current_results()
            if initial_content == 0:
                logger.warning("Nenhum conteúdo inicial detectado antes do scroll")
                time.sleep(2)  # Reduced from 5 to 2 seconds
                initial_content = self._count_current_results()
                
            logger.info(f"Conteúdo inicial detectado: {initial_content} itens")
            
            while scroll_count < max_scrolls:
                # Check timeout
                elapsed_time = time.time() - scroll_start_time
                if elapsed_time > max_scroll_time:
                    logger.warning(f"Timeout de scroll atingido ({max_scroll_time}s) - parando")
                    break
                
                # Memory cleanup and health check every 15 scrolls
                if scroll_count > 0 and scroll_count % 15 == 0:
                    self._cleanup_browser_memory()
                    if not self._check_browser_health():
                        logger.warning("Browser não está saudável durante scroll - parando")
                        break
                
                # Multi-method end detection
                if self._check_end_of_content():
                    logger.info("Fim do conteúdo detectado - scroll infinito concluído")
                    break
                
                # Get current content count before scrolling
                current_content_count = self._count_current_results()
                
                # Perform safer scrolling
                scroll_success = self._perform_safe_scroll()
                if not scroll_success:
                    logger.warning("Scroll falhou, tentando métodos alternativos")
                    if not self._alternative_scroll_methods():
                        logger.error("Todos os métodos de scroll falharam")
                        break
                
                # Optimized wait time - much faster
                wait_time = min(1 + (scroll_count // 20), 3)  # 1-3 seconds instead of 3-8
                logger.debug(f"Aguardando {wait_time}s para novo conteúdo...")
                time.sleep(wait_time)
                
                # Check if new content was loaded
                new_content_count = self._count_current_results()
                
                if new_content_count > current_content_count:
                    logger.info(f"✅ Novo conteúdo: {new_content_count - current_content_count} itens (total: {new_content_count})")
                    consecutive_no_content = 0
                    stable_content_checks = 0
                elif new_content_count == current_content_count:
                    consecutive_no_content += 1
                    logger.info(f"⏸️  Nenhum novo conteúdo ({consecutive_no_content} scrolls consecutivos)")
                    
                    # Reduced from 5 to 3 consecutive no-content scrolls
                    if consecutive_no_content >= 3:
                        stable_content_checks += 1
                        logger.info(f"🔍 Conteúdo estável por {consecutive_no_content} scrolls - verificação {stable_content_checks}")
                        
                        # Reduced from 3 to 2 stable checks
                        if stable_content_checks >= 2:
                            logger.info("✅ Fim do conteúdo assumido - parando scroll")
                            break
                
                scroll_count += 1
                
                # More frequent progress reporting
                if scroll_count % 3 == 0:  # Every 3 scrolls instead of 5
                    elapsed = time.time() - scroll_start_time
                    logger.info(f"📊 Scroll #{scroll_count}: {new_content_count} itens ({elapsed:.1f}s decorridos)")
            
            # Final validation
            final_content_count = self._count_current_results()
            
            if scroll_count >= max_scrolls:
                logger.warning(f"Limite máximo de scrolls ({max_scrolls}) atingido")
            
            logger.info(f"Scroll infinito concluído: {scroll_count} scrolls, {final_content_count} itens carregados")
            
        except Exception as e:
            error_msg = f"Erro durante scroll infinito: {str(e)}"
            logger.error(error_msg)
            self._take_error_screenshot()
            # Continue anyway - we may have loaded some content
    
    def _check_end_of_content(self) -> bool:
        """Check for end of content using multiple detection methods"""
        try:
            logger.debug("🔍 Verificando fim do conteúdo...")
            
            # Method 1: Official end message
            try:
                end_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.no-items, .no-content, .end-of-results')
                logger.debug(f"Encontrados {len(end_elements)} elementos de fim potenciais")
                
                for element in end_elements:
                    if element.is_displayed():
                        element_text = element.text.lower()
                        logger.debug(f"Texto do elemento: '{element_text}'")
                        if any(phrase in element_text for phrase in 
                            ["não há mais conteúdo", "no more content", "fim dos resultados", "end of results"]):
                            logger.info("✅ Mensagem oficial de fim detectada")
                            return True
            except Exception as e:
                logger.debug(f"Erro ao verificar mensagem de fim: {e}")
            
            # Method 2: Check if we can't scroll anymore
            try:
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                current_position = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
                
                logger.debug(f"Altura da página: {current_height}px, Posição atual: {current_position}px")
                
                if current_position >= current_height - 100:  # Close to bottom
                    logger.info("✅ Próximo ao final da página - fim do scroll")
                    return True
            except Exception as e:
                logger.debug(f"Erro ao verificar altura da página: {e}")
            
            # Method 3: Look for pagination indicators showing we're at the end
            try:
                pagination_elements = self.driver.find_elements(By.CSS_SELECTOR, '.pagination, .pager, .page-nav')
                for element in pagination_elements:
                    if "última" in element.text.lower() or "last" in element.text.lower():
                        logger.debug("Indicador de última página detectado")
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.debug(f"Erro na detecção de fim: {e}")
            return False
    
    def _count_current_results(self) -> int:
        """Count current number of results on page"""
        try:
            # Count by title links
            title_links = self.driver.find_elements(By.CSS_SELECTOR, "h2.title > a")
            return len(title_links)
        except:
            try:
                # Fallback: count by other result indicators
                results = self.driver.find_elements(By.CSS_SELECTOR, ".result-item, .document-item, .item")
                return len(results)
            except:
                return 0
    
    def _perform_safe_scroll(self) -> bool:
        """Perform safe scrolling with error handling"""
        try:
            # Method 1: Smooth scroll
            self.driver.execute_script("""
                window.scrollBy({
                    top: 300,
                    left: 0,
                    behavior: 'smooth'
                });
            """)
            return True
        except:
            try:
                # Method 2: Direct scroll
                self.driver.execute_script("window.scrollBy(0, 300);")
                return True
            except:
                return False
    
    def _alternative_scroll_methods(self) -> bool:
        """Try alternative scrolling methods if main method fails"""
        try:
            # Method 1: Scroll to element
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, "h2.title")
                if elements:
                    last_element = elements[-1]
                    self.driver.execute_script("arguments[0].scrollIntoView();", last_element)
                    return True
            except:
                pass
            
            # Method 2: Page Down key
            try:
                from selenium.webdriver.common.keys import Keys
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.PAGE_DOWN)
                return True
            except:
                pass
            
            # Method 3: End key
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                body.send_keys(Keys.END)
                return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.debug(f"Métodos alternativos de scroll falharam: {e}")
            return False
    
    def _cleanup_browser_memory(self):
        """Perform browser memory cleanup"""
        try:
            # Clear browser cache and run garbage collection
            self.driver.execute_script("""
                if (window.gc) {
                    window.gc();
                }
                // Clear some browser caches
                if ('caches' in window) {
                    caches.keys().then(function(names) {
                        names.forEach(function(name) {
                            caches.delete(name);
                        });
                    });
                }
            """)
            logger.debug("Limpeza de memória do browser executada")
        except Exception as e:
            logger.debug(f"Falha na limpeza de memória: {e}")
    
    def _collect_pdf_links(self) -> List[Dict[str, str]]:
        """Collect all PDF links using exact selector: h2.title > a, filtering for 'RESOLUÇÃO SES'"""
        try:
            logger.info("Coletando links de PDFs com seletor h2.title > a")
            
            # Find all title links
            title_links = self.driver.find_elements(By.CSS_SELECTOR, "h2.title > a")
            
            pdf_links = []
            
            for link in title_links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    # Filter only links containing "RESOLUÇÃO SES"
                    if href and "RESOLUÇÃO SES" in text.upper():
                        pdf_links.append({
                            'url': href,
                            'title': text,
                            'text': text
                        })
                        logger.debug(f"Link coletado: {text}")
                        
                except Exception as e:
                    logger.debug(f"Erro ao processar link: {e}")
                    continue
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_links = []
            for link in pdf_links:
                if link['url'] not in seen_urls:
                    seen_urls.add(link['url'])
                    unique_links.append(link)
            
            logger.info(f"Coletados {len(unique_links)} links únicos de PDFs com 'RESOLUÇÃO SES'")
            return unique_links
            
        except Exception as e:
            error_msg = f"Erro ao coletar links de PDFs: {str(e)}"
            logger.error(error_msg)
            return []
    
    def _download_all_pdfs(self, pdf_links: List[Dict[str, str]], ano: str, mes: str = None) -> List[str]:
        """Download all PDFs with sequential naming: [mes]-[ano]-RES-[numero_ordem_de_download]"""
        downloaded_files = []
        download_path = self._get_download_path(ano, mes)
        
        logger.info(f"Iniciando download de {len(pdf_links)} PDFs com numeração sequencial")
        
        for download_order, pdf_info in enumerate(pdf_links, 1):
            try:
                logger.info(f"Baixando {download_order} de {len(pdf_links)} arquivos: {pdf_info['title'][:50]}...")
                
                # Create simple sequential filename
                filename = self._create_simple_filename(download_order, ano, mes)
                filepath = download_path / filename
                
                # Check if file already exists
                if filepath.exists():
                    logger.info(f"Arquivo já existe no disco, pulando: {filename}")
                    downloaded_files.append(str(filepath))
                    continue
                
                # Download with retries
                if self._download_file_with_retries(pdf_info['url'], filepath):
                    # Validate PDF file
                    if self._validate_pdf_file(filepath):
                        downloaded_files.append(str(filepath))
                        logger.info(f"Download concluído com sucesso: {filename}")
                    else:
                        logger.error(f"Arquivo PDF corrompido ou inválido: {filename}")
                        if filepath.exists():
                            filepath.unlink()  # Remove corrupted file
                else:
                    logger.error(f"Falha no download após 3 tentativas: {pdf_info['url']}")
                
                # Small delay between downloads
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Erro ao baixar PDF {pdf_info['url']}: {e}")
                continue
        
        logger.info(f"Downloads concluídos: {len(downloaded_files)} arquivos salvos")
        return downloaded_files
    
    def _create_simple_filename(self, download_order: int, ano: str, mes: str = None) -> str:
        """Create filename following pattern: [mes]-[ano]-RES-[numero_ordem_de_download].pdf"""
        try:
            if mes:
                filename = f"{mes}-{ano}-RES-{download_order:03d}.pdf"
            else:
                filename = f"{ano}-RES-{download_order:03d}.pdf"
            
            logger.debug(f"📄 Arquivo #{download_order}: '{filename}'")
            return filename
            
        except Exception as e:
            logger.warning(f"Erro ao criar nome do arquivo: {e}")
            return f"{ano}-RES-{download_order:03d}.pdf"
    
    # REMOVED: Complex filename methods - simplified to sequential numbering per user request
    
    def _download_file_with_retries(self, url: str, filepath: Path, max_retries: int = 3) -> bool:
        """Download file with retry logic"""
        for attempt in range(1, max_retries + 1):
            try:
                # Make URL absolute if needed
                if not url.startswith('http'):
                    url = urljoin(self.base_url, url)
                
                logger.debug(f"Tentativa {attempt}/{max_retries} de download: {url}")
                
                response = requests.get(
                    url, 
                    stream=True, 
                    timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                response.raise_for_status()
                
                # Write file
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                return True
                
            except Exception as e:
                logger.warning(f"Tentativa {attempt}/{max_retries} falhou: {e}")
                if attempt < max_retries:
                    time.sleep(2 * attempt)  # Exponential backoff
                else:
                    logger.error(f"Todas as tentativas de download falharam: {url}")
        
        return False
    
    def _validate_pdf_file(self, filepath: Path) -> bool:
        """Validate if downloaded file is a valid PDF"""
        try:
            if not filepath.exists():
                return False
            
            # Check file size
            if filepath.stat().st_size < 1024:  # Less than 1KB is suspicious
                logger.warning(f"Arquivo muito pequeno: {filepath}")
                return False
            
            # Check PDF header
            with open(filepath, 'rb') as f:
                header = f.read(5)
                if not header.startswith(b'%PDF-'):
                    logger.warning(f"Arquivo não é um PDF válido: {filepath}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Erro ao validar PDF {filepath}: {e}")
            return False
    
    def _take_error_screenshot(self):
        """Take screenshot on error for debugging"""
        try:
            if self.driver:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = self.download_base_path / f"error_screenshot_{timestamp}.png"
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                self.driver.save_screenshot(str(screenshot_path))
                logger.info(f"Screenshot de erro salvo: {screenshot_path}")
        except Exception as e:
            logger.debug(f"Não foi possível salvar screenshot: {e}")
    
    def _cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.debug("Browser fechado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao fechar browser: {e}")
            finally:
                self.driver = None
    
    def _start_operation_timer(self, operation_name: str) -> datetime:
        """Start timing an operation"""
        start_time = datetime.now()
        logger.debug(f"Iniciando operação: {operation_name}")
        return start_time
    
    def _end_operation_timer(self, operation_name: str, start_time: datetime):
        """End timing an operation and log the duration"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        self.operation_times[operation_name] = duration
        logger.info(f"Operação '{operation_name}' concluída em {duration:.2f} segundos")
    
    def _log_system_resources(self, checkpoint: str):
        """Log current system resource usage"""
        try:
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_used_mb = (memory.total - memory.available) / (1024 * 1024)
            memory_percent = memory.percent
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get disk usage for downloads directory
            disk_usage = psutil.disk_usage(str(self.download_base_path.parent))
            disk_free_gb = disk_usage.free / (1024 * 1024 * 1024)
            
            logger.info(f"Recursos do sistema ({checkpoint}): "
                       f"Memória: {memory_used_mb:.1f}MB ({memory_percent:.1f}%), "
                       f"CPU: {cpu_percent:.1f}%, "
                       f"Disco livre: {disk_free_gb:.1f}GB")
                       
            # Log Chrome process memory if available
            try:
                chrome_processes = [p for p in psutil.process_iter(['pid', 'name', 'memory_info']) 
                                 if 'chrome' in p.info['name'].lower()]
                if chrome_processes:
                    total_chrome_memory = sum(p.info['memory_info'].rss for p in chrome_processes) / (1024 * 1024)
                    logger.info(f"Memória total do Chrome: {total_chrome_memory:.1f}MB ({len(chrome_processes)} processos)")
            except:
                pass  # Ignore if can't get Chrome process info
                
        except Exception as e:
            logger.debug(f"Erro ao obter recursos do sistema: {e}")
    
    def _log_session_summary(self, result: Dict[str, Any], pdf_links: List[Dict[str, str]]):
        """Log comprehensive session summary"""
        try:
            if not self.session_start_time:
                return
                
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
            
            logger.info("=== RESUMO DA SESSÃO DE SCRAPING ===")
            logger.info(f"Duração total da sessão: {session_duration:.1f} segundos ({session_duration/60:.1f} minutos)")
            logger.info(f"Status: {'SUCESSO' if result.get('success') else 'FALHA'}")
            logger.info(f"Tentativas realizadas: {result.get('retry_count', 0) + 1}")
            
            # Operation timing breakdown
            if self.operation_times:
                logger.info("=== TEMPO POR OPERAÇÃO ===")
                total_tracked_time = 0
                for operation, duration in self.operation_times.items():
                    percentage = (duration / session_duration) * 100 if session_duration > 0 else 0
                    logger.info(f"  {operation}: {duration:.2f}s ({percentage:.1f}%)")
                    total_tracked_time += duration
                
                untracked_time = session_duration - total_tracked_time
                if untracked_time > 0:
                    percentage = (untracked_time / session_duration) * 100
                    logger.info(f"  outros/overhead: {untracked_time:.2f}s ({percentage:.1f}%)")
            
            # Results summary
            logger.info("=== RESULTADOS ===")
            logger.info(f"Links encontrados: {len(pdf_links)}")
            logger.info(f"Arquivos baixados: {len(result.get('files_downloaded', []))}")
            logger.info(f"Tamanho total: {result.get('total_size_mb', 0):.1f} MB")
            
            if result.get('errors'):
                logger.info(f"Erros encontrados: {len(result['errors'])}")
                for error in result['errors'][:3]:  # Show first 3 errors
                    logger.info(f"  - {error}")
            
            # Performance metrics
            if len(pdf_links) > 0 and session_duration > 0:
                links_per_minute = (len(pdf_links) / session_duration) * 60
                logger.info(f"Taxa de coleta: {links_per_minute:.1f} links/minuto")
                
            if result.get('files_downloaded'):
                downloads = len(result['files_downloaded'])
                if session_duration > 0 and downloads > 0:
                    downloads_per_minute = (downloads / session_duration) * 60
                    avg_file_size = result.get('total_size_mb', 0) / downloads
                    logger.info(f"Taxa de download: {downloads_per_minute:.1f} arquivos/minuto")
                    logger.info(f"Tamanho médio dos arquivos: {avg_file_size:.2f} MB")
            
            logger.info("=== FIM DO RESUMO ===")
            
        except Exception as e:
            logger.debug(f"Erro ao gerar resumo da sessão: {e}")
    
    def _log_browser_state(self, context: str):
        """Log current browser state for debugging"""
        try:
            if not self.driver:
                logger.debug(f"Browser state ({context}): Driver não inicializado")
                return
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            window_size = self.driver.get_window_size()
            
            logger.debug(f"Browser state ({context}): "
                        f"URL: {current_url[:100]}{'...' if len(current_url) > 100 else ''}, "
                        f"Title: {page_title[:50]}{'...' if len(page_title) > 50 else ''}, "
                        f"Window: {window_size['width']}x{window_size['height']}")
            
            # Check for JavaScript errors
            try:
                js_errors = self.driver.execute_script("""
                    return window.jsErrors || [];
                """)
                if js_errors:
                    logger.warning(f"JavaScript errors detectados ({context}): {len(js_errors)} erros")
            except:
                pass
                
        except Exception as e:
            logger.debug(f"Erro ao obter estado do browser ({context}): {e}")
    
    def _log_scroll_progress(self, scroll_count: int, content_count: int, checkpoint: str = ""):
        """Log scrolling progress with detailed metrics"""
        if scroll_count % 5 == 0:  # Log every 5 scrolls
            try:
                # Get current page height
                page_height = self.driver.execute_script("return document.body.scrollHeight")
                current_position = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
                scroll_percentage = (current_position / page_height) * 100 if page_height > 0 else 0
                
                elapsed_time = (datetime.now() - self.session_start_time).total_seconds() if self.session_start_time else 0
                scroll_rate = scroll_count / elapsed_time if elapsed_time > 0 else 0
                
                logger.info(f"Scroll progress {checkpoint}: "
                           f"#{scroll_count}, "
                           f"{content_count} itens, "
                           f"{scroll_percentage:.1f}% da página, "
                           f"{scroll_rate:.2f} scrolls/seg")
                           
                # Log memory usage during intensive scrolling
                if scroll_count % 20 == 0:
                    self._log_system_resources(f"scroll_{scroll_count}")
                    
            except Exception as e:
                logger.debug(f"Erro ao registrar progresso do scroll: {e}")
    
    def get_site_status(self) -> Dict[str, Any]:
        """Check if the Portal Saude MG site is accessible"""
        try:
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