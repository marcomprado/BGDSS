"""
WebDriver Configuration Module

FUNCIONALIDADE:
    Módulo responsável pela configuração automática do WebDriver Selenium.
    Gerencia opções do navegador, profiles customizados e configurações específicas
    para diferentes tipos de scraping.

RESPONSABILIDADES:
    - Configuração automática do Chrome/Firefox WebDriver
    - Gerenciamento de opções do navegador (headless, user-agent, etc.)
    - Configuração de profiles customizados
    - Detecção automática de driver paths
    - Configurações anti-detecção para web scraping

INTEGRAÇÃO NO SISTEMA:
    - Usado por selenium_scraper.py para inicializar WebDriver
    - Integrado com settings.py para configurações globais
    - Suporte a diferentes navegadores e plataformas

PADRÕES DE DESIGN:
    - Factory Pattern: Criação de diferentes tipos de WebDriver
    - Configuration Pattern: Centralização de configurações
    - Builder Pattern: Construção incremental de opções
"""

import os
import platform
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from .settings import settings
from src.utils.resource_utils import get_bundled_driver_path, is_frozen


class ChromeDriverWithCleanup(webdriver.Chrome):
    """Chrome WebDriver with automatic cleanup of temporary user data directory."""
    
    def __init__(self, *args, **kwargs):
        self._temp_user_data_dir = kwargs.pop('temp_user_data_dir', None)
        super().__init__(*args, **kwargs)
    
    def quit(self):
        """Override quit to include cleanup."""
        try:
            super().quit()
        finally:
            self._cleanup_temp_directory()
    
    def _cleanup_temp_directory(self):
        """Clean up the temporary user data directory."""
        if self._temp_user_data_dir:
            try:
                import shutil
                if os.path.exists(self._temp_user_data_dir):
                    shutil.rmtree(self._temp_user_data_dir, ignore_errors=True)
                    print(f"Cleaned up temporary Chrome profile: {self._temp_user_data_dir}")
                self._temp_user_data_dir = None
            except Exception as e:
                print(f"Warning: Could not clean up temporary directory {self._temp_user_data_dir}: {e}")


