"""
TerminalInterface - Interface Principal do Terminal com Progress Bars e Feedback Visual

FUNCIONALIDADE:
    Interface avançada de terminal que fornece feedback visual rico, progress bars animadas,
    tratamento de interrupções e experiência de usuário profissional. Combina funcionalidades
    do menu system com elementos visuais avançados para operações longas.

RESPONSABILIDADES:
    - Interface principal do terminal com feedback visual avançado
    - Progress bars animadas e indicadores de status em tempo real
    - Tratamento robusto de interrupções (Ctrl+C, sinais do sistema)
    - Dashboard de monitoramento em tempo real
    - Notificações e alertas visuais
    - Logs em tempo real com colorização

INTEGRAÇÃO NO SISTEMA:
    - Usa MenuSystem como base para navegação
    - Integra com ScraperEngine para progress tracking
    - Conecta com FileManager para operações de arquivo
    - Interface com Application para status global
    - Suporte a operações assíncronas e multi-threading

PADRÕES DE DESIGN:
    - Observer Pattern: Observa progresso de operações
    - Command Pattern: Comandos de terminal como objetos
    - State Pattern: Estados da interface (idle, working, monitoring)
    - Facade Pattern: Interface simplificada para operações complexas

CARACTERÍSTICAS TÉCNICAS:
    - Progress bars customizáveis com múltiplos estilos
    - Animações ASCII para loading
    - Detecção automática de capabilities do terminal
    - Suporte a cores e estilos avançados
    - Tratamento gracioso de redimensionamento
"""

import sys
import os
import time
import threading
import signal
import queue
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import shutil

try:
    import psutil
    SYSTEM_MONITORING = True
except ImportError:
    SYSTEM_MONITORING = False

try:
    from rich.console import Console
    from rich.progress import (
        Progress, TaskID, BarColumn, TextColumn, 
        TimeElapsedColumn, TimeRemainingColumn,
        MofNCompleteColumn, SpinnerColumn
    )
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from src.ui.menu_system import MenuSystem, Menu, MenuItem, MenuItemType, MenuTheme, MenuStyle
from src.utils.logger import logger


class ProgressBarStyle(Enum):
    """Estilos de progress bar disponíveis."""
    SIMPLE = "simple"
    DETAILED = "detailed"
    MINIMAL = "minimal"
    ANIMATED = "animated"
    SPINNER = "spinner"


class TerminalState(Enum):
    """Estados da interface de terminal."""
    IDLE = "idle"
    MENU = "menu"
    WORKING = "working"
    MONITORING = "monitoring"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class ProgressTask:
    """Tarefa com progresso rastreável."""
    task_id: str
    title: str
    total: int
    current: int = 0
    status: str = "running"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def progress_percent(self) -> float:
        """Calcula porcentagem de progresso."""
        return (self.current / self.total * 100) if self.total > 0 else 0.0
    
    @property
    def elapsed_time(self) -> timedelta:
        """Tempo decorrido."""
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    @property
    def estimated_remaining(self) -> Optional[timedelta]:
        """Tempo estimado restante."""
        if self.current == 0 or self.total == 0:
            return None
        
        elapsed = self.elapsed_time.total_seconds()
        rate = self.current / elapsed
        remaining_items = self.total - self.current
        
        if rate > 0:
            return timedelta(seconds=remaining_items / rate)
        return None


