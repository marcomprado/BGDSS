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
        '--disable-javascript',
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
        '--disable-ipc-flooding-protection'
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
        default_dir = str(Path(__file__).parent.parent / 'downloads' / 'raw')
        return getattr(settings, 'DOWNLOAD_DIR', default_dir)
    
    def _detect_driver_path(self, browser: str) -> Optional[str]:
        """Detecta automaticamente o path do driver."""
        try:
            if browser == 'chrome':
                return ChromeDriverManager().install()
            elif browser == 'firefox':
                return GeckoDriverManager().install()
        except Exception as e:
            print(f"Erro ao detectar driver path: {e}")
            return None
    
    def _get_user_agent(self, agent_type: str = 'default') -> str:
        """Obtém user agent baseado no tipo solicitado."""
        return self.USER_AGENTS.get(agent_type, self.USER_AGENTS['default'])
    
    def _create_chrome_options(self, **kwargs) -> ChromeOptions:
        """Cria opções personalizadas para Chrome."""
        options = ChromeOptions()
        
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
    
    def _create_chrome_driver(self, **kwargs) -> webdriver.Chrome:
        """Cria driver do Chrome."""
        options = self._create_chrome_options(**kwargs)
        
        # Service configuration
        driver_path = kwargs.get('driver_path') or self._detect_driver_path('chrome')
        service = None
        if driver_path:
            service = ChromeService(driver_path)
        
        driver = webdriver.Chrome(service=service, options=options)
        
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