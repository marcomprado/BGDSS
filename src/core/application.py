"""
WebScraperApplication - Orquestração Central do Sistema

FUNCIONALIDADE:
    Classe principal responsável pela coordenação e gerenciamento de todos os componentes
    do sistema Web Scraper AI. Implementa padrão Singleton para garantir instância única
    e fornece interface unificada para operações de scraping, IA e gerenciamento de dados.

RESPONSABILIDADES:
    - Inicialização e configuração de todos os componentes do sistema
    - Orquestração entre módulos de scraping, IA e processamento
    - Gerenciamento de ciclo de vida da aplicação (start/stop)
    - Coordenação de tarefas de scraping via ScraperEngine
    - Monitoramento de saúde e métricas do sistema
    - Operações de backup e manutenção

INTEGRAÇÃO NO SISTEMA:
    - Singleton: Instância única acessível globalmente
    - Coordena ScraperEngine (execução), FileManager (arquivos), AI components
    - Interface principal para UI modules (CLI, Interactive, Daemon)
    - Gerencia configurações de sites e tarefas de scraping

PADRÕES DE DESIGN:
    - Singleton: Instância única da aplicação
    - Facade: Interface simplificada para sistema complexo
    - Dependency Injection: Componentes injetados na inicialização
    - Observer: Monitoramento de status e eventos

COMPONENTES GERENCIADOS:
    - ScraperEngine: Motor de execução multi-threaded
    - FileManager: Gerenciamento de arquivos e backup
    - OpenAIClient: Integração com serviços de IA
    - NavigatorAgent: Navegação inteligente
    - PDFProcessorAgent: Processamento de PDFs
    - SiteFactory: Criação de módulos específicos por site
"""

import signal
import sys
import atexit
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json

from src.core.scraper_engine import ScraperEngine, EngineStatus
from src.core.file_manager import FileManager
from src.modules.site_factory import SiteFactory, factory as site_factory
from src.ai.openai_client import OpenAIClient
from src.ai.navigator_agent import NavigatorAgent
from src.ai.pdf_processor_agent import PDFProcessorAgent
from src.processors.csv_processor import CSVProcessor
from src.processors.pdf_processor import PDFProcessor
from src.processors.excel_generator import ExcelGenerator
from src.models.site_config import SiteConfig
from src.models.scraping_task import ScrapingTask, TaskPriority
from src.utils.logger import logger
from src.utils.exceptions import ConfigurationError, ScrapingError
from config.settings import settings


