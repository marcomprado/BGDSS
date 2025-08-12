#!/usr/bin/env python3
"""
MDS Parcelas Pagas Terminal Interface

Interface específica para o MDS - Parcelas Pagas com funcionalidades de seleção
de ano, estado (UF) e município.
"""

import sys
import select
import termios
import tty
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.utils.logger import logger, set_context


class MDSParcelasUI:
    """
    Interface do usuário específica para MDS Parcelas Pagas.
    """
    
    def __init__(self, terminal_instance):
        self.terminal = terminal_instance
        self.ESC_PRESSED = "__ESC_PRESSED__"
        self.current_config = {}
        
        # Site info
        self.site_info = {
            'name': 'MDS - Parcelas Pagas',
            'url': 'https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*dpotvmubsQbsdfmbtQbhbtNC&event=*fyjcjs',
            'handler': 'mds_parcelas'
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
    
    def show_selected_filters(self, year_config=None, uf=None, municipality=None):
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
        """Show MDS Parcelas Pagas configuration screen."""
        year_config = None
        uf = None
        municipality = None
        
        while True:
            self.terminal.clear_screen()
            print("========================================")
            print("      MDS - PARCELAS PAGAS")
            print("========================================")
            print("")
            self.show_selected_filters(year_config, uf, municipality)
            print("Site: aplicacoes.mds.gov.br/suaswebcons")
            print("")
            print("Configure os filtros para consulta:")
            print("")
            
            # Step 1: Get year if not set
            if year_config is None:
                year_config = self.get_year_input("1. Ano (obrigatório, >= 2006):")
                if year_config is None:  # invalid input or ESC
                    return None  # Return to main menu
                continue  # Refresh screen with new filter
            
            # Step 2: Get UF if not set
            if uf is None:
                uf = self.get_uf_input("2. Estado (UF):")
                if uf is None:  # ESC was pressed
                    year_config = None  # Go back to year selection
                    continue
                continue  # Refresh screen with new filter
            
            # Step 3: Get municipality if not set
            if municipality is None:
                municipality = self.get_municipality_input("3. Município:", uf)
                if municipality is None:  # ESC was pressed
                    uf = None  # Go back to UF selection
                    continue
                continue  # Refresh screen with new filter
            
            # All filters selected - show confirmation
            print("✓ Todos os filtros configurados!")
            print("")
            print("1. Iniciar coleta")
            print("2. Modificar ano")
            print("3. Modificar estado")
            print("4. Modificar município")
            print("5. Voltar ao menu principal")
            print("")
            
            choice = self._get_key_input("Digite sua opção (1-5): ")
            
            if choice == self.ESC_PRESSED:
                return None  # Return to main menu
            elif choice == "1":
                config = {
                    'site': 'mds_parcelas',
                    'year_config': year_config,
                    'uf': uf.upper(),
                    'municipality': municipality,
                    'url': self.site_info['url']
                }
                return config
            elif choice == "2":
                year_config = None  # Reset year to modify
            elif choice == "3":
                uf = None  # Reset UF to modify
                municipality = None  # Also reset municipality since it depends on UF
            elif choice == "4":
                municipality = None  # Reset municipality to modify
            elif choice == "5":
                return None
            else:
                self.terminal.show_error("Opção inválida. Tente novamente.")
    
    def get_year_input(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Get and validate year input."""
        print(prompt)
        print("   Digite um ano específico (ex: 2024) ou:")
        print("   1 - Período de anos (ex: 2020-2024)")
        print("   2 - Anos diferentes (ex: 2020, 2022, 2024)")
        print("")
        
        year_str = self._get_key_input("   Digite sua opção: ")
        
        if year_str == self.ESC_PRESSED:
            return None  # Signal to go back
        
        # Check for options 1 or 2
        if year_str == "1":
            return self.get_year_range_input()
        elif year_str == "2":
            return self.get_multiple_years_input()
        
        # Try to parse as single year
        try:
            year = int(year_str)
            
            # Validate year (must be >= 2006)
            current_year = datetime.now().year
            if year < 2006:
                self.terminal.show_error("Ano deve ser igual ou maior que 2006.")
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
        
        if start_year < 2006:
            self.terminal.show_error("Ano de início deve ser igual ou maior que 2006.")
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
                if year < 2006:
                    self.terminal.show_error(f"Ano {year} deve ser igual ou maior que 2006.")
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
        """Get municipality input."""
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
            return None
        
        # Special case for "all municipalities"
        if municipality.upper() in ['TODOS', 'ALL', 'TODAS']:
            return f"ALL_{uf}"
        
        return municipality
    
    def execute_complete_flow(self):
        """Execute complete MDS Parcelas flow: config -> processing -> results."""
        config = self.show_config_screen()
        if config:
            self.current_config = config
            self.run_scraping_task(config)
    
    def run_scraping_task(self, config: Dict[str, Any]):
        """Run the scraping task."""
        self.show_processing_screen(config)
        
        try:
            # Start logging session
            logger.start_session(f"{config['site']}_scraping")
            set_context(site=config['site'])
            
            logger.info(f"Iniciando scraping MDS Parcelas: {config}")
            
            # Import and run the MDS Parcelas scraper
            from src.modules.sites.mds_parcelas import MDSParcelasScraper
            scraper = MDSParcelasScraper()
            result = scraper.execute_scraping(config)
            
            logger.info(f"Scraping finalizado: {result.get('success', False)}")
            logger.end_session()
            
            if result.get('success', False):
                self.show_success_screen(result)
            else:
                self.show_error_screen(result)
                
        except Exception as e:
            logger.error(f"Erro fatal durante scraping: {str(e)}")
            logger.exception("Stack trace completo:")
            logger.end_session()
            
            error_result = {
                'success': False,
                'error': str(e),
                'site': config['site']
            }
            self.show_error_screen(error_result)
    
    def show_processing_screen(self, config: Dict[str, Any]):
        """Show processing screen with progress indicators."""
        self.terminal.clear_screen()
        print("========================================")
        print("           EM PROCESSAMENTO")
        print("========================================")
        print("")
        print(f"Site: {self.site_info['name']}")
        print(f"Configuracao: {self.format_config_summary(config)}")
        print("")
        print("Status atual: Iniciando processo...")
        print("")
        
        # Show progress steps
        steps = [
            "Conectando ao site MDS",
            "Fazendo login/autenticação", 
            "Aplicando filtros",
            "Coletando dados",
            "Processando informações",
            "Salvando resultados",
            "Finalizando"
        ]
        
        for step in steps:
            print(f"[ ] {step}")
        
        print("")
        print("Aguarde... O processo pode levar alguns minutos.")
        print("• Autenticação: 30-60 segundos")
        print("• Coleta de dados: 1-5 minutos (depende dos filtros)")
        print("")
        print("Pressione Ctrl+C para cancelar")
    
    def show_success_screen(self, result: Dict[str, Any]):
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
        print(f"- Tempo decorrido: {result.get('duration_minutes', 0):.1f} minutos")
        print("")
        print(f"Arquivos salvos em: {result.get('download_path', 'downloads/raw/mds_parcelas/')}")
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
        print("Arquivos parciais salvos em: downloads/raw/mds_parcelas/temp/")
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
                path = "downloads/raw/mds_parcelas/"
            
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