class ProgressBarRenderer:
    """Renderizador de progress bars para terminal."""
    
    def __init__(self, width: int = 50):
        self.width = width
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_index = 0
        
    def render_simple(self, task: ProgressTask) -> str:
        """Renderiza progress bar simples."""
        percent = task.progress_percent
        filled = int(self.width * percent / 100)
        bar = '█' * filled + '░' * (self.width - filled)
        
        return f"{task.title}: [{bar}] {percent:.1f}% ({task.current}/{task.total})"
    
    def render_detailed(self, task: ProgressTask) -> str:
        """Renderiza progress bar detalhada."""
        percent = task.progress_percent
        filled = int(self.width * percent / 100)
        bar = '█' * filled + '░' * (self.width - filled)
        
        elapsed = task.elapsed_time
        remaining = task.estimated_remaining
        remaining_str = f" | ETA: {remaining}" if remaining else ""
        
        return (f"{task.title}\n"
                f"[{bar}] {percent:.1f}%\n"
                f"Progress: {task.current}/{task.total} | "
                f"Elapsed: {elapsed}{remaining_str}")
    
    def render_minimal(self, task: ProgressTask) -> str:
        """Renderiza progress bar minimalista."""
        percent = task.progress_percent
        return f"{task.title}: {percent:.0f}% ({task.current}/{task.total})"
    
    def render_animated(self, task: ProgressTask) -> str:
        """Renderiza progress bar com animação."""
        percent = task.progress_percent
        filled = int(self.width * percent / 100)
        
        # Animated fill character
        if filled < self.width and task.status == "running":
            animation_char = '▶' if filled > 0 else '▷'
            bar = '█' * (filled - 1) + animation_char + '░' * (self.width - filled)
        else:
            bar = '█' * filled + '░' * (self.width - filled)
        
        return f"{task.title}: [{bar}] {percent:.1f}%"
    
    def render_spinner(self, task: ProgressTask) -> str:
        """Renderiza spinner animado."""
        if task.status == "running":
            spinner = self.spinner_chars[self.spinner_index % len(self.spinner_chars)]
            self.spinner_index += 1
        else:
            spinner = '✓' if task.status == "completed" else '✗'
        
        return f"{spinner} {task.title}: {task.current}/{task.total}"