class WebScraperApplication:
    """
    Main application class that orchestrates all components.
    Provides a unified interface for the entire scraping system.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.is_initialized = False
        self.is_running = False
        
        # Core components
        self.engine: Optional[ScraperEngine] = None
        self.file_manager: Optional[FileManager] = None
        self.site_factory: Optional[SiteFactory] = None
        
        # AI components
        self.openai_client: Optional[OpenAIClient] = None
        self.navigator_agent: Optional[NavigatorAgent] = None
        self.pdf_processor_agent: Optional[PDFProcessorAgent] = None
        
        # Processors
        self.csv_processor: Optional[CSVProcessor] = None
        self.pdf_processor: Optional[PDFProcessor] = None
        self.excel_generator: Optional[ExcelGenerator] = None
        
        # Configuration and state
        self.site_configs: Dict[str, SiteConfig] = {}
        self.application_config: Dict[str, Any] = {}
        
        # Callbacks and hooks
        self.startup_hooks: List[Callable] = []
        self.shutdown_hooks: List[Callable] = []
        self.task_completion_hooks: List[Callable] = []
        
        logger.info("WebScraperApplication instance created")
    
    def initialize(self) -> None:
        """Initialize all application components."""
        if self.is_initialized:
            logger.warning("Application already initialized")
            return
        
        try:
            logger.info("Initializing Web Scraper AI Application...")
            
            self._validate_environment()
            
            self._load_application_config()
            
            self._initialize_core_components()
            
            self._initialize_ai_components()
            
            self._initialize_processors()
            
            self._load_site_configurations()
            
            self._setup_signal_handlers()
            
            self._register_cleanup_handlers()
            
            self._run_startup_hooks()
            
            self.is_initialized = True
            
            logger.info("Application initialized successfully")
            
        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            raise ConfigurationError(f"Initialization failed: {e}")
    
    def start(self) -> None:
        """Start the application and all its services."""
        if not self.is_initialized:
            self.initialize()
        
        if self.is_running:
            logger.warning("Application is already running")
            return
        
        try:
            logger.info("Starting Web Scraper AI Application...")
            
            self.engine.start()
            
            self._setup_engine_callbacks()
            
            self.is_running = True
            
            logger.info("Application started successfully")
            
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            raise ScrapingError(f"Startup failed: {e}")
    
    def stop(self, timeout: int = 30) -> None:
        """Stop the application gracefully."""
        if not self.is_running:
            return
        
        logger.info("Stopping Web Scraper AI Application...")
        
        try:
            if self.engine:
                self.engine.stop(timeout=timeout)
            
            self._run_shutdown_hooks()
            
            self.is_running = False
            
            logger.info("Application stopped successfully")
            
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
    
    def restart(self, timeout: int = 30) -> None:
        """Restart the application."""
        logger.info("Restarting application...")
        self.stop(timeout)
        self.start()
    
    def _validate_environment(self) -> None:
        """Validate environment and dependencies."""
        logger.info("Validating environment...")
        
        if not settings.OPENAI_API_KEY:
            raise ConfigurationError("OpenAI API key not configured")
        
        required_dirs = [
            settings.DOWNLOADS_DIR,
            settings.LOGS_DIR,
            settings.DRIVERS_DIR
        ]
        
        for directory in required_dirs:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
        
        try:
            from selenium import webdriver
            logger.debug("Selenium WebDriver available")
        except ImportError:
            raise ConfigurationError("Selenium WebDriver not available")
        
        logger.info("Environment validation completed")
    
    def _load_application_config(self) -> None:
        """Load application configuration."""
        config_file = self.config_path or (settings.BASE_DIR / 'config' / 'app_config.json')
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.application_config = json.load(f)
                logger.info(f"Loaded application config from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
                self.application_config = {}
        else:
            self.application_config = self._get_default_config()
            logger.info("Using default application configuration")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default application configuration."""
        return {
            'engine': {
                'max_workers': 3,
                'max_queue_size': 100,
                'task_timeout': 3600
            },
            'ai': {
                'enable_openai': True,
                'enable_navigator': True,
                'enable_pdf_processor': True
            },
            'file_management': {
                'auto_organize': True,
                'cleanup_temp_hours': 24,
                'archive_days': 90
            },
            'monitoring': {
                'enable_metrics': True,
                'log_level': 'INFO'
            }
        }
    
    def _initialize_core_components(self) -> None:
        """Initialize core application components."""
        logger.info("Initializing core components...")
        
        engine_config = self.application_config.get('engine', {})
        self.engine = ScraperEngine(
            max_workers=engine_config.get('max_workers', 3),
            max_queue_size=engine_config.get('max_queue_size', 100),
            task_timeout=engine_config.get('task_timeout', 3600)
        )
        
        self.file_manager = FileManager()
        
        self.site_factory = site_factory
        
        logger.info("Core components initialized")
    
    def _initialize_ai_components(self) -> None:
        """Initialize AI components."""
        logger.info("Initializing AI components...")
        
        ai_config = self.application_config.get('ai', {})
        
        if ai_config.get('enable_openai', True):
            try:
                self.openai_client = OpenAIClient()
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        
        if ai_config.get('enable_navigator', True):
            try:
                self.navigator_agent = NavigatorAgent(self.openai_client)
                logger.info("Navigator agent initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Navigator agent: {e}")
        
        if ai_config.get('enable_pdf_processor', True):
            try:
                self.pdf_processor_agent = PDFProcessorAgent(self.openai_client)
                logger.info("PDF processor agent initialized")
            except Exception as e:
                logger.error(f"Failed to initialize PDF processor agent: {e}")
        
        logger.info("AI components initialized")
    
    def _initialize_processors(self) -> None:
        """Initialize data processors."""
        logger.info("Initializing processors...")
        
        self.csv_processor = CSVProcessor()
        self.pdf_processor = PDFProcessor(use_ai=self.openai_client is not None)
        self.excel_generator = ExcelGenerator()
        
        logger.info("Processors initialized")
    
    def _load_site_configurations(self) -> None:
        """Load site configurations from config directory."""
        config_dir = settings.BASE_DIR / 'config' / 'sites'
        
        if not config_dir.exists():
            config_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created site configurations directory")
            return
        
        loaded_count = 0
        for config_file in config_dir.glob('*.json'):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                site_config = SiteConfig(**config_data)
                self.site_configs[site_config.name] = site_config
                loaded_count += 1
                
                logger.debug(f"Loaded site config: {site_config.name}")
                
            except Exception as e:
                logger.error(f"Failed to load site config {config_file}: {e}")
        
        logger.info(f"Loaded {loaded_count} site configurations")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _register_cleanup_handlers(self) -> None:
        """Register cleanup handlers."""
        atexit.register(self._cleanup_on_exit)
    
    def _cleanup_on_exit(self) -> None:
        """Cleanup function called on application exit."""
        if self.is_running:
            self.stop()
    
    def _setup_engine_callbacks(self) -> None:
        """Setup callbacks for the scraping engine."""
        self.engine.add_completion_callback(self._on_task_completion)
        self.engine.add_progress_callback(self._on_task_progress)
    
    def _on_task_completion(self, task: ScrapingTask) -> None:
        """Handle task completion."""
        logger.info(f"Task completed: {task.task_id}")
        
        for hook in self.task_completion_hooks:
            try:
                hook(task)
            except Exception as e:
                logger.error(f"Task completion hook failed: {e}")
        
        if self.application_config.get('file_management', {}).get('auto_organize', True):
            try:
                self.file_manager.organize_downloads(task.task_id)
            except Exception as e:
                logger.error(f"Failed to organize downloads for task {task.task_id}: {e}")
    
    def _on_task_progress(self, task: ScrapingTask) -> None:
        """Handle task progress updates."""
        logger.debug(f"Task progress: {task.task_id} - {task.get_progress_percentage()}%")
    
    def _run_startup_hooks(self) -> None:
        """Run all startup hooks."""
        for hook in self.startup_hooks:
            try:
                hook(self)
            except Exception as e:
                logger.error(f"Startup hook failed: {e}")
    
    def _run_shutdown_hooks(self) -> None:
        """Run all shutdown hooks."""
        for hook in self.shutdown_hooks:
            try:
                hook(self)
            except Exception as e:
                logger.error(f"Shutdown hook failed: {e}")
    
    # Public API methods
    
    def create_scraping_task(self,
                            site_name: str,
                            target_url: Optional[str] = None,
                            priority: TaskPriority = TaskPriority.NORMAL,
                            parameters: Optional[Dict[str, Any]] = None) -> ScrapingTask:
        """Create a new scraping task."""
        if site_name not in self.site_configs:
            raise ConfigurationError(f"Site configuration not found: {site_name}")
        
        site_config = self.site_configs[site_name]
        
        return self.engine.create_and_submit_task(
            site_config=site_config,
            target_url=target_url,
            priority=priority,
            parameters=parameters
        )
    
    def get_site_configs(self) -> Dict[str, SiteConfig]:
        """Get all loaded site configurations."""
        return self.site_configs.copy()
    
    def add_site_config(self, site_config: SiteConfig) -> None:
        """Add a new site configuration."""
        self.site_configs[site_config.name] = site_config
        logger.info(f"Added site configuration: {site_config.name}")
    
    def get_application_status(self) -> Dict[str, Any]:
        """Get comprehensive application status."""
        return {
            'initialized': self.is_initialized,
            'running': self.is_running,
            'engine_status': self.engine.get_engine_status() if self.engine else None,
            'site_configs_loaded': len(self.site_configs),
            'components': {
                'file_manager': self.file_manager is not None,
                'openai_client': self.openai_client is not None,
                'navigator_agent': self.navigator_agent is not None,
                'pdf_processor_agent': self.pdf_processor_agent is not None,
                'csv_processor': self.csv_processor is not None,
                'pdf_processor': self.pdf_processor is not None,
                'excel_generator': self.excel_generator is not None
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get application metrics."""
        metrics = {}
        
        if self.engine:
            metrics['engine'] = self.engine.get_metrics().to_dict()
        
        if self.file_manager:
            metrics['storage'] = self.file_manager.get_storage_statistics()
        
        metrics['application'] = {
            'uptime_seconds': (datetime.now() - self._start_time).total_seconds() if hasattr(self, '_start_time') else 0,
            'initialized': self.is_initialized,
            'running': self.is_running
        }
        
        return metrics
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Check engine
        if self.engine:
            engine_status = self.engine.status
            health['components']['engine'] = {
                'status': engine_status.value,
                'healthy': engine_status in [EngineStatus.RUNNING, EngineStatus.IDLE]
            }
        
        # Check OpenAI client
        if self.openai_client:
            try:
                openai_healthy = self.openai_client.check_health()
                health['components']['openai'] = {
                    'status': 'healthy' if openai_healthy else 'unhealthy',
                    'healthy': openai_healthy
                }
            except:
                health['components']['openai'] = {
                    'status': 'error',
                    'healthy': False
                }
        
        overall_healthy = all(
            comp.get('healthy', True) for comp in health['components'].values()
        )
        
        health['status'] = 'healthy' if overall_healthy else 'unhealthy'
        
        return health
    
    # Hook management
    
    def add_startup_hook(self, callback: Callable) -> None:
        """Add a startup hook."""
        self.startup_hooks.append(callback)
    
    def add_shutdown_hook(self, callback: Callable) -> None:
        """Add a shutdown hook."""
        self.shutdown_hooks.append(callback)
    
    def add_task_completion_hook(self, callback: Callable) -> None:
        """Add a task completion hook."""
        self.task_completion_hooks.append(callback)
    
    # Maintenance operations
    
    def cleanup_old_data(self) -> Dict[str, Any]:
        """Perform maintenance cleanup."""
        results = {}
        
        if self.file_manager:
            file_config = self.application_config.get('file_management', {})
            
            # Cleanup temp files
            temp_results = self.file_manager.cleanup_temp_files(
                max_age_hours=file_config.get('cleanup_temp_hours', 24)
            )
            results['temp_cleanup'] = temp_results
            
            # Archive old files
            archive_results = self.file_manager.archive_old_files(
                days_old=file_config.get('archive_days', 90)
            )
            results['archive'] = archive_results
        
        if self.engine:
            # Cleanup old tasks
            old_tasks_removed = self.engine.cleanup_old_tasks(days_old=7)
            results['old_tasks_removed'] = old_tasks_removed
        
        logger.info(f"Maintenance cleanup completed: {results}")
        return results
    
    def create_backup(self, description: str) -> Dict[str, Any]:
        """Create a system backup."""
        if not self.file_manager:
            raise ScrapingError("File manager not initialized")
        
        backup_info = self.file_manager.create_backup(
            description=description,
            tags=['system_backup', 'auto_generated']
        )
        
        return backup_info.to_dict()


# Global application instance
app = WebScraperApplication()