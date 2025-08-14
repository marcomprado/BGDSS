#!/usr/bin/env python3
"""
Portal Saude MG Terminal Interface

Interface específica para o Portal Saude MG com funcionalidades de seleção
de ano, mês e intervalos personalizados.
"""

import sys
import os
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from src.utils.logger import logger, set_context


class InteractiveProgressDisplay:
    """
    Interactive progress display with real-time updates.
    Features timer updates, loading animations, and progress counters.
    """
    
    def __init__(self, terminal_instance, config: Dict[str, Any]):
        self.terminal = terminal_instance
        self.config = config
        self.start_time = datetime.now()
        self.current_step = ""
        self.current_detail = ""
        self.steps_completed = []
        
        # Animation system
        self.animation_frames = ["   ", ".  ", ".. ", "..."]
        self.animation_index = 0
        self.last_animation_update = time.time()
        
        # Progress counters
        self.pdf_current = 0
        self.pdf_total = 0
        
        # Threading control
        self.running = False
        self.update_thread = None
        self.lock = threading.Lock()
        
        # Display state
        self.last_timer_line = ""
        self.timer_line_number = 7   # Line where timer is displayed (was 6, now corrected)
        self.steps_start_line = 10   # Line where steps start (was 9, now corrected) 
        self.first_render = False    # Flag to prevent updates before first render
        
    def start(self):
        """Start the real-time update thread."""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
    
    def stop(self):
        """Stop the real-time update thread."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
    
    def show_status(self, step: str, detail: str = "", completed_steps: List[str] = None):
        """Show current processing status with real-time updates."""
        with self.lock:
            self.current_step = step
            self.current_detail = detail
            if completed_steps:
                self.steps_completed = completed_steps
        
        # Full render only on step changes
        self._full_render()
    
    def set_pdf_progress(self, current: int, total: int):
        """Update PDF download progress counter."""
        with self.lock:
            self.pdf_current = current
            self.pdf_total = total
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in minutes since start."""
        elapsed = datetime.now() - self.start_time
        return elapsed.total_seconds() / 60
    
    def _update_loop(self):
        """Background thread for real-time updates."""
        while self.running:
            # Update timer every second
            self._update_timer()
            
            # Update animation every 0.5 seconds
            current_time = time.time()
            if current_time - self.last_animation_update >= 0.5:
                self._update_animation()
                self.last_animation_update = current_time
            
            time.sleep(0.5)
    
    def _update_timer(self):
        """Update only the timer line."""
        if not self.first_render:
            return  # Don't update before first render
            
        with self.lock:
            elapsed = datetime.now() - self.start_time
            total_minutes = elapsed.total_seconds() / 60
            new_timer_line = f"Tempo decorrido: {total_minutes:.1f} minutos"
            
            if new_timer_line != self.last_timer_line:
                # Move cursor to timer line and update
                print(f"\033[{self.timer_line_number};1H\033[K{new_timer_line}", end='', flush=True)
                # Move cursor to bottom to avoid interference
                print(f"\033[20;1H", end='', flush=True)
                self.last_timer_line = new_timer_line
    
    def _update_animation(self):
        """Update loading animations for active steps."""
        with self.lock:
            self.animation_index = (self.animation_index + 1) % len(self.animation_frames)
            
            # Update the current step line with animation
            if self.current_step:
                self._update_current_step_line()
    
    def _update_current_step_line(self):
        """Update only the line with the current active step."""
        if not self.first_render:
            return  # Don't update before first render
            
        all_steps = [
            "Conectando ao site",
            "Aplicando filtros", 
            "Carregando resultados",
            "Baixando PDFs",
            "Processamento AI",
            "Finalizando"
        ]
        
        if self.current_step in all_steps:
            step_index = all_steps.index(self.current_step)
            line_number = self.steps_start_line + step_index
            
            # Build the step line with animation
            animation = self.animation_frames[self.animation_index]
            step_line = f"⋯ {self.current_step}{animation}"
            
            # Add detail if available
            if self.current_detail:
                step_line += f" ({self.current_detail})"
            
            # Add PDF progress if applicable
            if self.current_step == "Baixando PDFs" and self.pdf_total > 0:
                step_line += f" ({self.pdf_current}/{self.pdf_total})"
            
            # Move cursor to step line and update
            print(f"\033[{line_number};1H\033[K{step_line}", end='', flush=True)
            # Move cursor to bottom to avoid interference
            print(f"\033[20;1H", end='', flush=True)
    
    def _full_render(self):
        """Render the complete interface."""
        self.terminal.clear_screen()
        print("========================================")
        print("         EM PROCESSAMENTO") 
        print("========================================")
        print("")
        
        # Show configuration summary
        config_summary = self._format_config()
        print(f"Configuração: {config_summary}")
        print("")
        
        # Show elapsed time (will be updated by thread)
        elapsed = datetime.now() - self.start_time
        total_minutes = elapsed.total_seconds() / 60
        self.last_timer_line = f"Tempo decorrido: {total_minutes:.1f} minutos"
        print(self.last_timer_line)
        print("")
        
        # Show process steps
        print("Etapas do processo:")
        
        all_steps = [
            "Conectando ao site",
            "Aplicando filtros",
            "Carregando resultados", 
            "Baixando PDFs",
            "Processamento AI",
            "Finalizando"
        ]
        
        for step_name in all_steps:
            if step_name in self.steps_completed:
                print(f"✓ {step_name}")
            elif step_name == self.current_step:
                # Initial render with animation
                animation = self.animation_frames[self.animation_index]
                step_line = f"⋯ {step_name}{animation}"
                if self.current_detail:
                    step_line += f" ({self.current_detail})"
                if step_name == "Baixando PDFs" and self.pdf_total > 0:
                    step_line += f" ({self.pdf_current}/{self.pdf_total})"
                print(step_line)
            else:
                print(f"  {step_name}")
        
        print("")
        print("Pressione Ctrl+C para cancelar")
        
        # Mark first render as complete and position cursor safely
        self.first_render = True
        print(f"\033[20;1H", end='', flush=True)  # Move cursor to bottom
    
    def _format_config(self) -> str:
        """Format configuration for display."""
        parts = []
        
        # Handle year
        if self.config.get('year_range'):
            start_year, end_year = self.config['year_range']
            parts.append(f"Anos: {start_year}-{end_year}")
        elif 'year' in self.config:
            if self.config['year'] == 999:
                parts.append("Ano: Todos")
            else:
                parts.append(f"Ano: {self.config['year']}")
        
        # Handle month
        if self.config.get('month_range'):
            start_month, end_month = self.config['month_range']
            months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            start_name = months[start_month - 1]
            end_name = months[end_month - 1]
            parts.append(f"Meses: {start_name}-{end_name}")
        elif 'month' in self.config:
            if self.config['month'] == 13:
                parts.append("Mês: Todos")
            elif 1 <= self.config['month'] <= 12:
                months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                parts.append(f"Mês: {months[self.config['month']-1]}")
        
        return " | ".join(parts) if parts else "Configuração padrão"