class SystemMonitor:
    """Monitor de recursos do sistema."""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'disk_usage': 0.0,
            'network_io': {'bytes_sent': 0, 'bytes_recv': 0}
        }
    
    def start_monitoring(self):
        """Inicia monitoramento de recursos."""
        if not SYSTEM_MONITORING:
            return
        
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        """Para monitoramento de recursos."""
        self.monitoring = False
    
    def _monitor_loop(self):
        """Loop principal de monitoramento."""
        while self.monitoring:
            try:
                if SYSTEM_MONITORING:
                    self.stats['cpu_percent'] = psutil.cpu_percent(interval=1)
                    self.stats['memory_percent'] = psutil.virtual_memory().percent
                    self.stats['disk_usage'] = psutil.disk_usage('/').percent
                    
                    net_io = psutil.net_io_counters()
                    self.stats['network_io'] = {
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv
                    }
                
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas atuais."""
        return self.stats.copy()


class LogViewer:
    """Visualizador de logs em tempo real."""
    
    def __init__(self, max_lines: int = 20):
        self.max_lines = max_lines
        self.log_lines: List[Tuple[datetime, str, str]] = []  # timestamp, level, message
        self.lock = threading.Lock()
    
    def add_log(self, level: str, message: str):
        """Adiciona linha de log."""
        with self.lock:
            self.log_lines.append((datetime.now(), level, message))
            
            # Keep only recent logs
            if len(self.log_lines) > self.max_lines:
                self.log_lines = self.log_lines[-self.max_lines:]
    
    def get_formatted_logs(self) -> List[str]:
        """Retorna logs formatados."""
        with self.lock:
            formatted = []
            for timestamp, level, message in self.log_lines:
                time_str = timestamp.strftime("%H:%M:%S")
                
                # Color by level
                if level == "ERROR":
                    color = "\033[31m"  # Red
                elif level == "WARNING":
                    color = "\033[33m"  # Yellow
                elif level == "INFO":
                    color = "\033[32m"  # Green
                elif level == "DEBUG":
                    color = "\033[36m"  # Cyan
                else:
                    color = "\033[37m"  # White
                
                formatted.append(f"{color}[{time_str}] {level}: {message}\033[0m")
            
            return formatted


class TerminalInterface:
    """
    Interface principal do terminal com funcionalidades avançadas.
    
    Combina menu system, progress tracking, monitoring e feedback visual.
    """
    
    def __init__(self, app_reference=None, theme: MenuTheme = MenuTheme.DEFAULT):
        self.app = app_reference
        self.theme = theme
        self.menu_system = MenuSystem(theme)
        self.state = TerminalState.IDLE
        
        # Progress tracking
        self.progress_tasks: Dict[str, ProgressTask] = {}
        self.progress_renderer = ProgressBarRenderer()
        self.active_progress_style = ProgressBarStyle.DETAILED
        
        # Monitoring
        self.system_monitor = SystemMonitor()
        self.log_viewer = LogViewer()
        
        # Terminal capabilities
        self.terminal_width = self._get_terminal_width()
        self.terminal_height = self._get_terminal_height()
        self.supports_color = self._supports_color()
        
        # Rich console if available
        if RICH_AVAILABLE:
            self.console = Console()
            self.rich_progress = None
        
        # Signal handlers
        self._setup_signal_handlers()
        
        # State management
        self.running = False
        self.interrupted = False
        self.shutdown_requested = False
    
    def _get_terminal_width(self) -> int:
        """Obtém largura do terminal."""
        return shutil.get_terminal_size().columns
    
    def _get_terminal_height(self) -> int:
        """Obtém altura do terminal."""
        return shutil.get_terminal_size().lines
    
    def _supports_color(self) -> bool:
        """Verifica se terminal suporta cores."""
        return (hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and 
                os.getenv('TERM') != 'dumb')
    
    def _setup_signal_handlers(self):
        """Configura handlers para sinais do sistema."""
        def signal_handler(signum, frame):
            self.handle_interrupt(signum)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Handle window resize
        if hasattr(signal, 'SIGWINCH'):
            signal.signal(signal.SIGWINCH, self._handle_resize)
    
    def _handle_resize(self, signum, frame):
        """Trata redimensionamento do terminal."""
        self.terminal_width = self._get_terminal_width()
        self.terminal_height = self._get_terminal_height()
        
        # Update progress bar width
        self.progress_renderer.width = min(50, self.terminal_width - 20)
    
    def handle_interrupt(self, signum: int):
        """Trata interrupções do usuário."""
        self.interrupted = True
        
        if signum == signal.SIGINT:
            self.show_message("🛑 Interrupção detectada (Ctrl+C)", "warning")
        elif signum == signal.SIGTERM:
            self.show_message("🛑 Sinal de término recebido", "warning")
        
        if self.state == TerminalState.WORKING:
            self.show_message("⏸️ Aguardando finalização de tarefas ativas...", "info")
            self.shutdown_requested = True
        else:
            self.shutdown_gracefully()
    
    def shutdown_gracefully(self):
        """Desliga interface graciosamente."""
        self.state = TerminalState.SHUTTING_DOWN
        self.running = False
        
        # Stop monitoring
        self.system_monitor.stop_monitoring()
        
        # Cancel active progress tasks
        for task in self.progress_tasks.values():
            if task.status == "running":
                task.status = "cancelled"
                task.end_time = datetime.now()
        
        self.show_message("👋 Interface encerrada graciosamente", "success")
    
    def start(self) -> Dict[str, Any]:
        """Inicia interface do terminal."""
        self.running = True
        self.state = TerminalState.IDLE
        
        try:
            # Start system monitoring
            self.system_monitor.start_monitoring()
            
            # Show welcome
            self.show_welcome()
            
            # Create and run main menu
            main_menu = self.create_main_menu()
            result = self.menu_system.run(main_menu)
            
            return result
            
        except KeyboardInterrupt:
            logger.info("Terminal interface interrupted")
            return {'interrupted': True}
        except Exception as e:
            logger.error(f"Terminal interface error: {e}")
            self.show_error(f"Erro na interface: {e}")
            return {'error': str(e)}
        finally:
            self.shutdown_gracefully()
    
    def show_welcome(self):
        """Mostra tela de boas-vindas."""
        self.clear_screen()
        
        welcome_text = """
╔══════════════════════════════════════════════════════════════╗
║                    🤖 WEB SCRAPER AI                         ║
║              Sistema Avançado de Web Scraping               ║
╚══════════════════════════════════════════════════════════════╝

