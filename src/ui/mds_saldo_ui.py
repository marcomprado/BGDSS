#!/usr/bin/env python3
"""
MDS Saldo Detalhado Terminal Interface

Interface específica para o MDS - Saldo Detalhado por Conta com funcionalidades 
de seleção de ano, mês e município.
"""

import sys
import select
import termios
import tty
import os
import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.utils.logger import logger, set_context
from src.ai.municipality_corrector import get_municipality_corrector


class InteractiveProgressDisplay:
    """
    Interactive progress display with real-time updates for MDS Saldo.
    Simplified version focused on essential progress tracking.
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
        
        # Threading control
        self.running = False
        self.update_thread = None
        self.lock = threading.Lock()
        
        # Display state
        self.last_timer_line = ""
        self.timer_line_number = 7
        self.steps_start_line = 10
        self.first_render = False
        
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
            return
            
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
            return
            
        all_steps = [
            "Conectando ao site MDS",
            "Fazendo autenticação",
            "Aplicando filtros",
            "Consultando saldo",
            "Coletando dados",
            "Processando informações",
            "Salvando resultados",
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
            "Conectando ao site MDS",
            "Fazendo autenticação",
            "Aplicando filtros",
            "Consultando saldo",
            "Coletando dados",
            "Processando informações",
            "Salvando resultados",
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
                print(step_line)
            else:
                print(f"  {step_name}")
        
        print("")
        print("Pressione Ctrl+C para cancelar")
        
        # Mark first render as complete and position cursor safely
        self.first_render = True
        print(f"\033[20;1H", end='', flush=True)
    
    def _format_config(self) -> str:
        """Format configuration for display."""
        parts = []
        
        # Handle year configuration
        year_config = self.config.get('year_config', {})
        if year_config.get('type') == 'single':
            parts.append(f"Ano: {year_config['year']}")
        elif year_config.get('type') == 'range':
            parts.append(f"Anos: {year_config['start_year']}-{year_config['end_year']}")
        elif year_config.get('type') == 'multiple':
            years_str = ', '.join(map(str, year_config['years'][:3]))
            if len(year_config['years']) > 3:
                years_str += '...'
            parts.append(f"Anos: {years_str}")
        elif year_config.get('type') == 'all':
            parts.append("Anos: Todos")
        
        # Handle month
        if 'month' in self.config:
            month = self.config['month']
            if isinstance(month, dict):
                if month.get('type') == 'all':
                    parts.append("Mês: Todos")
                elif month.get('type') == 'single':
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    parts.append(f"Mês: {month_names[month['month']-1]}")
                elif month.get('type') == 'multiple':
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    months_str = ', '.join([month_names[m-1] for m in month['months'][:3]])
                    if len(month['months']) > 3:
                        months_str += '...'
                    parts.append(f"Meses: {months_str}")
            else:
                # Legacy support for integer month values
                if month == 13:
                    parts.append("Mês: Todos")
                elif 1 <= month <= 12:
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    parts.append(f"Mês: {month_names[month-1]}")
        
        # Handle UF
        if 'uf' in self.config:
            parts.append(f"UF: {self.config['uf']}")
        
        # Handle municipality
        if 'municipality' in self.config:
            municipality = self.config['municipality']
            if municipality.startswith('ALL_'):
                uf = municipality.split('_')[1]
                parts.append(f"Município: Todos de {uf}")
            else:
                parts.append(f"Município: {municipality}")
        
        return " | ".join(parts) if parts else "Configuração padrão"

class MDSSaldoUI:
    """
    Interface do usuário específica para MDS Saldo Detalhado por Conta.
    """
    
    def __init__(self, terminal_instance):
        self.terminal = terminal_instance
        self.ESC_PRESSED = "__ESC_PRESSED__"
        self.current_config = {}
        
        # Site info
        self.site_info = {
            'name': 'MDS - Saldo Detalhado',
            'url': 'https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*tbmepQbs',
            'handler': 'mds_saldo'
        }
        
        # Estados brasileiros válidos
        self.valid_states = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
    
    def _get_key_input(self, prompt: str) -> str:
        """Get user input with ESC detection support."""
        print(f"{prompt} (ESC para voltar)")
        
        try:
            if sys.platform != 'win32':
                # Unix/Linux/macOS implementation
                return self._get_key_unix()
            else:
                # Windows implementation - fallback to regular input
                return self._get_key_windows()
        except (ImportError, AttributeError, OSError):
            # Fallback: aceitar tanto ESC físico quanto 'esc' digitado
            print("(Digite 'esc' para voltar)")
            user_input = input().strip().lower()
            if user_input == 'esc':
                return self.ESC_PRESSED
            return user_input
    
    def _get_key_unix(self) -> str:
        """Unix/Linux/macOS key detection."""
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
    
    def _get_key_windows(self) -> str:
        """Windows key detection - fallback to regular input with ESC simulation."""
        try:
            import msvcrt
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
                        chars.append(char.decode('utf-8'))
                        msvcrt.putch(char)
            
            print()  # New line
            return ''.join(chars).strip()
            
        except ImportError:
            # Fallback: simulate ESC with 'esc' command
            print("(Digite 'esc' para voltar)")
            user_input = input().strip().lower()
            if user_input == 'esc':
                return self.ESC_PRESSED
            return user_input
    
    def show_selected_filters(self, year_config=None, month=None, uf=None, municipality=None):
        """Mostra os filtros já selecionados no topo da tela."""
        filters = []
        
        if year_config:
            if year_config.get('type') == 'single':
                filters.append(f"Ano: {year_config['year']}")
            elif year_config.get('type') == 'range':
                filters.append(f"Anos: {year_config['start_year']}-{year_config['end_year']}")
            elif year_config.get('type') == 'multiple':
                years_str = ', '.join(map(str, year_config['years']))
                filters.append(f"Anos: {years_str}")
            elif year_config.get('type') == 'all':
                filters.append("Anos: Todos")
        
        if month:
            if isinstance(month, dict):
                if month.get('type') == 'all':
                    filters.append("Mês: Todos")
                elif month.get('type') == 'single':
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    filters.append(f"Mês: {month_names[month['month']-1]}")
                elif month.get('type') == 'multiple':
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    months_str = ', '.join([month_names[m-1] for m in month['months'][:3]])
                    if len(month['months']) > 3:
                        months_str += '...'
                    filters.append(f"Meses: {months_str}")
            else:
                # Legacy support for integer month values
                if month == 13:
                    filters.append("Mês: Todos")
                elif 1 <= month <= 12:
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    filters.append(f"Mês: {month_names[month-1]}")
        
        if uf:
            filters.append(f"Estado: {uf}")
        
        if municipality:
            if municipality.startswith('ALL_'):
                state = municipality.split('_')[1]
                filters.append(f"Município: Todos de {state}")
            else:
                filters.append(f"Município: {municipality}")
        
        if filters:
            print("Filtros selecionados: " + " | ".join(filters))
            print("")
    
    def show_config_screen(self) -> Optional[Dict[str, Any]]:
        """Show MDS Saldo Detalhado configuration screen."""
        year_config = None
        month = None
        uf = None
        municipality = None
        
        while True:
            self.terminal.clear_screen()
            print("========================================")
            print("    MDS - SALDO DETALHADO POR CONTA")
            print("========================================")
            print("")
            self.show_selected_filters(year_config, month, uf, municipality)
            print("Site: aplicacoes.mds.gov.br/suaswebcons")
            print("")
            print("Configure os filtros para consulta:")
            print("")
            
            # Step 1: Get year if not set
            if year_config is None:
                year_config = self.get_year_input("1. Ano (obrigatório, >= 2011):")
                if year_config is None:  # invalid input or ESC
                    return None  # Return to main menu
                continue  # Refresh screen with new filter
            
            # Step 2: Get month if not set
            if month is None:
                month = self.get_month_input("2. Mês (obrigatório):")
                if month is None:  # ESC was pressed
                    year_config = None  # Go back to year selection
                    continue
                continue  # Refresh screen with new filter
            
            # Step 3: Get UF if not set
            if uf is None:
                uf = self.get_uf_input("3. Estado (UF):")
                if uf is None:  # ESC was pressed
                    month = None  # Go back to month selection
                    continue
                continue  # Refresh screen with new filter
            
            # Step 4: Get municipality if not set
            if municipality is None:
                municipality = self.get_municipality_input("4. Município:", uf)
                if municipality is None:  # ESC was pressed
                    uf = None  # Go back to UF selection
                    continue
                continue  # Refresh screen with new filter
            
            # All filters selected - show confirmation
            print("✓ Todos os filtros configurados!")
            print("")
            print("1. Iniciar coleta")
            print("2. Modificar ano")
            print("3. Modificar mês")
            print("4. Modificar estado")
            print("5. Modificar município")
            print("6. Voltar ao menu principal")
            print("")
            
            choice = self._get_key_input("Digite sua opção (1-6): ")
            
            if choice == self.ESC_PRESSED:
                return None  # Return to main menu
            elif choice == "1":
                config = {
                    'site': 'mds_saldo',
                    'year_config': year_config,
                    'month': month,
                    'uf': uf.upper(),
                    'municipality': municipality,
                    'url': self.site_info['url']
                }
                return config
            elif choice == "2":
                year_config = None  # Reset year to modify
            elif choice == "3":
                month = None  # Reset month to modify
            elif choice == "4":
                uf = None  # Reset UF to modify
                municipality = None  # Also reset municipality since it depends on UF
            elif choice == "5":
                municipality = None  # Reset municipality to modify
            elif choice == "6":
                return None
            else:
                self.terminal.show_error("Opção inválida. Tente novamente.")
    
    def get_year_input(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get and validate year input."""
        print(prompt)
        print("   Digite um ano específico (ex: 2024) ou:")
        print("   1 - Todos os anos disponíveis")
        print("   2 - Período de anos (ex: 2020-2024)")
        print("   3 - Anos diferentes (ex: 2020, 2022, 2024)")
        print("")
        
        year_str = self._get_key_input("   Digite sua opção: ")
        
        if year_str == self.ESC_PRESSED:
            return None  # Signal to go back
        
        # Check for options 1, 2 or 3
        if year_str == "1":
            return {'type': 'all'}
        elif year_str == "2":
            return self.get_year_range_input()
        elif year_str == "3":
            return self.get_multiple_years_input()
        
        # Try to parse as single year
        try:
            year = int(year_str)
            
            # Validate year (must be >= 2011)
            current_year = datetime.now().year
            if year < 2011:
                self.terminal.show_error("Ano deve ser igual ou maior que 2011.")
                return None
            elif year > current_year:
                self.terminal.show_error(f"Ano deve ser menor ou igual a {current_year}.")
                return None
            else:
                return {'type': 'single', 'year': year}
        except ValueError:
            self.terminal.show_error("Entrada invalida. Digite um numero ou opcao valida.")
            return None
    
    def get_year_range_input(self) -> Optional[Dict[str, Any]]:
        """Get year range input from user."""
        print("   Configurar período de anos:")
        print("")
        
        # Get start year
        start_year_str = self._get_key_input("   Ano de início (ex: 2020): ")
        if start_year_str == self.ESC_PRESSED:
            return None
        
        try:
            start_year = int(start_year_str)
        except ValueError:
            self.terminal.show_error("Ano de início inválido.")
            return None
        
        # Get end year  
        end_year_str = self._get_key_input("   Ano de fim (ex: 2024): ")
        if end_year_str == self.ESC_PRESSED:
            return None
        
        try:
            end_year = int(end_year_str)
        except ValueError:
            self.terminal.show_error("Ano de fim inválido.")
            return None
        
        # Validate range
        current_year = datetime.now().year
        
        if start_year < 2011:
            self.terminal.show_error("Ano de início deve ser igual ou maior que 2011.")
            return None
            
        if end_year > current_year:
            self.terminal.show_error(f"Ano de fim deve ser menor ou igual a {current_year}.")
            return None
            
        if start_year > end_year:
            self.terminal.show_error("Ano de início deve ser menor ou igual ao ano de fim.")
            return None
        
        print(f"   Período configurado: {start_year} até {end_year} ({end_year - start_year + 1} anos)")
        return {'type': 'range', 'start_year': start_year, 'end_year': end_year}
    
    def get_multiple_years_input(self) -> Optional[Dict[str, Any]]:
        """Get multiple years input from user."""
        print("   Digite anos separados por vírgula (ex: 2020, 2022, 2024):")
        print("")
        
        years_str = self._get_key_input("   Anos: ")
        if years_str == self.ESC_PRESSED:
            return None
        
        try:
            # Parse comma-separated years
            year_strings = [y.strip() for y in years_str.split(',')]
            years = []
            
            for year_str in year_strings:
                year = int(year_str)
                
                # Validate each year
                if year < 2011:
                    self.terminal.show_error(f"Ano {year} deve ser igual ou maior que 2011.")
                    return None
                elif year > datetime.now().year:
                    self.terminal.show_error(f"Ano {year} deve ser menor ou igual a {datetime.now().year}.")
                    return None
                    
                years.append(year)
            
            if not years:
                self.terminal.show_error("Pelo menos um ano válido deve ser informado.")
                return None
            
            # Remove duplicates and sort
            years = sorted(list(set(years)))
            
            print(f"   Anos configurados: {', '.join(map(str, years))} ({len(years)} anos)")
            return {'type': 'multiple', 'years': years}
            
        except ValueError:
            self.terminal.show_error("Formato inválido. Use números separados por vírgula (ex: 2020, 2022, 2024).")
            return None

    def get_month_input(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get and validate month input."""
        print(prompt)
        print("   Digite um mês específico ou:")
        print("   1) Janeiro    2) Fevereiro   3) Marco")
        print("   4) Abril      5) Maio        6) Junho")
        print("   7) Julho      8) Agosto      9) Setembro")
        print("   10) Outubro   11) Novembro   12) Dezembro")
        print("   13) Todos os meses")
        print("   14) Vários meses (ex: 1,3,5 ou 1-6)")
        print("")
        
        month_str = self._get_key_input("   Digite sua opcao: ")
        
        if month_str == self.ESC_PRESSED:
            return None  # Signal to go back
        
        # Check for option 14 (multiple months)
        if month_str == "14":
            return self.get_multiple_months_input()
        
        try:
            month = int(month_str)
            if 1 <= month <= 13:
                if month == 13:
                    return {'type': 'all'}
                else:
                    return {'type': 'single', 'month': month}
            else:
                self.terminal.show_error("Opcao deve estar entre 1 e 14.")
                return None
        except ValueError:
            self.terminal.show_error("Opcao invalida. Digite um numero.")
            return None
    
    def get_multiple_months_input(self) -> Optional[Dict[str, Any]]:
        """Get multiple months input from user."""
        print("   Configure vários meses:")
        print("   Exemplos:")
        print("   - Meses específicos: 1,3,5,7 (Jan, Mar, Mai, Jul)")
        print("   - Intervalo: 1-6 (Janeiro até Junho)")
        print("   - Combinado: 1,3,5-8,12 (Jan, Mar, Mai-Ago, Dez)")
        print("")
        
        months_str = self._get_key_input("   Digite os meses: ")
        if months_str == self.ESC_PRESSED:
            return None
        
        try:
            months = set()
            
            # Split by comma first
            parts = [part.strip() for part in months_str.split(',')]
            
            for part in parts:
                if '-' in part:
                    # Handle range (e.g., "1-6")
                    range_parts = part.split('-')
                    if len(range_parts) == 2:
                        start = int(range_parts[0].strip())
                        end = int(range_parts[1].strip())
                        
                        if start < 1 or start > 12 or end < 1 or end > 12:
                            self.terminal.show_error("Meses devem estar entre 1 e 12.")
                            return None
                        
                        if start > end:
                            self.terminal.show_error("Mês inicial deve ser menor ou igual ao final no intervalo.")
                            return None
                        
                        for month in range(start, end + 1):
                            months.add(month)
                    else:
                        self.terminal.show_error("Formato de intervalo inválido. Use formato 'início-fim' (ex: 1-6).")
                        return None
                else:
                    # Handle single month
                    month = int(part)
                    if month < 1 or month > 12:
                        self.terminal.show_error("Meses devem estar entre 1 e 12.")
                        return None
                    months.add(month)
            
            if not months:
                self.terminal.show_error("Pelo menos um mês válido deve ser informado.")
                return None
            
            # Convert to sorted list
            months_list = sorted(list(months))
            
            # Display confirmation
            month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                          'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            month_names_str = ', '.join([month_names[m-1] for m in months_list])
            print(f"   Meses configurados: {month_names_str} ({len(months_list)} meses)")
            
            return {'type': 'multiple', 'months': months_list}
            
        except ValueError:
            self.terminal.show_error("Formato inválido. Use números de 1-12, vírgulas e hífens (ex: 1,3,5-8,12).")
            return None
    
    def get_uf_input(self, prompt: str) -> Optional[str]:
        """Get and validate UF (state) input."""
        print(prompt)
        print("   Digite a sigla do estado desejado (ex: MG, SP, RJ):")
        print("")
        
        uf_str = self._get_key_input("   UF: ")
        
        if uf_str == self.ESC_PRESSED:
            return None  # Signal to go back
        
        uf = uf_str.upper().strip()
        
        if len(uf) != 2:
            self.terminal.show_error("UF deve ter exatamente 2 caracteres.")
            return None
        
        if uf not in self.valid_states:
            self.terminal.show_error(f"UF '{uf}' não é válida. Estados disponíveis: {', '.join(self.valid_states)}")
            return None
        
        return uf
    
    def get_municipality_input(self, prompt: str, uf: str) -> Optional[str]:
        """Get municipality input with AI auto-correction."""
        while True:  # Loop until valid input or ESC
            print(prompt)
            print(f"   Digite o nome do município desejado no estado {uf}:")
            print("   Ou digite 'TODOS' para selecionar todos os municípios do estado")
            print("")
            
            municipality_str = self._get_key_input("   Município: ")
            
            if municipality_str == self.ESC_PRESSED:
                return None  # Signal to go back
            
            municipality = municipality_str.strip()
            
            if not municipality:
                self.terminal.show_error("Nome do município não pode ser vazio.")
                continue  # Ask again
            
            # Special case for "all municipalities"
            if municipality.upper() in ['TODOS', 'ALL', 'TODAS']:
                return f"ALL_{uf}"
            
            # Use AI to correct municipality name
            try:
                corrector = get_municipality_corrector()
                corrected_name = corrector.correct_municipality_name(municipality, uf)
                
                if corrected_name == "erro4040":
                    self.terminal.show_error(f"Município '{municipality}' não existe no estado {uf}. Por favor, digite novamente.")
                    input("Pressione Enter para continuar...")
                    # Don't clear screen here, just continue the loop
                    print("")
                    continue  # Ask again
                
                # If correction was made, use the corrected name silently
                if corrected_name != municipality:
                    logger.info(f"Municipality name auto-corrected: '{municipality}' -> '{corrected_name}'")
                
                return corrected_name
                
            except Exception as e:
                logger.warning(f"Could not verify municipality name: {str(e)}")
                # On error, return the original input to not block the user
                return municipality
    
    def execute_complete_flow(self):
        """Execute complete MDS Saldo flow: config -> processing -> results."""
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
            logger.info(f"Iniciando scraping MDS Saldo: {config}")
            
            # Start interactive progress display
            progress.start()
            
            # Show initial status
            progress.show_status("Conectando ao site MDS", "Inicializando navegador")
            
            # Import and create scraper
            from src.modules.sites.mds_saldo import MDSSaldoScraper
            scraper = MDSSaldoScraper()
            
            # Execute scraping with progress updates
            result = self._execute_scraping_with_callbacks(scraper, config, progress)
            
            logger.info(f"Scraping finalizado: {result.get('success', False)}")
            
            # Capture real elapsed time before stopping progress display
            actual_elapsed_minutes = progress.get_elapsed_time()
            
            # Stop progress display and show results
            progress.stop()
            logger.disable_silent_mode()
            logger.end_session()
            
            if result.get('success', False):
                self.show_success_screen(result, actual_elapsed_minutes)
            else:
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
        completed_steps = ["Conectando ao site MDS"]
        
        # Authenticate
        progress.show_status("Fazendo autenticação", "Login no sistema", completed_steps)
        time.sleep(0.5)  # Simulate authentication time
        completed_steps.append("Fazendo autenticação")
        
        # Apply filters
        progress.show_status("Aplicando filtros", "Configurando parâmetros", completed_steps)
        
        # Create callback function to update progress
        def progress_callback(stage, detail):
            if stage == "querying_balance":
                completed_steps_copy = completed_steps + ["Aplicando filtros"]
                progress.show_status("Consultando saldo", detail, completed_steps_copy)
            elif stage == "collecting_data":
                completed_steps_copy = completed_steps + ["Aplicando filtros", "Consultando saldo"]
                progress.show_status("Coletando dados", detail, completed_steps_copy)
            elif stage == "processing":
                completed_steps_copy = completed_steps + ["Aplicando filtros", "Consultando saldo", "Coletando dados"]
                progress.show_status("Processando informações", detail, completed_steps_copy)
            elif stage == "saving":
                completed_steps_copy = completed_steps + ["Aplicando filtros", "Consultando saldo", "Coletando dados", "Processando informações"]
                progress.show_status("Salvando resultados", detail, completed_steps_copy)
        
        # Execute the actual scraping
        try:
            # Pass the callback if the scraper supports it
            if hasattr(scraper, 'execute_scraping'):
                # Try to pass callback if method signature supports it
                import inspect
                sig = inspect.signature(scraper.execute_scraping)
                if 'progress_callback' in sig.parameters:
                    result = scraper.execute_scraping(config, progress_callback=progress_callback)
                else:
                    result = scraper.execute_scraping(config)
            else:
                result = {'success': False, 'error': 'Scraper not implemented'}
            
            # Show final status
            if result.get('success'):
                completed_steps_final = ["Conectando ao site MDS", "Fazendo autenticação", "Aplicando filtros", 
                                        "Consultando saldo", "Coletando dados", "Processando informações", "Salvando resultados"]
                progress.show_status("Finalizando", "Processo concluído", completed_steps_final)
        
        except Exception as e:
            result = {'success': False, 'error': str(e)}
        
        return result
    
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
        print(f"- Registros coletados: {result.get('total_records', 0)}")
        print(f"- Tamanho total: {result.get('total_size_mb', 0):.1f} MB")
        
        # Use actual elapsed time from progress display if available, otherwise fallback to result time
        elapsed_time = actual_elapsed_minutes if actual_elapsed_minutes is not None else result.get('duration_minutes', 0)
        print(f"- Tempo decorrido: {elapsed_time:.1f} minutos")
        
        print("")
        print(f"Arquivos salvos em: {result.get('download_path', 'downloads/raw/mds_saldo/')}")
        print("")
        
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
        
        # Show specific help for common errors
        error_msg = result.get('error', '').lower()
        if 'conexão' in error_msg or 'timeout' in error_msg:
            print("Possíveis soluções:")
            print("- Verifique sua conexão com a internet")
            print("- Tente novamente em alguns minutos")
            print("- O site do MDS pode estar temporariamente indisponível")
        elif 'autenticação' in error_msg or 'login' in error_msg:
            print("Possíveis soluções:")
            print("- Verifique se o site não mudou seus mecanismos de autenticação")
            print("- O sistema pode estar em manutenção")
        
        print("")
        print("Arquivos parciais salvos em: downloads/raw/mds_saldo/temp/")
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
                path = "downloads/raw/mds_saldo/"
            
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
        print("Os logs contêm informações detalhadas sobre:")
        print("- Conexões com o site")
        print("- Autenticação")
        print("- Aplicação de filtros")
        print("- Erros de parsing")
        print("- Stack traces completos")
        print("")
        input("Pressione Enter para continuar...")
    
    def format_config_summary(self, config: Dict[str, Any]) -> str:
        """Format configuration summary for display."""
        parts = []
        
        # Handle year configuration
        year_config = config.get('year_config', {})
        if year_config.get('type') == 'single':
            parts.append(f"Ano: {year_config['year']}")
        elif year_config.get('type') == 'range':
            parts.append(f"Anos: {year_config['start_year']}-{year_config['end_year']}")
        elif year_config.get('type') == 'multiple':
            years_str = ', '.join(map(str, year_config['years']))
            parts.append(f"Anos: {years_str}")
        elif year_config.get('type') == 'all':
            parts.append("Anos: Todos")
        
        # Handle month
        if 'month' in config:
            month = config['month']
            if isinstance(month, dict):
                if month.get('type') == 'all':
                    parts.append("Mês: Todos")
                elif month.get('type') == 'single':
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    parts.append(f"Mês: {month_names[month['month']-1]}")
                elif month.get('type') == 'multiple':
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    months_str = ', '.join([month_names[m-1] for m in month['months']])
                    parts.append(f"Meses: {months_str}")
            else:
                # Legacy support for integer month values
                if month == 13:
                    parts.append("Mês: Todos")
                elif 1 <= month <= 12:
                    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                    parts.append(f"Mês: {month_names[month-1]}")
        
        # Handle UF
        if 'uf' in config:
            parts.append(f"UF: {config['uf']}")
        
        # Handle municipality
        if 'municipality' in config:
            municipality = config['municipality']
            if municipality.startswith('ALL_'):
                uf = municipality.split('_')[1]
                parts.append(f"Municipio: Todos de {uf}")
            else:
                parts.append(f"Municipio: {municipality}")
        
        return ", ".join(parts)