class PortalSaudeUI:
    """
    Interface do usuário específica para Portal Saude MG.
    """
    
    def __init__(self, terminal_instance):
        self.terminal = terminal_instance
        self.ESC_PRESSED = "__ESC_PRESSED__"
        self.current_config = {}
        
        # Site info
        self.site_info = {
            'name': 'Portal Saude MG - Resoluções',
            'url': 'https://portal-antigo.saude.mg.gov.br/deliberacoes/documents?by_year=0&by_month=&by_format=pdf&category_id=4795&ordering=newest&q=',
            'handler': 'portal_saude_mg'
        }
    
    def _get_key_input(self, prompt: str) -> str:
        """Get user input with ESC detection support."""
        print(f"{prompt} (ESC para voltar)")
        
        try:
            if sys.platform != 'win32':
                # Unix/Linux/macOS implementation
                logger.debug("Using Unix terminal input method")
                return self._get_key_unix()
            else:
                # Windows implementation
                logger.debug("Using Windows terminal input method")
                return self._get_key_windows()
        except (ImportError, ModuleNotFoundError, AttributeError, OSError) as e:
            # Fallback to regular input if special key detection fails
            logger.info(f"Special key detection failed, using standard input: {e}")
            user_input = input().strip()
            return user_input
    
    def _get_key_unix(self) -> str:
        """Unix/Linux/macOS key detection."""
        try:
            # Import Unix-specific modules only when needed
            import termios
            import tty
            import select
            
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin.fileno())
                
                # Read input character by character
                chars = []
                while True:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        char = sys.stdin.read(1)
                        
                        # ESC key (ASCII 27)
                        if ord(char) == 27:
                            # Check if it's a real ESC or part of escape sequence
                            if select.select([sys.stdin], [], [], 0.1)[0]:
                                # It's an escape sequence, consume it
                                next_char = sys.stdin.read(1)
                                if next_char == '[':
                                    # Arrow keys, function keys, etc.
                                    sys.stdin.read(1)  # consume the rest
                                    continue
                            else:
                                # Real ESC key
                                return self.ESC_PRESSED
                        
                        # Enter key
                        elif ord(char) in [10, 13]:  # \n or \r
                            break
                        
                        # Backspace
                        elif ord(char) == 127:
                            if chars:
                                chars.pop()
                                sys.stdout.write('\b \b')
                                sys.stdout.flush()
                        
                        # Regular character
                        elif ord(char) >= 32:  # Printable characters
                            chars.append(char)
                            sys.stdout.write(char)
                            sys.stdout.flush()
                
                print()  # New line after input
                return ''.join(chars).strip()
                
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        except (ImportError, ModuleNotFoundError) as e:
            logger.debug(f"Unix terminal modules not available: {e}")
            # Fallback to regular input
            user_input = input().strip()
            return user_input
    
    def _get_key_windows(self) -> str:
        """Windows key detection - fallback to regular input with ESC simulation."""
        try:
            import msvcrt
            logger.debug("Using msvcrt for Windows key detection")
            chars = []
            
            while True:
                if msvcrt.kbhit():
                    char = msvcrt.getch()
                    
                    # ESC key
                    if ord(char) == 27:
                        return self.ESC_PRESSED
                    
                    # Enter key
                    elif ord(char) in [10, 13]:
                        break
                    
                    # Backspace
                    elif ord(char) == 8:
                        if chars:
                            chars.pop()
                            msvcrt.putch(b'\b')
                            msvcrt.putch(b' ')
                            msvcrt.putch(b'\b')
                    
                    # Regular character
                    elif ord(char) >= 32:
                        try:
                            chars.append(char.decode('utf-8'))
                            msvcrt.putch(char)
                        except UnicodeDecodeError:
                            # Handle non-UTF8 characters gracefully
                            chars.append(chr(ord(char)))
                            msvcrt.putch(char)
            
            print()  # New line
            return ''.join(chars).strip()
            
        except (ImportError, ModuleNotFoundError) as e:
            logger.debug(f"msvcrt not available: {e}")
            # Fallback: simulate ESC with 'esc' command
            print("(Digite 'esc' para voltar)")
            user_input = input().strip().lower()
            if user_input == 'esc':
                return self.ESC_PRESSED
            return user_input
    
    def show_selected_filters(self, year=None, year_range=None, month=None, month_range=None):
        """Mostra os filtros já selecionados no topo da tela."""
        filters = []
        
        if year_range:
            start_year, end_year = year_range
            filters.append(f"Ano: {start_year}-{end_year}")
        elif year is not None:
            if year == 999:
                filters.append("Ano: Todos")
            elif year == 998:
                filters.append("Ano: Intervalo personalizado")
            else:
                filters.append(f"Ano: {year}")
        
        if month_range:
            start_month, end_month = month_range
            month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            start_name = month_names[start_month - 1]
            end_name = month_names[end_month - 1]
            filters.append(f"Mês: {start_name}-{end_name}")
        elif month is not None:
            if month == 13:
                filters.append("Mês: Todos")
            elif month == 14:
                filters.append("Mês: Intervalo personalizado")
            elif 1 <= month <= 12:
                month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                             'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                filters.append(f"Mês: {month_names[month-1]}")
        
        if filters:
            print("Filtros selecionados: " + " | ".join(filters))
            print("")

    def show_config_screen(self) -> Optional[Dict[str, Any]]:
        """Show Portal Saude MG configuration screen."""
        year = None
        year_range = None
        month = None
        month_range = None
        
        while True:
            self.terminal.clear_screen()
            print("========================================")
            print("   PORTAL SAUDE MG - RESOLUÇÕES")
            print("========================================")
            print("")
            self.show_selected_filters(year, year_range, month, month_range)
            print("Site: portal-antigo.saude.mg.gov.br/deliberacoes")
            print("")
            print("Configuracoes automaticas aplicadas:")
            print("- Formato: PDF")
            print("- Categoria: Resolucoes")
            print("- Ordenacao: Mais recente")
            print("")
            print("Configure os filtros:")
            print("")
            
            # Step 1: Get year if not set
            if year is None:
                year = self.get_year_input("1. Ano (obrigatorio):")
                if year is None:  # invalid input or ESC
                    return None  # Return to main menu
                continue  # Refresh screen with new filter
            
            # Step 2: Get year range if year range option selected
            if year == 998 and year_range is None:  # Intervalo personalizado de anos
                year_range = self.get_year_range_input()
                if year_range is None:  # ESC was pressed
                    year = None  # Go back to year selection
                    continue
                continue  # Refresh screen with new filter
                
            # Step 3: Get month if not set
            if month is None:
                month = self.get_month_input("2. Mes:")
                if month is None:  # ESC was pressed
                    if year == 998:
                        year_range = None  # Go back to year range
                    else:
                        year = None  # Go back to year selection
                    continue
                continue  # Refresh screen with new filter
                
            # Step 4: Get month range if month range option selected
            if month == 14 and month_range is None:  # Intervalo personalizado de meses
                month_range = self.get_month_range_input()
                if month_range is None:  # ESC was pressed
                    month = None  # Go back to month selection
                    continue
                continue  # Refresh screen with new filter
            
            # All filters selected - show confirmation
            print("✓ Todos os filtros configurados!")
            print("")
            print("1. Iniciar coleta")
            print("2. Modificar ano")
            print("3. Modificar mês")
            print("4. Voltar ao menu principal")
            print("")
            
            choice = self._get_key_input("Digite sua opcao (1-4): ")
            
            if choice == self.ESC_PRESSED:
                return None  # Return to main menu
            elif choice == "1":
                config = {
                    'site': 'portal_saude_mg',
                    'year': year,
                    'month': month,
                    'url': 'https://portal-antigo.saude.mg.gov.br/deliberacoes/documents?by_year=0&by_month=&by_format=pdf&category_id=4795&ordering=newest&q='
                }
                
                # Add range information if available
                if year_range:
                    config['year_range'] = year_range
                if month_range:
                    config['month_range'] = month_range
                
                return config
            elif choice == "2":
                year = None  # Reset year to modify
                year_range = None  # Also reset year range
            elif choice == "3":
                month = None  # Reset month to modify
                month_range = None  # Also reset month range
            elif choice == "4":
                return None
            else:
                self.terminal.show_error("Opcao invalida. Tente novamente.")
    
    def get_year_input(self, prompt: str) -> Optional[int]:
        """Get and validate year input."""
        print(prompt)
        print("   Digite um ano específico (ex: 2024) ou:")
        print("   1 - Todos os anos disponíveis")
        print("   2 - Intervalo personalizado de anos")
        print("")
        
        year_str = self._get_key_input("   Digite sua opção: ")
        
        if year_str == self.ESC_PRESSED:
            return None  # Signal to go back
        
        try:
            year = int(year_str)
            
            # Special case for "all years"
            if year == 1:
                return 999  # Keep internal value as 999
            
            # Special case for "year range"
            if year == 2:
                return 998  # Keep internal value as 998
            
            # Allow any reasonable year (from 2000 to current year + 20)
            current_year = datetime.now().year
            if 2000 <= year <= current_year + 20:
                return year
            else:
                self.terminal.show_error(f"Ano deve estar entre 2000 e {current_year + 20}, 1 para todos os anos, ou 2 para intervalo.")
                return None
        except ValueError:
            self.terminal.show_error("Entrada invalida. Digite um numero.")
            return None

    def get_month_input(self, prompt: str, required: bool = False) -> Optional[int]:
        """Get and validate month input."""
        print(prompt)
        print("   1) Janeiro    2) Fevereiro   3) Marco")
        print("   4) Abril      5) Maio        6) Junho")
        print("   7) Julho      8) Agosto      9) Setembro")
        print("   10) Outubro   11) Novembro   12) Dezembro")
        
        if not required:
            print("   13) Todos os meses")
            print("   14) Intervalo personalizado de meses")
            max_option = 14
        else:
            max_option = 12
        
        print("")
        month_str = self._get_key_input(f"   Digite sua opcao (1-{max_option}): ")
        
        if month_str == self.ESC_PRESSED:
            return None  # Signal to go back
        
        try:
            month = int(month_str)
            if 1 <= month <= max_option:
                return month
            else:
                self.terminal.show_error(f"Opcao deve estar entre 1 e {max_option}.")
                return None
        except ValueError:
            self.terminal.show_error("Opcao invalida. Digite um numero.")
            return None

    def get_year_range_input(self) -> Optional[tuple]:
        """Get year range input from user."""
        print("   Configurar intervalo de anos:")
        print("")
        
        # Get start year
        start_year_str = self._get_key_input("   Ano de início (ex: 2010): ")
        if start_year_str == self.ESC_PRESSED:
            return None
        
        try:
            start_year = int(start_year_str)
        except ValueError:
            self.terminal.show_error("Ano de início inválido.")
            return None
        
        # Get end year  
        end_year_str = self._get_key_input("   Ano de fim (ex: 2014): ")
        if end_year_str == self.ESC_PRESSED:
            return None
        
        try:
            end_year = int(end_year_str)
        except ValueError:
            self.terminal.show_error("Ano de fim inválido.")
            return None
        
        # Validate range
        current_year = datetime.now().year
        
        if not (2000 <= start_year <= current_year + 20):
            self.terminal.show_error(f"Ano de início deve estar entre 2000 e {current_year + 20}.")
            return None
            
        if not (2000 <= end_year <= current_year + 20):
            self.terminal.show_error(f"Ano de fim deve estar entre 2000 e {current_year + 20}.")
            return None
            
        if start_year > end_year:
            self.terminal.show_error("Ano de início deve ser menor ou igual ao ano de fim.")
            return None
        
        print(f"   Intervalo configurado: {start_year} até {end_year} ({end_year - start_year + 1} anos)")
        return (start_year, end_year)

    def get_month_range_input(self) -> Optional[tuple]:
        """Get month range input from user."""
        print("   Configurar intervalo de meses:")
        print("")
        print("   1) Janeiro    2) Fevereiro   3) Março")
        print("   4) Abril      5) Maio        6) Junho") 
        print("   7) Julho      8) Agosto      9) Setembro")
        print("   10) Outubro   11) Novembro   12) Dezembro")
        print("")
        
        # Get start month
        start_month_str = self._get_key_input("   Mês de início (1-12): ")
        if start_month_str == self.ESC_PRESSED:
            return None
        
        try:
            start_month = int(start_month_str)
            if not (1 <= start_month <= 12):
                self.terminal.show_error("Mês de início deve estar entre 1 e 12.")
                return None
        except ValueError:
            self.terminal.show_error("Mês de início inválido.")
            return None
        
        # Get end month
        end_month_str = self._get_key_input("   Mês de fim (1-12): ")
        if end_month_str == self.ESC_PRESSED:
            return None
        
        try:
            end_month = int(end_month_str)
            if not (1 <= end_month <= 12):
                self.terminal.show_error("Mês de fim deve estar entre 1 e 12.")
                return None
        except ValueError:
            self.terminal.show_error("Mês de fim inválido.")
            return None
        
        # Validate range
        if start_month > end_month:
            self.terminal.show_error("Mês de início deve ser menor ou igual ao mês de fim.")
            return None
        
        month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        start_name = month_names[start_month - 1]
        end_name = month_names[end_month - 1]
        
        print(f"   Intervalo configurado: {start_name} até {end_name} ({end_month - start_month + 1} meses)")
        return (start_month, end_month)
    
    def execute_complete_flow(self):
        """Execute complete Portal Saude MG flow: config -> processing -> results."""
        config = self.show_config_screen()
        if config:
            self.current_config = config
            self.run_scraping_task(config)
    
    def run_scraping_task(self, config: Dict[str, Any]):
        """Run the scraping task with interactive progress display."""
        # Initialize interactive progress display
        progress = InteractiveProgressDisplay(self.terminal, config)
        
        try:
            # Start logging session
            logger.start_session(f"{config['site']}_scraping")
            set_context(site=config['site'])
            
            # Enable silent mode to prevent console pollution
            logger.enable_silent_mode()
            logger.info(f"Iniciando scraping: {config}")
            
            # Start interactive progress display
            progress.start()
            
            # Show initial status
            progress.show_status("Conectando ao site", "Inicializando navegador")
            
            # Import and create scraper
            from src.modules.sites.portal_saude_mg import PortalSaudeMGScraper
            scraper = PortalSaudeMGScraper()
            
            # Execute scraping with progress updates
            result = self._execute_scraping_with_callbacks(scraper, config, progress)
            
            logger.info(f"Scraping finalizado: {result.get('success', False)}")
            
            # Process with AI if scraping was successful
            if result.get('success', False):
                final_result = self._process_ai_with_callbacks(result, config, progress)
                
                # Capture real elapsed time before stopping progress display
                actual_elapsed_minutes = progress.get_elapsed_time()
                
                # Stop progress display and show results
                progress.stop()
                logger.disable_silent_mode()
                logger.end_session()
                self.show_success_screen(final_result, actual_elapsed_minutes)
            else:
                # Capture real elapsed time before stopping progress display
                actual_elapsed_minutes = progress.get_elapsed_time()
                
                # Stop progress display and show error
                progress.stop()
                logger.disable_silent_mode()
                logger.end_session()
                self.show_error_screen(result)
                
        except Exception as e:
            # Capture real elapsed time before stopping progress display
            actual_elapsed_minutes = progress.get_elapsed_time()
            
            # Stop progress display on error
            progress.stop()
            logger.disable_silent_mode()
            logger.error(f"Erro fatal durante scraping: {str(e)}")
            logger.exception("Stack trace completo:")
            logger.end_session()
            
            error_result = {
                'success': False,
                'error': str(e),
                'site': config['site']
            }
            self.show_error_screen(error_result)
    
    def _execute_scraping_with_callbacks(self, scraper, config: Dict[str, Any], progress: InteractiveProgressDisplay) -> Dict[str, Any]:
        """Execute scraping with progress callbacks."""
        completed_steps = ["Conectando ao site"]
        
        # Apply filters
        progress.show_status("Aplicando filtros", "Configurando ano e mês", completed_steps)
        
        # Create callback function to update progress
        def progress_callback(stage, detail, current=None, total=None):
            if stage == "loading_results":
                completed_steps_copy = completed_steps + ["Aplicando filtros"] if "Aplicando filtros" not in completed_steps else completed_steps
                progress.show_status("Carregando resultados", detail, completed_steps_copy)
            elif stage == "downloading_pdfs":
                completed_steps_copy = completed_steps + ["Aplicando filtros", "Carregando resultados"]
                if current and total:
                    progress.set_pdf_progress(current, total)
                progress.show_status("Baixando PDFs", detail, completed_steps_copy)
        
        if config.get('year_range') or config.get('month_range'):
            result = self.process_custom_range(scraper, config, progress_callback)
        elif config['year'] == 999:  # Todos os anos
            result = self.process_all_years(scraper, config, progress_callback)
        elif config.get('month') == 13:  # Todos os meses de um ano específico
            ano = str(config['year'])
            result = self.process_all_months_for_year(scraper, ano, progress_callback)
        else:
            # Single month/year
            ano = str(config['year'])
            mes = f"{config['month']:02d}" if config.get('month') else None
            set_context(year=ano, month=mes)
            
            completed_steps.append("Aplicando filtros")
            progress.show_status("Aplicando filtros", "Ano e mês configurados", completed_steps)
            
            result = scraper.execute_scraping(ano, mes, progress_callback)
        
        # Show final scraping status
        if result.get('success'):
            # All steps should already be completed via callbacks
            files_count = len(result.get('files_downloaded', []))
            completed_steps_final = ["Conectando ao site", "Aplicando filtros", "Carregando resultados", "Baixando PDFs"]
            # Show completed status without active step to avoid confusion
            progress.show_status("", f"Downloads concluídos - {files_count} arquivos", completed_steps_final)
        
        return result
    
    def _process_ai_with_callbacks(self, result: Dict[str, Any], config: Dict[str, Any], progress: InteractiveProgressDisplay) -> Dict[str, Any]:
        """Process PDFs with AI and update progress."""
        completed_steps = ["Conectando ao site", "Aplicando filtros", "Carregando resultados", "Baixando PDFs"]
        
        files_count = len(result.get('files_downloaded', []))
        progress.show_status("Processamento AI", f"Analisando {files_count} PDFs", completed_steps)
        
        # Process with AI
        final_result = self.process_pdfs_with_ai(result, config)
        
        # Show completion
        completed_steps.append("Processamento AI")
        if final_result.get('ai_processing', {}).get('success'):
            progress.show_status("Finalizando", "Tabela Excel gerada com sucesso", completed_steps)
        else:
            progress.show_status("Finalizando", "AI com problemas - PDFs baixados", completed_steps)
        
        return final_result

    def verify_ai_dependencies(self) -> Dict[str, Any]:
        """Verifica se dependências AI estão disponíveis."""
        try:
            logger.info("Verificando dependências AI...")
            
            # Tentar importar e inicializar PDFProcessor
            from src.ai.pdf_call import PDFProcessor
            processor = PDFProcessor()  # Vai falhar se API key não configurada
            
            # Tentar importar PDFTableGenerator  
            from src.utils.pdf_data_to_table import PDFTableGenerator
            generator = PDFTableGenerator()
            
            logger.info("Dependências AI verificadas com sucesso")
            return {
                'success': True,
                'processor': processor,
                'generator': generator
            }
            
        except ImportError as e:
            error_msg = f"Módulos AI não disponíveis: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'import_error'
            }
        except Exception as e:
            error_msg = f"Erro ao inicializar dependências AI: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'initialization_error'
            }

    def process_pdfs_with_ai(self, scraping_result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Processar PDFs com AI após scraping bem-sucedido."""
        logger.info("Iniciando processamento AI dos PDFs...")
        
        # Verificar se há PDFs para processar
        downloaded_files = scraping_result.get('files_downloaded', [])
        if not downloaded_files:
            logger.warning("Nenhum PDF encontrado para processamento AI")
            scraping_result['ai_processing'] = {
                'attempted': False,
                'reason': 'Nenhum PDF encontrado'
            }
            return scraping_result
        
        # Verificar dependências AI
        ai_check = self.verify_ai_dependencies()
        if not ai_check['success']:
            logger.error(f"Dependências AI não disponíveis: {ai_check['error']}")
            return self.handle_ai_processing_error(ai_check, scraping_result, config)
        
        try:
            processor = ai_check['processor']
            generator = ai_check['generator']
            
            # Determinar diretório de PDFs
            pdf_directory = scraping_result.get('download_path', 'downloads/raw/portal_saude_mg')
            logger.info(f"Processando PDFs do diretório: {pdf_directory}")
            
            # Atualizar tela de progresso
            self.update_processing_screen("Processando PDFs com IA...")
            
            # Processar PDFs um por vez para evitar limite de tokens
            from pathlib import Path
            pdf_dir = Path(pdf_directory)
            pdf_files = list(pdf_dir.glob("*.pdf"))
            
            # Carregar URL mapping se existir
            url_mapping = self._load_url_mapping_from_dir(pdf_dir)
            logger.info(f"Processando {len(pdf_files)} PDFs sequencialmente")
            
            processing_results = []
            for i, pdf_file in enumerate(pdf_files):
                logger.info(f"Processando arquivo {i+1}/{len(pdf_files)}: {pdf_file.name}")
                
                # Obter URL para este arquivo se disponível
                file_url = None
                if url_mapping and pdf_file.name in url_mapping:
                    file_url = url_mapping[pdf_file.name]['url']
                
                result = processor.process_single_pdf(str(pdf_file), file_link=file_url)
                processing_results.append(result)
            
            if not processing_results:
                error_msg = "Nenhum resultado do processamento AI"
                logger.error(error_msg)
                return self.handle_ai_processing_error(
                    {'success': False, 'error': error_msg},
                    scraping_result, config
                )
            
            # Atualizar tela de progresso
            self.update_processing_screen("Gerando tabela Excel...")
            
            # Gerar tabela Excel
            table_result = generator.process_extraction_results_to_table(
                processing_results, pdf_directory
            )
            
            if not table_result.get('success', False):
                error_msg = f"Falha na geração da tabela: {table_result.get('error', 'Erro desconhecido')}"
                logger.error(error_msg)
                return self.handle_ai_processing_error(
                    {'success': False, 'error': error_msg},
                    scraping_result, config
                )
            
            # Sucesso completo - adicionar informações AI ao resultado
            logger.info("Processamento AI concluído com sucesso")
            
            # Calcular estatísticas
            successful_extractions = sum(1 for r in processing_results if r.get('success', False))
            failed_extractions = len(processing_results) - successful_extractions
            total_tokens = sum(
                r.get('extracted_data', {}).get('_ai_metadata', {}).get('tokens_used', 0)
                for r in processing_results if r.get('success', False)
            )
            
            # Combinar resultados
            final_result = scraping_result.copy()
            final_result['ai_processing'] = {
                'success': True,
                'pdfs_processed': len(processing_results),
                'successful_extractions': successful_extractions,
                'failed_extractions': failed_extractions,
                'total_tokens_used': total_tokens,
                'estimated_cost_usd': 'consultar no API provider',
                'excel_file': table_result.get('output_file'),
                'table_stats': {
                    'total_rows': table_result.get('total_rows', 0),
                    'extraction_issues': table_result.get('extraction_issues', [])
                }
            }
            
            return final_result
            
        except Exception as e:
            error_msg = f"Erro durante processamento AI: {str(e)}"
            logger.error(error_msg)
            logger.exception("Stack trace do erro AI:")
            return self.handle_ai_processing_error(
                {'success': False, 'error': error_msg},
                scraping_result, config
            )

    def handle_ai_processing_error(self, ai_error: Dict[str, Any], scraping_result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Lidar com erros de processamento AI sem falhar o programa."""
        logger.warning("Processamento AI falhou, mas PDFs foram baixados com sucesso")
        
        # Adicionar informações de erro AI ao resultado
        result_with_error = scraping_result.copy()
        result_with_error['ai_processing'] = {
            'success': False,
            'attempted': True,
            'error': ai_error.get('error', 'Erro desconhecido'),
            'error_type': ai_error.get('error_type', 'unknown'),
            'pdfs_available': len(scraping_result.get('files_downloaded', [])),
            'recovery_options': [
                'Configurar API key OpenAI',
                'Instalar dependências AI',
                'Tentar processamento novamente'
            ]
        }
        
        # Mostrar tela de erro específica para AI
        self.show_ai_error_screen(result_with_error, config)
        return result_with_error

    def _load_url_mapping_from_dir(self, pdf_directory) -> Optional[Dict[str, Dict[str, str]]]:
        """Carregar URL mapping do diretório de PDFs."""
        try:
            mapping_file = pdf_directory / 'url_mapping.json'
            if not mapping_file.exists():
                return None
            
            import json
            with open(mapping_file, 'r', encoding='utf-8') as f:
                url_mapping = json.load(f)
            
            if isinstance(url_mapping, dict):
                return url_mapping
            return None
        except Exception:
            return None

    def update_processing_screen(self, status_message: str):
        """Atualizar tela de processamento com novo status."""
        # Deprecated: Now using ProgressTracker for dynamic updates
        logger.info(f"Status: {status_message}")

    def show_success_screen(self, result: Dict[str, Any], actual_elapsed_minutes: float = None):
        """Show success screen with results."""
        self.terminal.clear_screen()
        print("========================================")
        print("         PROCESSO CONCLUIDO")
        print("========================================")
        print("")
        print("Status: SUCESSO")
        print("")
        print("Resumo da coleta:")
        print(f"- Site processado: {self.site_info['name']}")
        print(f"- Filtros aplicados: {self.format_config_summary(self.current_config)}")
        
        # Mostrar detalhes específicos para busca por múltiplos anos, meses ou intervalos
        if result.get('range_description'):
            print(f"- Intervalo processado: {result.get('range_description')}")
            print(f"- Períodos processados: {result.get('periods_processed')}")
            print(f"- Arquivos coletados: {len(result.get('files_downloaded', []))} arquivos")
        elif result.get('years_processed'):
            print(f"- Anos processados: {result.get('years_processed')} anos")
            if result.get('years_with_data'):
                years_list = ', '.join(map(str, sorted(result['years_with_data'], reverse=True)[:5]))
                if len(result['years_with_data']) > 5:
                    years_list += f" (e mais {len(result['years_with_data']) - 5})"
                print(f"- Anos com dados: {years_list}")
            print(f"- Arquivos coletados: {len(result.get('files_downloaded', []))} arquivos")
        elif result.get('months_processed'):
            print(f"- Meses processados: {result.get('months_processed')} de 12")
            print(f"- Arquivos coletados: {len(result.get('files_downloaded', []))} arquivos")
        else:
            print(f"- Arquivos coletados: {len(result.get('files_downloaded', []))} arquivos")
            
        print(f"- Tamanho total: {result.get('total_size_mb', 0):.1f} MB")
        
        # Use actual elapsed time from progress display if available, otherwise fallback to result time
        elapsed_time = actual_elapsed_minutes if actual_elapsed_minutes is not None else result.get('duration_minutes', 0)
        print(f"- Tempo decorrido: {elapsed_time:.1f} minutos")
        
        # Mostrar resumo adicional se disponível
        if result.get('summary'):
            print(f"- Resumo: {result.get('summary')}")
        
        print("")
        print(f"Arquivos salvos em: {result.get('download_path', 'downloads/')}")
        
        # Mostrar informações específicas sobre processamento AI
        ai_info = result.get('ai_processing', {})
        if ai_info.get('success'):
            print("")
            print("=== PROCESSAMENTO AI ===")
            print(f"✓ PDFs processados com IA: {ai_info.get('pdfs_processed', 0)}")
            print(f"✓ Extrações bem-sucedidas: {ai_info.get('successful_extractions', 0)}")
            if ai_info.get('failed_extractions', 0) > 0:
                print(f"⚠ Extrações com erro: {ai_info.get('failed_extractions', 0)}")
            print(f"✓ Tokens consumidos: {ai_info.get('total_tokens_used', 0):,}")
            print(f"✓ Custo estimado: {ai_info.get('estimated_cost_usd', 'consultar no API provider')}")
            
            excel_file = ai_info.get('excel_file')
            if excel_file:
                print(f"✓ Tabela Excel gerada: {excel_file}")
                table_stats = ai_info.get('table_stats', {})
                if table_stats.get('total_rows'):
                    print(f"  - Linhas na tabela: {table_stats['total_rows']}")
                    issues = table_stats.get('extraction_issues', [])
                    if issues:
                        print(f"  - Problemas encontrados: {len(issues)}")
        elif ai_info.get('attempted'):
            print("")
            print("=== PROCESSAMENTO AI ===")
            print("✗ Processamento AI falhou")
            print(f"  - {ai_info.get('error', 'Erro desconhecido')}")
            print(f"  - PDFs disponíveis: {ai_info.get('pdfs_available', 0)}")
        else:
            print("")
            print("=== PROCESSAMENTO AI ===")
            print("- Não foi tentado (nenhum PDF encontrado)")
        
        print("")
        
        # Opções baseadas no sucesso do AI
        if ai_info.get('success') and ai_info.get('excel_file'):
            print("1. Abrir tabela Excel")
            print("2. Abrir pasta de downloads (PDFs)")
            print("3. Abrir pasta processed (Excel)")
            print("4. Processar outro site")
            print("5. Sair")
            print("")
            
            choice = self.terminal.get_user_input("Digite sua opcao (1-5): ")
            
            if choice == "1":
                self.open_excel_file(ai_info.get('excel_file'))
            elif choice == "2":
                self.open_downloads_folder(result.get('download_path'))
            elif choice == "3":
                import os
                processed_path = os.path.dirname(ai_info.get('excel_file', 'downloads/processed'))
                self.open_downloads_folder(processed_path)
            elif choice == "4":
                return
            elif choice == "5":
                self.terminal.running = False
        else:
            print("1. Abrir pasta de downloads")
            print("2. Processar outro site")
            print("3. Sair")
            print("")
            
            choice = self.terminal.get_user_input("Digite sua opcao (1-3): ")
            
            if choice == "1":
                self.open_downloads_folder(result.get('download_path'))
            elif choice == "2":
                return
            elif choice == "3":
                self.terminal.running = False

    def show_error_screen(self, result: Dict[str, Any]):
        """Show error screen."""
        self.terminal.clear_screen()
        print("========================================")
        print("           PROCESSO FALHOU")
        print("========================================")
        print("")
        print("Status: ERRO")
        print("")
        print("Detalhes do erro:")
        print(result.get('error', 'Erro desconhecido'))
        print("")
        print("Arquivos parciais salvos em: downloads/temp/")
        print("")
        print("1. Tentar novamente com as mesmas configuracoes")
        print("2. Voltar ao menu principal para nova configuracao")
        print("3. Ver logs de erro detalhados")
        print("4. Sair")
        print("")
        
        choice = self.terminal.get_user_input("Digite sua opcao (1-4): ")
        
        if choice == "1":
            if self.current_config:
                self.run_scraping_task(self.current_config)
            else:
                self.terminal.show_error("Configuracao nao encontrada. Retornando ao menu principal.")
        elif choice == "2":
            return
        elif choice == "3":
            self.show_error_logs()
        elif choice == "4":
            self.terminal.running = False

    def open_downloads_folder(self, path: str = None):
        """Open downloads folder in file manager."""
        try:
            if path is None:
                path = "downloads/"
            
            if os.path.exists(path):
                if sys.platform == "win32":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    os.system(f"open '{path}'")
                else:
                    os.system(f"xdg-open '{path}'")
            else:
                print(f"Pasta nao encontrada: {path}")
        except Exception as e:
            print(f"Erro ao abrir pasta: {e}")
        
        input("Pressione Enter para continuar...")

    def show_error_logs(self):
        """Show error logs."""
        self.terminal.clear_screen()
        print("========================================")
        print("         LOGS DE ERRO")
        print("========================================")
        print("")
        print("Logs detalhados salvos em: logs/")
        print("")
        print("Para análise técnica, verifique os arquivos de log.")
        print("")
        input("Pressione Enter para continuar...")

    def open_excel_file(self, excel_path: str = None):
        """Open Excel file in default application."""
        try:
            if excel_path is None or not os.path.exists(excel_path):
                print(f"Arquivo Excel não encontrado: {excel_path}")
                input("Pressione Enter para continuar...")
                return
            
            if sys.platform == "win32":
                os.startfile(excel_path)
            elif sys.platform == "darwin":
                os.system(f"open '{excel_path}'")
            else:
                os.system(f"xdg-open '{excel_path}'")
                
            print(f"Abrindo arquivo: {excel_path}")
            
        except Exception as e:
            print(f"Erro ao abrir arquivo Excel: {e}")
        
        input("Pressione Enter para continuar...")

    def show_ai_error_screen(self, result: Dict[str, Any], config: Dict[str, Any]):
        """Show AI processing error screen with recovery options."""
        self.terminal.clear_screen()
        print("========================================")
        print("        ERRO NO PROCESSAMENTO AI")
        print("========================================")
        print("")
        print("Status: PDFs baixados com sucesso ✓")
        print("        Processamento AI falhou ✗")
        print("")
        
        ai_info = result.get('ai_processing', {})
        error_msg = ai_info.get('error', 'Erro desconhecido')
        error_type = ai_info.get('error_type', 'unknown')
        
        print("Erro encontrado:")
        if error_type == 'import_error':
            print("• Módulos AI não estão instalados")
            print("• Execute: pip install -r requirements.txt")
        elif error_type == 'initialization_error':
            if 'API key' in error_msg or 'OpenAI' in error_msg:
                print("• OpenAI API key não configurada")
                print("• Verifique se OPENAI_API_KEY está definida no arquivo .env")
            else:
                print(f"• {error_msg}")
        else:
            print(f"• {error_msg}")
        
        print("")
        print("Arquivos baixados salvos em:")
        print(f"{result.get('download_path', 'downloads/raw/portal_saude_mg')}")
        print(f"Total: {len(result.get('files_downloaded', []))} PDFs ({result.get('total_size_mb', 0):.1f} MB)")
        print("")
        
        print("Opções de recuperação:")
        print("1. Configurar API key e tentar processamento AI novamente")
        print("2. Instalar dependências AI faltantes")
        print("3. Continuar sem processamento AI (só PDFs baixados)")
        print("4. Abrir pasta de downloads")
        print("5. Voltar ao menu principal")
        print("6. Sair")
        print("")
        
        choice = self.terminal.get_user_input("Digite sua opção (1-6): ")
        
        if choice == "1":
            # Tentar processamento AI novamente
            try:
                logger.info("Usuário escolheu tentar processamento AI novamente")
                final_result = self.process_pdfs_with_ai(result, config)
                self.show_success_screen(final_result)
            except Exception as e:
                logger.error(f"Erro ao tentar processamento AI novamente: {e}")
                self.terminal.show_error("Falha ao tentar novamente. Verifique a configuração.")
                self.show_ai_error_screen(result, config)
                
        elif choice == "2":
            self.show_dependency_help_screen()
            
        elif choice == "3":
            # Continuar sem AI - mostrar resultado do scraping apenas
            self.show_success_screen(result)
            
        elif choice == "4":
            self.open_downloads_folder(result.get('download_path'))
            self.show_ai_error_screen(result, config)
            
        elif choice == "5":
            return  # Volta ao menu principal
            
        elif choice == "6":
            self.terminal.running = False
            
        else:
            self.terminal.show_error("Opção inválida. Tente novamente.")
            self.show_ai_error_screen(result, config)

    def show_dependency_help_screen(self):
        """Show help screen for installing AI dependencies."""
        self.terminal.clear_screen()
        print("========================================")
        print("         AJUDA - DEPENDÊNCIAS AI")
        print("========================================")
        print("")
        print("Para usar o processamento AI, você precisa:")
        print("")
        print("1. Instalar dependências Python:")
        print("   pip install -r requirements.txt")
        print("")
        print("2. Configurar API key OpenAI:")
        print("   - Crie/edite o arquivo .env na raiz do projeto")
        print("   - Adicione: OPENAI_API_KEY=sua_chave_aqui")
        print("   - Obtenha sua chave em: https://platform.openai.com/api-keys")
        print("")
        print("3. Verificar se o arquivo .env está no formato correto:")
        print("   OPENAI_API_KEY=sk-proj-...")
        print("   (sem espaços ao redor do =)")
        print("")
        print("4. Reiniciar o programa após configurar")
        print("")
        print("Dependências necessárias:")
        print("• pymupdf4llm - Para extração de texto de PDFs")
        print("• openai - Para processamento com IA")
        print("• pandas - Para manipulação de dados")
        print("• openpyxl - Para geração de Excel")
        print("")
        
        input("Pressione Enter para continuar...")
    

    def format_config_summary(self, config: Dict[str, Any]) -> str:
        """Format configuration summary for display."""
        parts = []
        
        # Handle year or year range
        if config.get('year_range'):
            start_year, end_year = config['year_range']
            parts.append(f"Ano: {start_year}-{end_year}")
        elif 'year' in config:
            if config['year'] == 999:
                parts.append("Ano: Todos")
            elif config['year'] == 998:
                parts.append("Ano: Intervalo personalizado")
            else:
                parts.append(f"Ano: {config['year']}")
        
        # Handle month or month range
        if config.get('month_range'):
            start_month, end_month = config['month_range']
            months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            start_name = months[start_month - 1]
            end_name = months[end_month - 1]
            parts.append(f"Mes: {start_name}-{end_name}")
        elif 'month' in config:
            if config['month'] == 13:
                parts.append("Mes: Todos")
            elif config['month'] == 14:
                parts.append("Mes: Intervalo personalizado")
            elif 1 <= config['month'] <= 12:
                months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                         'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                parts.append(f"Mes: {months[config['month']-1]}")
        
        if 'municipality' in config:
            if config['municipality'] == 'ALL_MG':
                parts.append("Municipio: Todos de MG")
            else:
                parts.append(f"Municipio: {config['municipality']}")
        
        return ", ".join(parts)
    
    def process_custom_range(self, scraper, config: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Process custom year and/or month ranges."""
        year_range = config.get('year_range')
        month_range = config.get('month_range')
        
        all_range_results = []
        total_files_found = 0
        periods_processed = 0
        
        # Determine years to process
        if year_range:
            start_year, end_year = year_range
            years_to_process = list(range(start_year, end_year + 1))
            range_desc = f"Anos {start_year}-{end_year}"
        elif config['year'] == 999:  # "Todos os anos" - use real years
            current_year = datetime.now().year
            years_to_process = list(range(current_year, 1999, -1))  # Current year back to 2000
            range_desc = f"Todos os anos disponíveis"
        else:
            years_to_process = [config['year']]
            range_desc = f"Ano {config['year']}"
        
        # Determine months to process
        if month_range:
            start_month, end_month = month_range
            months_to_process = list(range(start_month, end_month + 1))
            month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            range_desc += f", Meses {month_names[start_month-1]}-{month_names[end_month-1]}"
        elif config.get('month') == 13:
            months_to_process = list(range(1, 13))
            range_desc += ", Todos os meses"
        else:
            months_to_process = [config.get('month')] if config.get('month') else [None]
        
        logger.info(f"Processando Intervalo Personalizado: {range_desc}")
        
        for year in years_to_process:
            ano = str(year)
            set_context(year=ano)
            logger.info(f"Iniciando processamento do ano {ano}")
            
            year_files = 0
            
            for month in months_to_process:
                if month is None:
                    mes_desc = "todos os meses"
                    mes = None
                else:
                    mes = f"{month:02d}"
                    mes_desc = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][month-1]
                
                set_context(year=ano, month=mes)
                
                try:
                    result = scraper.execute_scraping(ano, mes, progress_callback)
                    files_count = len(result.get('files_downloaded', []))
                    
                    if files_count > 0:
                        all_range_results.append(result)
                        total_files_found += files_count
                        year_files += files_count
                        periods_processed += 1
                        logger.info(f"Sucesso {mes_desc}/{ano}: {files_count} arquivos")
                    else:
                        logger.info(f"Sem dados {mes_desc}/{ano}")
                        # Check for future months
                        if year == years_to_process[-1] and month and month > datetime.now().month:
                            logger.info(f"Mês futuro detectado - parando ano {ano}")
                            break
                
                except Exception as e:
                    logger.error(f"Erro ao processar {mes_desc}/{ano}: {str(e)}")
                    continue
            
            logger.info(f"Ano {ano} concluído: {year_files} arquivos")
        
        logger.info(f"Intervalo processado: {periods_processed} períodos, {total_files_found} arquivos")
        return self.consolidate_range_results(all_range_results, config, periods_processed, total_files_found)

    def consolidate_range_results(self, range_results: List[Dict[str, Any]], config: Dict[str, Any], periods_processed: int, total_files: int) -> Dict[str, Any]:
        """Consolidate results from custom range processing."""
        if not range_results:
            return {
                'success': False,
                'files_downloaded': [],
                'total_files': 0,
                'errors': ['Nenhum período processado com sucesso'],
                'periods_processed': 0
            }
        
        # Consolidar arquivos de todos os períodos
        all_files = []
        all_errors = []
        total_duration = 0
        total_size_mb = 0
        
        for result in range_results:
            all_files.extend(result.get('files_downloaded', []))
            all_errors.extend(result.get('errors', []))
            total_duration += result.get('duration_minutes', 0)
            total_size_mb += result.get('total_size_mb', 0)
        
        # Create summary
        year_range = config.get('year_range')
        month_range = config.get('month_range')
        
        if year_range and month_range:
            range_desc = f"Anos {year_range[0]}-{year_range[1]}, Meses {month_range[0]}-{month_range[1]}"
        elif year_range:
            range_desc = f"Anos {year_range[0]}-{year_range[1]}"
        elif month_range:
            range_desc = f"Ano {config['year']}, Meses {month_range[0]}-{month_range[1]}"
        else:
            range_desc = "Intervalo personalizado"
        
        consolidated_result = {
            'success': len(all_files) > 0,
            'files_downloaded': all_files,
            'total_files': total_files,
            'duration_minutes': total_duration,
            'total_size_mb': total_size_mb,
            'download_path': "downloads/raw/portal_saude_mg",
            'errors': all_errors,
            'periods_processed': periods_processed,
            'range_description': range_desc,
            'summary': f"Processado {range_desc} - Total: {len(all_files)} arquivos ({total_size_mb:.1f} MB)"
        }
        
        return consolidated_result

    def process_all_years(self, scraper, config: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Process all available years."""
        current_year = datetime.now().year
        years_to_check = list(range(current_year, 1999, -1))  # Current year back to 2000
        
        all_year_results = []
        total_files_found = 0
        years_processed = 0
        years_with_data = []
        
        logger.info(f"Processando Todos os Anos Disponíveis (2000-{current_year})")
        
        for year in years_to_check:
            ano = str(year)
            set_context(year=ano)
            logger.info(f"Iniciando processamento do ano {ano}")
            
            try:
                if config.get('month') == 13:  # Todos os meses para este ano
                    year_result = self.process_all_months_for_year(scraper, ano, progress_callback)
                else:
                    # Mês específico para este ano
                    mes = f"{config['month']:02d}" if config.get('month') else None
                    set_context(year=ano, month=mes)
                    year_result = scraper.execute_scraping(ano, mes, progress_callback)
                
                files_in_year = len(year_result.get('files_downloaded', []))
                
                if files_in_year > 0:
                    all_year_results.append(year_result)
                    total_files_found += files_in_year
                    years_processed += 1
                    years_with_data.append(year)
                    logger.info(f"Sucesso ano {year}: {files_in_year} arquivos")
                else:
                    logger.info(f"Sem dados no ano {year}")
                    
                    # Se não encontrar dados por 3 anos consecutivos, parar
                    if len(years_with_data) > 0 and (years_with_data[-1] - year) > 3:
                        logger.info(f"Sem dados por mais de 3 anos consecutivos - parando busca")
                        break
                        
            except Exception as e:
                logger.error(f"Erro no ano {year}: {str(e)}")
                continue
        
        logger.info(f"Processamento de todos os anos concluído: {years_processed} anos, {total_files_found} arquivos")
        return self.consolidate_yearly_results(all_year_results, years_processed, total_files_found, years_with_data)

    def process_all_months_for_year(self, scraper, ano: str, progress_callback=None) -> Dict[str, Any]:
        """Process all months for a specific year."""
        all_results = []
        total_files_found = 0
        months_processed = 0
        
        month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        
        logger.info(f"Processando Todos os Meses de {ano}")
        
        set_context(year=ano)
        
        for month_num in range(1, 13):
            mes = f"{month_num:02d}"
            month_name = month_names[month_num - 1]
            
            set_context(year=ano, month=mes)
            logger.info(f"Processando {month_name}/{ano}")
            
            try:
                result = scraper.execute_scraping(ano, mes, progress_callback)
                
                # Parar se não houver links (provável mês futuro)
                if result.get('total_files', 0) == 0:
                    logger.info(f"Nenhum resultado para {month_name} - parando meses")
                    break
                
                files_count = len(result.get('files_downloaded', []))
                logger.info(f"Sucesso {month_name}: {files_count} arquivos")
                
                all_results.append(result)
                total_files_found += files_count
                months_processed += 1
                
            except Exception as e:
                logger.error(f"Erro em {month_name}/{ano}: {str(e)}")
                continue
        
        logger.info(f"Processamento de meses para {ano} concluído: {months_processed} meses, {total_files_found} arquivos")
        return self.consolidate_monthly_results(all_results, ano, months_processed, total_files_found)


    def consolidate_yearly_results(self, yearly_results: List[Dict[str, Any]], years_processed: int, total_files: int, years_with_data: List[int]) -> Dict[str, Any]:
        """Consolidate results from multiple years."""
        if not yearly_results:
            return {
                'success': False,
                'files_downloaded': [],
                'total_files': 0,
                'errors': ['Nenhum ano processado com sucesso'],
                'years_processed': 0
            }
        
        # Consolidar arquivos de todos os anos
        all_files = []
        all_errors = []
        total_duration = 0
        total_size_mb = 0
        
        for result in yearly_results:
            all_files.extend(result.get('files_downloaded', []))
            all_errors.extend(result.get('errors', []))
            total_duration += result.get('duration_minutes', 0)
            total_size_mb += result.get('total_size_mb', 0)
        
        years_range = f"{min(years_with_data)}-{max(years_with_data)}" if years_with_data else "N/A"
        
        consolidated_result = {
            'success': len(all_files) > 0,
            'files_downloaded': all_files,
            'total_files': total_files,
            'duration_minutes': total_duration,
            'total_size_mb': total_size_mb,
            'download_path': "downloads/raw/portal_saude_mg",
            'errors': all_errors,
            'years_processed': years_processed,
            'years_with_data': years_with_data,
            'summary': f"Processados {years_processed} anos ({years_range}) - Total: {len(all_files)} arquivos ({total_size_mb:.1f} MB)"
        }
        
        return consolidated_result

    def consolidate_monthly_results(self, monthly_results: List[Dict[str, Any]], ano: str, months_processed: int, total_files: int) -> Dict[str, Any]:
        """Consolidate results from multiple months into a single result."""
        if not monthly_results:
            return {
                'success': False,
                'files_downloaded': [],
                'total_files': 0,
                'errors': ['Nenhum mês processado com sucesso'],
                'months_processed': 0
            }
        
        # Consolidar arquivos de todos os meses
        all_files = []
        all_errors = []
        total_duration = 0
        total_size_mb = 0
        
        for result in monthly_results:
            all_files.extend(result.get('files_downloaded', []))
            all_errors.extend(result.get('errors', []))
            total_duration += result.get('duration_minutes', 0)
            total_size_mb += result.get('total_size_mb', 0)
        
        # Resultado consolidado
        consolidated_result = {
            'success': len(all_files) > 0,
            'files_downloaded': all_files,
            'total_files': total_files,
            'duration_minutes': total_duration,
            'total_size_mb': total_size_mb,
            'download_path': f"downloads/raw/portal_saude_mg/{ano}",
            'errors': all_errors,
            'months_processed': months_processed,
            'summary': f"Processados {months_processed} meses de {ano} - Total: {len(all_files)} arquivos ({total_size_mb:.1f} MB)"
        }
        
        return consolidated_result