🚀 Sistema inicializado com sucesso!
🔧 Interface de terminal avançada ativa
📊 Monitoramento de sistema habilitado
⚡ Pronto para operações de scraping

        """
        
        self.show_message(welcome_text, "info")
        
        # Show system status
        if self.app:
            try:
                status = self.app.get_application_status()
                health = self.app.health_check()
                
                print("📋 Status do Sistema:")
                print(f"   ✅ Aplicação: {'Executando' if status['running'] else 'Parada'}")
                print(f"   🌐 Sites configurados: {status['site_configs_loaded']}")
                print(f"   🏥 Saúde geral: {health['status'].upper()}")
                
            except Exception as e:
                logger.warning(f"Could not get app status: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def create_main_menu(self) -> Menu:
        """Cria menu principal da aplicação."""
        menu = Menu("🤖 Web Scraper AI - Menu Principal", 
                   "Sistema avançado de web scraping com IA")
        
        # Status and monitoring
        menu.add_separator("📊 Monitoramento")
        menu.add_action("status", "📈 Status da Aplicação", self.show_application_status)
        menu.add_action("health", "🏥 Verificação de Saúde", self.show_health_check)
        menu.add_action("metrics", "📊 Métricas de Performance", self.show_metrics)
        menu.add_action("system", "💻 Monitor do Sistema", self.show_system_monitor)
        
        # Scraping operations
        menu.add_separator("🕸️ Operações de Scraping")
        menu.add_action("create_task", "🚀 Criar Tarefa de Scraping", self.create_scraping_task)
        menu.add_action("list_tasks", "📋 Listar Tarefas", self.list_tasks)
        menu.add_action("monitor_tasks", "👁️ Monitorar Tarefas", self.monitor_tasks_live)
        
        # Configuration
        menu.add_separator("⚙️ Configuração")
        menu.add_submenu("settings", "🔧 Configurações", self.create_settings_menu())
        menu.add_action("logs", "📜 Visualizar Logs", self.show_logs)
        
        # Maintenance
        menu.add_separator("🛠️ Manutenção")
        menu.add_action("backup", "💾 Criar Backup", self.create_backup)
        menu.add_action("cleanup", "🧹 Limpeza do Sistema", self.cleanup_system)
        
        # Exit
        menu.add_separator()
        menu.add_exit("🚪 Sair")
        
        return menu
    
    def create_settings_menu(self) -> Menu:
        """Cria menu de configurações."""
        from src.ui.menu_system import create_settings_menu, InputValidator, InputType
        
        menu = create_settings_menu()
        
        # Add interface-specific settings
        menu.add_input(
            "progress_style",
            "Estilo de Progress Bar",
            InputType.CHOICE,
            choices=["simple", "detailed", "minimal", "animated", "spinner"],
            default_value="detailed"
        )
        
        menu.add_input(
            "terminal_theme",
            "Tema do Terminal",
            InputType.CHOICE,
            choices=["default", "dark", "light", "colorful", "minimal"],
            default_value="default"
        )
        
        menu.add_toggle("enable_monitoring", "Monitoramento de Sistema", default_value=True)
        menu.add_toggle("show_animations", "Animações", default_value=True)
        
        return menu
    
    # Action methods
    def show_application_status(self):
        """Mostra status detalhado da aplicação."""
        if not self.app:
            self.show_error("Aplicação não disponível")
            return
        
        try:
            status = self.app.get_application_status()
            
            self.clear_screen()
            print("📊 STATUS DA APLICAÇÃO")
            print("=" * 60)
            
            # Basic status
            print(f"🔧 Inicializada: {'✅ Sim' if status['initialized'] else '❌ Não'}")
            print(f"▶️  Executando: {'✅ Sim' if status['running'] else '❌ Não'}")
            print(f"🌐 Sites configurados: {status['site_configs_loaded']}")
            
            # Engine status
            if status.get('engine_status'):
                engine = status['engine_status']
                print(f"\n⚙️ STATUS DO MOTOR:")
                print(f"   Status: {engine['status']}")
                print(f"   Tarefas ativas: {engine['active_tasks']}")
                print(f"   Fila: {engine['queue_size']}")
                print(f"   Completadas: {engine['completed_tasks']}")
            
            # Components
            components = status.get('components', {})
            print(f"\n🔧 COMPONENTES:")
            for comp_name, available in components.items():
                icon = "✅" if available else "❌"
                name = comp_name.replace('_', ' ').title()
                print(f"   {icon} {name}")
            
            input("\nPressione Enter para continuar...")
            
        except Exception as e:
            self.show_error(f"Erro ao obter status: {e}")
    
    def show_health_check(self):
        """Mostra verificação de saúde."""
        if not self.app:
            self.show_error("Aplicação não disponível")
            return
        
        try:
            # Show progress while checking
            progress_id = self.start_progress("health_check", "Verificando saúde do sistema...", 4)
            
            self.update_progress(progress_id, 1, "Verificando componentes...")
            time.sleep(0.5)
            
            health = self.app.health_check()
            
            self.update_progress(progress_id, 2, "Analisando conectividade...")
            time.sleep(0.5)
            
            self.update_progress(progress_id, 3, "Verificando recursos...")
            time.sleep(0.5)
            
            self.update_progress(progress_id, 4, "Concluído!")
            self.complete_progress(progress_id)
            
            # Show results
            self.clear_screen()
            print("🏥 VERIFICAÇÃO DE SAÚDE")
            print("=" * 60)
            
            overall_icon = "✅" if health['status'] == 'healthy' else "❌"
            print(f"{overall_icon} Status Geral: {health['status'].upper()}")
            print(f"🕐 Verificado em: {health['timestamp']}")
            
            if 'components' in health:
                print(f"\n🔧 SAÚDE DOS COMPONENTES:")
                for comp_name, info in health['components'].items():
                    status_icon = "✅" if info.get('healthy', True) else "❌"
                    comp_display = comp_name.replace('_', ' ').title()
                    status_text = info.get('status', 'unknown')
                    print(f"   {status_icon} {comp_display}: {status_text}")
            
            input("\nPressione Enter para continuar...")
            
        except Exception as e:
            self.show_error(f"Erro na verificação de saúde: {e}")
    
    def show_metrics(self):
        """Mostra métricas de performance."""
        if not self.app:
            self.show_error("Aplicação não disponível")
            return
        
        try:
            metrics = self.app.get_metrics()
            
            self.clear_screen()
            print("📈 MÉTRICAS DE PERFORMANCE")
            print("=" * 60)
            
            if 'engine' in metrics:
                engine = metrics['engine']
                print(f"⚙️ MOTOR DE SCRAPING:")
                print(f"   ✅ Tarefas completadas: {engine.get('tasks_completed', 0)}")
                print(f"   ❌ Tarefas falharam: {engine.get('tasks_failed', 0)}")
                print(f"   📊 Taxa de sucesso: {engine.get('success_rate', 0):.2%}")
                print(f"   ⏱️  Tempo médio: {engine.get('average_task_time', 0):.2f}s")
                print(f"   🕐 Uptime: {engine.get('uptime_seconds', 0):.0f}s")
            
            if 'storage' in metrics:
                storage = metrics['storage']
                total_files = storage.get('total_files', 0)
                total_size_mb = storage.get('total_size', 0) / (1024 * 1024)
                print(f"\n💾 ARMAZENAMENTO:")
                print(f"   📁 Total de arquivos: {total_files}")
                print(f"   💿 Tamanho total: {total_size_mb:.2f} MB")
            
            # System metrics if available
            if SYSTEM_MONITORING:
                sys_stats = self.system_monitor.get_stats()
                print(f"\n💻 SISTEMA:")
                print(f"   🖥️  CPU: {sys_stats['cpu_percent']:.1f}%")
                print(f"   🧠 Memória: {sys_stats['memory_percent']:.1f}%")
                print(f"   💾 Disco: {sys_stats['disk_usage']:.1f}%")
            
            input("\nPressione Enter para continuar...")
            
        except Exception as e:
            self.show_error(f"Erro ao obter métricas: {e}")
    
    def show_system_monitor(self):
        """Mostra monitor do sistema em tempo real."""
        if not SYSTEM_MONITORING:
            self.show_error("Monitoramento de sistema não disponível (psutil necessário)")
            return
        
        self.state = TerminalState.MONITORING
        
        try:
            print("💻 MONITOR DO SISTEMA EM TEMPO REAL")
            print("=" * 60)
            print("Pressione 'q' para sair ou Ctrl+C para interromper\n")
            
            while self.state == TerminalState.MONITORING and not self.interrupted:
                stats = self.system_monitor.get_stats()
                
                # Clear previous output (move cursor up)
                print("\033[4A", end="")
                
                # CPU bar
                cpu_bar = self._create_simple_bar(stats['cpu_percent'], 30)
                print(f"🖥️  CPU:     [{cpu_bar}] {stats['cpu_percent']:5.1f}%")
                
                # Memory bar
                mem_bar = self._create_simple_bar(stats['memory_percent'], 30)
                print(f"🧠 Memória: [{mem_bar}] {stats['memory_percent']:5.1f}%")
                
                # Disk bar
                disk_bar = self._create_simple_bar(stats['disk_usage'], 30)
                print(f"💾 Disco:   [{disk_bar}] {stats['disk_usage']:5.1f}%")
                
                print(f"📡 Rede:    ↑{stats['network_io']['bytes_sent']/1024/1024:.1f}MB "
                      f"↓{stats['network_io']['bytes_recv']/1024/1024:.1f}MB")
                
                # Check for quit command
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    char = sys.stdin.read(1)
                    if char.lower() == 'q':
                        break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.show_error(f"Erro no monitor: {e}")
        finally:
            self.state = TerminalState.IDLE
            print("\n\nMonitoramento encerrado.")
            input("Pressione Enter para continuar...")
    
    def _create_simple_bar(self, percent: float, width: int) -> str:
        """Cria barra simples para indicadores."""
        filled = int(width * percent / 100)
        return '█' * filled + '░' * (width - filled)
    
    def create_scraping_task(self):
        """Interface para criação de tarefa de scraping."""
        if not self.app:
            self.show_error("Aplicação não disponível")
            return
        
        try:
            # Get available sites
            site_configs = getattr(self.app, 'site_configs', {})
            if not site_configs:
                self.show_error("Nenhum site configurado disponível")
                return
            
            # Create selection menu
            site_menu = Menu("Selecionar Site para Scraping")
            site_menu.add_separator("Sites Disponíveis")
            
            for site_name, config in site_configs.items():
                description = getattr(config, 'description', 'Sem descrição')
                site_menu.add_action(
                    site_name, 
                    f"🌐 {config.name}", 
                    lambda s=site_name: self._create_task_for_site(s),
                    description=description
                )
            
            site_menu.add_separator()
            site_menu.add_back()
            
            self.menu_system.run(site_menu)
            
        except Exception as e:
            self.show_error(f"Erro ao criar tarefa: {e}")
    
    def _create_task_for_site(self, site_name: str):
        """Cria tarefa para site específico."""
        try:
            from src.models.scraping_task import TaskPriority
            
            # Create task with progress tracking
            progress_id = self.start_progress("create_task", f"Criando tarefa para {site_name}...", 3)
            
            self.update_progress(progress_id, 1, "Validando configuração...")
            time.sleep(0.5)
            
            task = self.app.create_scraping_task(site_name, TaskPriority.NORMAL)
            
            self.update_progress(progress_id, 2, "Adicionando à fila...")
            time.sleep(0.5)
            
            self.update_progress(progress_id, 3, "Tarefa criada com sucesso!")
            self.complete_progress(progress_id)
            
            self.show_success(f"✅ Tarefa criada: {task.task_id}")
            
        except Exception as e:
            self.show_error(f"Erro ao criar tarefa: {e}")
    
    def list_tasks(self):
        """Lista todas as tarefas."""
        if not self.app or not self.app.engine:
            self.show_error("Motor de scraping não disponível")
            return
        
        try:
            active_tasks = self.app.engine.get_active_tasks()
            completed_tasks = self.app.engine.get_completed_tasks()
            
            self.clear_screen()
            print("📋 LISTA DE TAREFAS")
            print("=" * 60)
            
            print(f"🔄 TAREFAS ATIVAS ({len(active_tasks)}):")
            if active_tasks:
                for task_id, task in list(active_tasks.items())[:10]:
                    status_icon = "🔄" if task.status.name == "IN_PROGRESS" else "⏸️"
                    print(f"   {status_icon} {task_id[:12]}... - {task.status.value}")
            else:
                print("   Nenhuma tarefa ativa")
            
            print(f"\n✅ TAREFAS COMPLETADAS ({len(completed_tasks)}):")
            if completed_tasks:
                for task_id, task in list(completed_tasks.items())[:10]:
                    status_icon = "✅" if task.status.name == "COMPLETED" else "❌"
                    completion_time = task.updated_at.strftime('%H:%M:%S')
                    print(f"   {status_icon} {task_id[:12]}... - {task.status.value} ({completion_time})")
            else:
                print("   Nenhuma tarefa completada")
            
            if len(active_tasks) + len(completed_tasks) > 20:
                print(f"\n... e mais {len(active_tasks) + len(completed_tasks) - 20} tarefas")
            
            input("\nPressione Enter para continuar...")
            
        except Exception as e:
            self.show_error(f"Erro ao listar tarefas: {e}")
    
    def monitor_tasks_live(self):
        """Monitora tarefas em tempo real."""
        if not self.app or not self.app.engine:
            self.show_error("Motor de scraping não disponível")
            return
        
        self.state = TerminalState.MONITORING
        
        try:
            print("👁️ MONITOR DE TAREFAS EM TEMPO REAL")
            print("=" * 60)
            print("Pressione 'q' para sair ou Ctrl+C para interromper\n")
            
            while self.state == TerminalState.MONITORING and not self.interrupted:
                active_tasks = self.app.engine.get_active_tasks()
                engine_status = self.app.engine.get_status()
                
                # Clear screen
                print("\033[2J\033[H", end="")
                
                print("👁️ MONITOR DE TAREFAS EM TEMPO REAL")
                print("=" * 60)
                
                # Engine status
                print(f"⚙️ Motor: {engine_status['status']}")
                print(f"🔄 Tarefas ativas: {engine_status['active_tasks']}")
                print(f"📦 Fila: {engine_status['queue_size']}")
                print(f"✅ Completadas: {engine_status['completed_tasks']}")
                print()
                
                # Active tasks
                if active_tasks:
                    print("🔄 TAREFAS ATIVAS:")
                    for task_id, task in list(active_tasks.items())[:5]:
                        elapsed = (datetime.now() - task.created_at).total_seconds()
                        print(f"   • {task_id[:12]}... - {task.status.value} ({elapsed:.0f}s)")
                else:
                    print("🔄 Nenhuma tarefa ativa")
                
                print(f"\n⏰ Atualizado: {datetime.now().strftime('%H:%M:%S')}")
                print("Pressione 'q' para sair...")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.show_error(f"Erro no monitor: {e}")
        finally:
            self.state = TerminalState.IDLE
            print("\n\nMonitoramento encerrado.")
            input("Pressione Enter para continuar...")
    
    def show_logs(self):
        """Mostra logs em tempo real."""
        self.clear_screen()
        print("📜 LOGS DO SISTEMA")
        print("=" * 60)
        
        logs = self.log_viewer.get_formatted_logs()
        if logs:
            for log_line in logs:
                print(log_line)
        else:
            print("Nenhum log recente disponível")
        
        input("\nPressione Enter para continuar...")
    
    def create_backup(self):
        """Cria backup do sistema."""
        if not self.app:
            self.show_error("Aplicação não disponível")
            return
        
        try:
            # Get backup description
            description = input("📝 Descrição do backup (opcional): ").strip()
            if not description:
                description = f"Backup manual - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Create backup with progress
            progress_id = self.start_progress("backup", "Criando backup do sistema...", 5)
            
            self.update_progress(progress_id, 1, "Preparando backup...")
            time.sleep(0.5)
            
            self.update_progress(progress_id, 2, "Copiando dados...")
            time.sleep(1)
            
            backup_info = self.app.create_backup(description)
            
            self.update_progress(progress_id, 3, "Comprimindo arquivos...")
            time.sleep(1)
            
            self.update_progress(progress_id, 4, "Finalizando...")
            time.sleep(0.5)
            
            self.update_progress(progress_id, 5, "Backup criado com sucesso!")
            self.complete_progress(progress_id)
            
            # Show backup info
            self.clear_screen()
            print("💾 BACKUP CRIADO COM SUCESSO")
            print("=" * 60)
            print(f"🆔 ID do Backup: {backup_info['backup_id']}")
            print(f"📁 Arquivos: {backup_info['file_count']}")
            print(f"💿 Tamanho: {backup_info['total_size'] / (1024*1024):.2f} MB")
            print(f"📅 Criado em: {backup_info['created_at']}")
            
            input("\nPressione Enter para continuar...")
            
        except Exception as e:
            self.show_error(f"Erro ao criar backup: {e}")
    
    def cleanup_system(self):
        """Realiza limpeza do sistema."""
        if not self.app:
            self.show_error("Aplicação não disponível")
            return
        
        try:
            # Confirm cleanup
            confirm = input("🧹 Deseja realizar limpeza do sistema? (s/N): ").strip().lower()
            if confirm not in ['s', 'sim', 'y', 'yes']:
                return
            
            # Cleanup with progress
            progress_id = self.start_progress("cleanup", "Realizando limpeza do sistema...", 4)
            
            self.update_progress(progress_id, 1, "Limpando arquivos temporários...")
            time.sleep(1)
            
            results = self.app.cleanup_old_data()
            
            self.update_progress(progress_id, 2, "Arquivando dados antigos...")
            time.sleep(1)
            
            self.update_progress(progress_id, 3, "Otimizando storage...")
            time.sleep(1)
            
            self.update_progress(progress_id, 4, "Limpeza concluída!")
            self.complete_progress(progress_id)
            
            # Show results
            self.clear_screen()
            print("🧹 LIMPEZA CONCLUÍDA")
            print("=" * 60)
            
            if 'temp_cleanup' in results:
                temp = results['temp_cleanup']
                print(f"🗑️  Arquivos temporários: {temp.get('deleted_files', 0)} removidos")
                print(f"💾 Espaço liberado: {temp.get('freed_bytes', 0) / (1024*1024):.2f} MB")
            
            if 'archive' in results:
                archive = results['archive']
                print(f"📦 Arquivos arquivados: {archive.get('archived_files', 0)}")
            
            if 'old_tasks_removed' in results:
                print(f"🗂️  Tarefas antigas removidas: {results['old_tasks_removed']}")
            
            input("\nPressione Enter para continuar...")
            
        except Exception as e:
            self.show_error(f"Erro na limpeza: {e}")
    
    # Progress tracking methods
    def start_progress(self, task_id: str, title: str, total: int) -> str:
        """Inicia nova tarefa com progresso."""
        task = ProgressTask(task_id, title, total)
        self.progress_tasks[task_id] = task
        
        self.state = TerminalState.WORKING
        return task_id
    
    def update_progress(self, task_id: str, current: int, status: str = "running"):
        """Atualiza progresso de tarefa."""
        if task_id in self.progress_tasks:
            task = self.progress_tasks[task_id]
            task.current = current
            task.status = status
            
            # Render progress bar
            if self.active_progress_style == ProgressBarStyle.SIMPLE:
                bar = self.progress_renderer.render_simple(task)
            elif self.active_progress_style == ProgressBarStyle.DETAILED:
                bar = self.progress_renderer.render_detailed(task)
            elif self.active_progress_style == ProgressBarStyle.MINIMAL:
                bar = self.progress_renderer.render_minimal(task)
            elif self.active_progress_style == ProgressBarStyle.ANIMATED:
                bar = self.progress_renderer.render_animated(task)
            else:
                bar = self.progress_renderer.render_spinner(task)
            
            # Clear previous line and print new progress
            print(f"\r{bar}", end="", flush=True)
    
    def complete_progress(self, task_id: str):
        """Completa tarefa de progresso."""
        if task_id in self.progress_tasks:
            task = self.progress_tasks[task_id]
            task.status = "completed"
            task.end_time = datetime.now()
            task.current = task.total
            
            # Final progress bar
            print(f"\r✅ {task.title} - Concluído!")
            print()  # New line
            
            # Clean up completed task after a moment
            threading.Timer(5.0, lambda: self.progress_tasks.pop(task_id, None)).start()
    
    # Utility methods
    def clear_screen(self):
        """Limpa a tela."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_message(self, message: str, msg_type: str = "info"):
        """Mostra mensagem formatada."""
        if msg_type == "error":
            print(f"\033[31m❌ {message}\033[0m")
        elif msg_type == "warning":
            print(f"\033[33m⚠️ {message}\033[0m")
        elif msg_type == "success":
            print(f"\033[32m✅ {message}\033[0m")
        else:
            print(f"\033[36mℹ️ {message}\033[0m")
    
    def show_error(self, message: str):
        """Mostra mensagem de erro."""
        self.show_message(message, "error")
        input("Pressione Enter para continuar...")
    
    def show_success(self, message: str):
        """Mostra mensagem de sucesso."""
        self.show_message(message, "success")
        time.sleep(1.5)


# Support for non-rich environments
try:
    import select
except ImportError:
    # Fallback for systems without select
    class select:
        @staticmethod
        def select(rlist, wlist, xlist, timeout):
            return [], [], []


# Export principais
__all__ = [
    'TerminalInterface', 'ProgressBarStyle', 'TerminalState',
    'ProgressTask', 'ProgressBarRenderer', 'SystemMonitor', 'LogViewer'
]