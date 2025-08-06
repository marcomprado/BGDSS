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
        Execute scraping for Portal Saude MG.
        
        Args:
            ano: String with year (ex: "2024")
            mes: String with month ("01" to "12") or None for all months
            
        Returns:
            Dict with success status, files downloaded, total files, and errors
        """
        
        start_time = datetime.now()
        downloaded_files = []
        errors = []
        
        try:
            self.session_start_time = datetime.now()
            logger.info(f"Starting Portal Saude MG scraping - Ano: {ano}, Mes: {mes or 'todos'}")
            
            # 1. Initialize browser and navigate to initial page
            operation_start = self._start_operation_timer("browser_init")
            self._initialize_browser(ano, mes)
            self._end_operation_timer("browser_init", operation_start)
            
            # Navigate to base URL with retry logic
            operation_start = self._start_operation_timer("navigation")
            navigation_success = self._navigate_with_retry()
            self._end_operation_timer("navigation", operation_start)
            if not navigation_success:
                raise Exception("Falha na navegação para a página inicial")
            
            # 2. Fill search filters
            operation_start = self._start_operation_timer("fill_filters")
            logger.info("Preenchendo filtros de busca")
            self._fill_year_filter(ano)
            if mes:
                self._fill_month_filter(mes)
            self._end_operation_timer("fill_filters", operation_start)
            
            # 3. Execute search
            operation_start = self._start_operation_timer("execute_search")
            logger.info("Executando busca")
            self._execute_search()
            self._end_operation_timer("execute_search", operation_start)
            
            # 4. Load all results (infinite scroll)
            operation_start = self._start_operation_timer("load_results")
            logger.info("Carregando todos os resultados com scroll infinito")
            self._load_all_results()
            self._end_operation_timer("load_results", operation_start)
            
            # 5. Collect all PDF links
            operation_start = self._start_operation_timer("collect_links")
            logger.info("Coletando todos os links de PDFs")
            pdf_links = self._collect_pdf_links()
            self._end_operation_timer("collect_links", operation_start)
            logger.info(f"Encontrados {len(pdf_links)} links de PDFs")
            
            # 6. Download all PDFs
            if pdf_links:
                operation_start = self._start_operation_timer("download_pdfs")
                downloaded_files = self._download_all_pdfs(pdf_links, ano, mes)
                self._end_operation_timer("download_pdfs", operation_start)
            
            # 7. Calculate results
            duration = (datetime.now() - start_time).total_seconds() / 60
            total_size_mb = sum(os.path.getsize(file_info['file_path']) for file_info in downloaded_files if os.path.exists(file_info['file_path'])) / (1024 * 1024)
            
            # 8. Save URL mapping for PDF processing
            download_path = self._get_download_path(ano, mes)
            url_mapping = self._save_url_mapping(downloaded_files, download_path)
            
            result = {
                "success": True,
                "files_downloaded": downloaded_files,
                "total_files": len(pdf_links),
                "duration_minutes": duration,
                "download_path": str(download_path),
                "url_mapping_file": url_mapping,
                "total_size_mb": total_size_mb,
                "errors": errors
            }
                
            logger.info(f"Scraping concluído com sucesso: {len(downloaded_files)} arquivos baixados")
            return result
            
        except Exception as e:
            error_msg = f"Erro durante scraping: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            return {
                "success": False,
                "files_downloaded": downloaded_files,
                "total_files": 0,
                "errors": errors
            }
            
        finally:
            self._cleanup()
    
    def _navigate_with_retry(self) -> bool:
        """Navigate to base URL"""
        try:
            logger.info("Navegando para a página inicial")
            self.driver.get(self.base_url)
            self._wait_for_page_load()
            return self._verify_page_loaded()
        except Exception as e:
            logger.error(f"Erro na navegação: {e}")
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
    
    
    def _execute_search(self):
        """Execute search - since filters are applied via URL, just wait for page to load"""
        logger.info("Aguardando carregamento da página com filtros aplicados")
        
        # Simply wait for the page to load with applied filters
        if self._wait_for_search_results():
            logger.info("Página carregada com sucesso")
            return
        
        raise Exception("Falha ao carregar página com filtros")
    
    def _wait_for_search_results(self) -> bool:
        """Wait for search results to appear"""
        try:
            # Wait for results to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h2.title > a"))
            )
            logger.debug("Resultados carregados")
            time.sleep(2)  # Short wait for stabilization
            return True
            
        except TimeoutException:
            logger.warning("Timeout ao aguardar resultados")
            return False
        except Exception as e:
            logger.error(f"Erro ao aguardar resultados: {e}")
            return False
    
    def _load_all_results(self):
        """Load all results using fast infinite scroll"""
        logger.info("Iniciando scroll infinito otimizado")
        
        scroll_count = 0
        max_scrolls = 50
        consecutive_no_content = 0
        scroll_start_time = time.time()
        
        initial_content = self._count_current_results()
        logger.info(f"Conteúdo inicial: {initial_content} itens")
        
        while scroll_count < max_scrolls:
            # Quick timeout check (2 minutes max)
            if time.time() - scroll_start_time > 120:
                logger.info("Timeout de 2 minutos atingido - finalizando")
                break
            
            # Simple end detection
            if self._is_at_page_bottom():
                logger.info("Final da página atingido")
                break
            
            current_count = self._count_current_results()
            
            # Fast scroll
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.8)  # Much faster wait
            
            new_count = self._count_current_results()
            
            if new_count > current_count:
                logger.debug(f"Novo conteúdo: +{new_count - current_count} (total: {new_count})")
                consecutive_no_content = 0
            else:
                consecutive_no_content += 1
                if consecutive_no_content >= 3:  # Quick exit after 3 failed attempts
                    logger.info("Nenhum conteúdo novo por 3 scrolls - finalizando")
                    break
            
            scroll_count += 1
            
            if scroll_count % 10 == 0:
                elapsed = time.time() - scroll_start_time
                logger.info(f"Scroll #{scroll_count}: {new_count} itens ({elapsed:.1f}s)")
        
        final_count = self._count_current_results()
        logger.info(f"Scroll concluído: {final_count} itens em {scroll_count} scrolls")
    
    def _is_at_page_bottom(self) -> bool:
        """Simple check if we're at the bottom of the page"""
        try:
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = self.driver.execute_script("return window.pageYOffset + window.innerHeight")
            return current_position >= current_height - 200
        except:
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
    
    def _collect_pdf_links(self) -> List[Dict[str, str]]:
        """Collect all PDF links using exact selector: h2.title > a"""
        try:
            logger.info("Coletando todos os links de documentos")
            
            # Find all title links
            title_links = self.driver.find_elements(By.CSS_SELECTOR, "h2.title > a")
            
            pdf_links = []
            
            for link in title_links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    # Collect all links with valid href (no name filtering)
                    if href and text:
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
            
            logger.info(f"Coletados {len(unique_links)} links únicos de documentos")
            return unique_links
            
        except Exception as e:
            error_msg = f"Erro ao coletar links de PDFs: {str(e)}"
            logger.error(error_msg)
            return []
    
    def _download_all_pdfs(self, pdf_links: List[Dict[str, str]], ano: str, mes: str = None) -> List[Dict[str, str]]:
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
                    downloaded_files.append({
                        'file_path': str(filepath),
                        'url': pdf_info['url'],
                        'title': pdf_info['title']
                    })
                    continue
                
                # Download with retries
                if self._download_file_with_retries(pdf_info['url'], filepath):
                    # Validate PDF file
                    if self._validate_pdf_file(filepath):
                        downloaded_files.append({
                            'file_path': str(filepath),
                            'url': pdf_info['url'],
                            'title': pdf_info['title']
                        })
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
            
            logger.debug(f"Arquivo #{download_order}: '{filename}'")
            return filename
            
        except Exception as e:
            logger.warning(f"Erro ao criar nome do arquivo: {e}")
            return f"{ano}-RES-{download_order:03d}.pdf"
    
    
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
    
    def _save_url_mapping(self, downloaded_files: List[Dict[str, str]], download_path: Path) -> str:
        """
        Save URL mapping to a JSON file for PDF processor to use.
        
        Args:
            downloaded_files: List of file info dictionaries
            download_path: Path where files were downloaded
            
        Returns:
            Path to the saved URL mapping file
        """
        try:
            import json
            from pathlib import Path
            
            # Create mapping from filename to URL
            url_mapping = {}
            for file_info in downloaded_files:
                file_path = Path(file_info['file_path'])
                filename = file_path.name
                url_mapping[filename] = {
                    'url': file_info['url'],
                    'title': file_info['title'],
                    'full_path': str(file_path)
                }
            
            # Save to JSON file in the same directory
            mapping_file = download_path / 'url_mapping.json'
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(url_mapping, f, ensure_ascii=False, indent=2)
            
            logger.info(f"URL mapping saved to: {mapping_file}")
            return str(mapping_file)
            
        except Exception as e:
            logger.error(f"Failed to save URL mapping: {e}")
            return ""