class WebDriverConfig:
    """Configurador principal do WebDriver."""
    
    # Configurações padrão para diferentes tipos de navegador
    DEFAULT_CHROME_OPTIONS = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-images',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-default-apps',
        '--disable-popup-blocking',
        '--disable-translate',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--disable-client-side-phishing-detection',
        '--disable-sync',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        # Memory management for stability
        '--memory-pressure-off',
        '--max_old_space_size=4096',
        '--disable-gpu-sandbox',
        '--no-zygote',
        # Specific fixes for problematic sites
        '--disable-features=VizDisplayCompositor',
        '--disable-software-rasterizer',
        '--disable-background-networking'
    ]
    
    DEFAULT_FIREFOX_OPTIONS = [
        '--no-sandbox',
        '--disable-dev-shm-usage'
    ]
    
    # User agents para diferentes tipos de scraping
    USER_AGENTS = {
        'default': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'mobile': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
        'tablet': 'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
        'linux': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    def __init__(self):
        self.browser_type = getattr(settings, 'BROWSER_TYPE', 'chrome').lower()
        self.headless = getattr(settings, 'HEADLESS_MODE', True)
        self.window_size = getattr(settings, 'WINDOW_SIZE', (1920, 1080))
        self.timeout = getattr(settings, 'WEBDRIVER_TIMEOUT', 30)
        self.download_dir = self._get_download_directory()
        
    def _get_download_directory(self) -> str:
        """Obtém o diretório de download configurado."""
        # Use the RAW_DOWNLOADS_DIR from settings (which now handles executable paths correctly)
        return str(settings.RAW_DOWNLOADS_DIR)
    
    def _detect_driver_path(self, browser: str) -> Optional[str]:
        """Detecta automaticamente o path do driver com suporte adequado para diferentes arquiteturas."""
        try:
            if browser == 'chrome':
                # First, try bundled driver for executables
                if is_frozen():
                    driver_names = ['chromedriver.exe', 'chromedriver']
                    for driver_name in driver_names:
                        bundled_driver = get_bundled_driver_path(driver_name)
                        if bundled_driver:
                            print(f"Using bundled ChromeDriver: {bundled_driver}")
                            return bundled_driver
                
                # Clear cache and force fresh download
                import os
                import platform
                import shutil
                
                # Detect system architecture
                machine = platform.machine().lower()
                system = platform.system().lower()
                
                print(f"Detected system: {system}, machine: {machine}")
                
                # Try system-installed driver first
                system_driver = shutil.which('chromedriver')
                if system_driver:
                    print(f"Using system ChromeDriver: {system_driver}")
                    return system_driver
                
                # Use ChromeDriverManager as fallback (avoid in frozen apps when possible)
                if not is_frozen():
                    manager = ChromeDriverManager()
                    
                    # Install and verify the driver
                    driver_path = manager.install()
                    
                    # Verify the driver is a valid executable binary
                    if self._is_valid_driver_binary(driver_path):
                        import stat
                        # Make sure it's executable
                        os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                        print(f"ChromeDriver installed at: {driver_path}")
                        return driver_path
                    else:
                        print(f"Invalid ChromeDriver binary at: {driver_path}")
                        # Try to find the actual binary in the directory
                        actual_binary = self._find_chromedriver_binary(driver_path)
                        if actual_binary:
                            print(f"Found actual ChromeDriver binary at: {actual_binary}")
                            return actual_binary
                        return None
                else:
                    print("Running as executable but no bundled ChromeDriver found")
                    return None
                    
            elif browser == 'firefox':
                # First, try bundled driver for executables
                if is_frozen():
                    driver_names = ['geckodriver.exe', 'geckodriver']
                    for driver_name in driver_names:
                        bundled_driver = get_bundled_driver_path(driver_name)
                        if bundled_driver:
                            print(f"Using bundled GeckoDriver: {bundled_driver}")
                            return bundled_driver
                
                # Try system-installed driver
                import shutil
                system_driver = shutil.which('geckodriver')
                if system_driver:
                    print(f"Using system GeckoDriver: {system_driver}")
                    return system_driver
                
                # Use GeckoDriverManager as fallback (avoid in frozen apps when possible)
                if not is_frozen():
                    manager = GeckoDriverManager(cache_valid_range=1)
                    driver_path = manager.install()
                    
                    if os.path.exists(driver_path):
                        import stat
                        os.chmod(driver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                        print(f"GeckoDriver installed at: {driver_path}")
                        return driver_path
                    else:
                        return None
                else:
                    print("Running as executable but no bundled GeckoDriver found")
                    return None
                    
        except Exception as e:
            print(f"Erro ao detectar driver path: {e}")
            # Try to find system-installed drivers as fallback
            import shutil
            
            if browser == 'chrome':
                system_driver = shutil.which('chromedriver')
                if system_driver:
                    print(f"Using system ChromeDriver: {system_driver}")
                    return system_driver
            elif browser == 'firefox':
                system_driver = shutil.which('geckodriver')
                if system_driver:
                    print(f"Using system GeckoDriver: {system_driver}")
                    return system_driver
            
            return None
    
    def _is_valid_driver_binary(self, driver_path: str) -> bool:
        """Check if the given path points to a valid executable binary."""
        if not os.path.exists(driver_path):
            return False
        
        # Check if it's a file (not directory)
        if not os.path.isfile(driver_path):
            return False
        
        # Check if it's executable
        if not os.access(driver_path, os.X_OK):
            return False
        
        # Check if it's not a text file (avoid THIRD_PARTY_NOTICES, etc.)
        try:
            with open(driver_path, 'rb') as f:
                # Read first few bytes to check if it's binary
                header = f.read(4)
                # On macOS, Mach-O binaries start with specific magic numbers
                # On Linux, ELF binaries start with \x7fELF
                if header.startswith(b'\x7fELF') or header.startswith(b'\xcf\xfa\xed\xfe') or header.startswith(b'\xce\xfa\xed\xfe'):
                    return True
                # Windows PE executables
                elif header.startswith(b'MZ'):
                    return True
                return False
        except (IOError, OSError):
            return False
    
    def _find_chromedriver_binary(self, base_path: str) -> Optional[str]:
        """Find the actual ChromeDriver binary in a directory structure."""
        import glob
        
        # If base_path is a file, check its parent directory
        if os.path.isfile(base_path):
            search_dir = os.path.dirname(base_path)
        else:
            search_dir = base_path
        
        # Common ChromeDriver binary names
        binary_names = ['chromedriver', 'chromedriver.exe']
        
        # Search in the directory and subdirectories
        for binary_name in binary_names:
            # Direct path
            direct_path = os.path.join(search_dir, binary_name)
            if self._is_valid_driver_binary(direct_path):
                return direct_path
            
            # Search in subdirectories (recursive up to 2 levels)
            pattern = os.path.join(search_dir, '*', binary_name)
            matches = glob.glob(pattern)
            for match in matches:
                if self._is_valid_driver_binary(match):
                    return match
            
            # Search deeper (2 levels)
            pattern = os.path.join(search_dir, '*', '*', binary_name)
            matches = glob.glob(pattern)
            for match in matches:
                if self._is_valid_driver_binary(match):
                    return match
        
        return None
    
    def _get_user_agent(self, agent_type: str = 'default') -> str:
        """Obtém user agent baseado no tipo solicitado."""
        return self.USER_AGENTS.get(agent_type, self.USER_AGENTS['default'])
    
    def _create_chrome_options(self, temp_user_data_dir: str = None, **kwargs) -> ChromeOptions:
        """Cria opções personalizadas para Chrome."""
        options = ChromeOptions()
        
        # Use provided temporary user data directory or create one
        if temp_user_data_dir:
            options.add_argument(f'--user-data-dir={temp_user_data_dir}')
        
        # Opções básicas
        for option in self.DEFAULT_CHROME_OPTIONS:
            options.add_argument(option)
        
        # Configurações específicas
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument(f'--window-size={self.window_size[0]},{self.window_size[1]}')
        
        # User Agent
        user_agent_type = kwargs.get('user_agent_type', 'default')
        options.add_argument(f'--user-agent={self._get_user_agent(user_agent_type)}')
        
        # Configurações de download
        prefs = {
            'download.default_directory': self.download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 2 if kwargs.get('disable_images', True) else 1
        }
        
        # JavaScript habilitado/desabilitado
        if not kwargs.get('javascript_enabled', True):
            prefs['profile.managed_default_content_settings.javascript'] = 2
        
        options.add_experimental_option('prefs', prefs)
        
        # Opções anti-detecção
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Configurações customizadas
        custom_options = kwargs.get('custom_options', [])
        for option in custom_options:
            options.add_argument(option)
        
        return options
    
    def _create_firefox_options(self, **kwargs) -> FirefoxOptions:
        """Cria opções personalizadas para Firefox."""
        options = FirefoxOptions()
        
        # Opções básicas
        for option in self.DEFAULT_FIREFOX_OPTIONS:
            options.add_argument(option)
        
        if self.headless:
            options.add_argument('--headless')
        
        # Configurações de profile
        profile = webdriver.FirefoxProfile()
        
        # Download settings
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.dir', self.download_dir)
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 
                             'application/pdf,application/octet-stream,text/csv')
        
        # JavaScript
        if not kwargs.get('javascript_enabled', True):
            profile.set_preference('javascript.enabled', False)
        
        # Images
        if kwargs.get('disable_images', True):
            profile.set_preference('permissions.default.image', 2)
        
        # User Agent
        user_agent_type = kwargs.get('user_agent_type', 'default')
        profile.set_preference('general.useragent.override', self._get_user_agent(user_agent_type))
        
        options.profile = profile
        
        return options
    
    def create_webdriver(self, browser: Optional[str] = None, **kwargs) -> webdriver.Remote:
        """
        Cria uma instância do WebDriver configurada.
        
        Args:
            browser: Tipo do navegador ('chrome' ou 'firefox')
            **kwargs: Opções adicionais de configuração
                - user_agent_type: Tipo de user agent
                - javascript_enabled: Habilitar JavaScript
                - disable_images: Desabilitar imagens
                - custom_options: Lista de opções customizadas
                - driver_path: Path customizado do driver
        
        Returns:
            Instância configurada do WebDriver
        """
        browser = browser or self.browser_type
        
        try:
            if browser == 'chrome':
                return self._create_chrome_driver(**kwargs)
            elif browser == 'firefox':
                return self._create_firefox_driver(**kwargs)
            else:
                raise ValueError(f"Navegador não suportado: {browser}")
                
        except Exception as e:
            print(f"Erro ao criar WebDriver: {e}")
            # Fallback para Chrome se Firefox falhar
            if browser == 'firefox':
                print("Tentando fallback para Chrome...")
                return self._create_chrome_driver(**kwargs)
            raise
    
    def _create_chrome_driver(self, **kwargs) -> ChromeDriverWithCleanup:
        """Cria driver do Chrome com cleanup automático e proteções para Windows."""
        import time
        
        # Create unique temporary user data directory with timestamp for better uniqueness
        timestamp = int(time.time() * 1000)  # milliseconds timestamp
        temp_user_data_dir = tempfile.mkdtemp(
            prefix=f'chrome_profile_{uuid.uuid4().hex[:8]}_{timestamp}_'
        )
        
        # Windows-specific optimizations
        if platform.system() == 'Windows':
            existing_custom_options = kwargs.get('custom_options', [])
            windows_options = [
                '--disable-dev-shm-usage',  # Essential for Windows stability
                '--disable-gpu-sandbox',    # Helps with Windows admin execution
                '--no-sandbox',            # Required when running as admin on Windows
                '--disable-software-rasterizer',  # Windows rendering optimization
            ]
            # Merge Windows options with existing custom options
            kwargs['custom_options'] = existing_custom_options + windows_options
        
        # Create Chrome options with temporary directory
        options = self._create_chrome_options(
            temp_user_data_dir=temp_user_data_dir,
            **kwargs
        )
        
        # Service configuration
        driver_path = kwargs.get('driver_path') or self._detect_driver_path('chrome')
        service = None
        if driver_path:
            service = ChromeService(driver_path)
        
        # Create driver with temporary directory for cleanup
        driver = ChromeDriverWithCleanup(
            service=service, 
            options=options,
            temp_user_data_dir=temp_user_data_dir
        )
        
        # Configurações pós-inicialização
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(10)
        
        # Script anti-detecção
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def _create_firefox_driver(self, **kwargs) -> webdriver.Firefox:
        """Cria driver do Firefox."""
        options = self._create_firefox_options(**kwargs)
        
        # Service configuration
        driver_path = kwargs.get('driver_path') or self._detect_driver_path('firefox')
        service = None
        if driver_path:
            service = FirefoxService(driver_path)
        
        driver = webdriver.Firefox(service=service, options=options)
        
        # Configurações pós-inicialização
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(10)
        
        return driver
    
    def create_mobile_driver(self, device_name: str = 'iPhone 12 Pro') -> webdriver.Chrome:
        """
        Cria WebDriver configurado para emular dispositivo móvel.
        
        Args:
            device_name: Nome do dispositivo para emular
        
        Returns:
            WebDriver configurado para mobile
        """
        options = ChromeOptions()
        
        # Configurações mobile
        mobile_emulation = {
            "deviceName": device_name
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        # Aplicar outras configurações padrão
        for option in self.DEFAULT_CHROME_OPTIONS:
            if '--window-size' not in option:  # Pular window size para mobile
                options.add_argument(option)
        
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument(f'--user-agent={self._get_user_agent("mobile")}')
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self.timeout)
        driver.implicitly_wait(10)
        
        return driver
    
    def get_profile_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna configurações pré-definidas para diferentes perfis de scraping.
        
        Returns:
            Dicionário com configurações de perfis
        """
        return {
            'fast_scraping': {
                'disable_images': True,
                'javascript_enabled': False,
                'user_agent_type': 'default',
                'custom_options': ['--aggressive-cache-discard', '--memory-pressure-off']
            },
            'comprehensive_scraping': {
                'disable_images': False,
                'javascript_enabled': True,
                'user_agent_type': 'default',
                'custom_options': ['--enable-features=NetworkService']
            },
            'government_sites': {
                'disable_images': False,
                'javascript_enabled': True,
                'user_agent_type': 'default',
                'custom_options': [
                    '--enable-features=NetworkService',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-gpu-sandbox',
                    '--memory-pressure-off',
                    '--max_old_space_size=4096',
                    '--disable-software-rasterizer',
                    '--no-zygote',
                    '--single-process'
                ]
            },
            'stealth_scraping': {
                'disable_images': True,
                'javascript_enabled': True,
                'user_agent_type': 'default',
                'custom_options': [
                    '--disable-blink-features=AutomationControlled',
                    '--exclude-switches=enable-automation',
                    '--disable-extensions-http-throttling'
                ]
            },
            'job_sites': {
                'disable_images': True,
                'javascript_enabled': True,
                'user_agent_type': 'default',
                'custom_options': ['--disable-web-security']
            },
            'ecommerce': {
                'disable_images': False,
                'javascript_enabled': True,
                'user_agent_type': 'default',
                'custom_options': ['--enable-features=NetworkService']
            }
        }


# Instância global do configurador
webdriver_config = WebDriverConfig()


def create_configured_driver(profile: str = 'default', **kwargs) -> webdriver.Remote:
    """
    Função conveniente para criar WebDriver com perfil específico.
    
    Args:
        profile: Nome do perfil de configuração
        **kwargs: Opções adicionais
    
    Returns:
        WebDriver configurado
    """
    profiles = webdriver_config.get_profile_configs()
    
    if profile in profiles:
        profile_config = profiles[profile]
        kwargs.update(profile_config)
    
    return webdriver_config.create_webdriver(**kwargs)


def get_available_profiles() -> List[str]:
    """Retorna lista de perfis disponíveis."""
    return list(webdriver_config.get_profile_configs().keys())


def validate_webdriver_setup() -> Dict[str, bool]:
    """
    Valida se o setup do WebDriver está funcionando.
    
    Returns:
        Dicionário com status de cada navegador
    """
    results = {}
    
    # Testar Chrome
    try:
        driver = webdriver_config.create_webdriver('chrome')
        driver.get('data:text/html,<html><body><h1>Test</h1></body></html>')
        driver.quit()
        results['chrome'] = True
    except Exception as e:
        print(f"Chrome setup failed: {e}")
        results['chrome'] = False
    
    # Testar Firefox
    try:
        driver = webdriver_config.create_webdriver('firefox')
        driver.get('data:text/html,<html><body><h1>Test</h1></body></html>')
        driver.quit()
        results['firefox'] = True
    except Exception as e:
        print(f"Firefox setup failed: {e}")
        results['firefox'] = False
    
    return results