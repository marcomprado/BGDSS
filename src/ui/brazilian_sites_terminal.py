#!/usr/bin/env python3
"""
Brazilian Government Sites Terminal Interface

Simple, focused terminal interface for extracting data from three Brazilian government sites:
1. Portal Saude MG - Deliberações
2. MDS - Parcelas Pagas  
3. MDS - Saldo Detalhado por Conta

This interface provides the exact user experience specified in the requirements.
"""

import os
import sys
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

class BrazilianSitesTerminal:
    """
    Main terminal interface for Brazilian government sites data extraction.
    """
    
    def __init__(self):
        self.current_site = None
        self.current_config = {}
        self.running = True
        
        # Site definitions
        self.sites = {
            1: {
                'name': 'Portal Saude MG - Deliberacoes',
                'url': 'https://portal-antigo.saude.mg.gov.br/deliberacoes/documents?by_year=0&by_month=&by_format=pdf&category_id=4795&ordering=newest&q=',
                'handler': 'portal_saude_mg'
            },
            2: {
                'name': 'MDS - Parcelas Pagas',
                'url': 'https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*dpotvmubsQbsdfmbtQbhbtNC&event=*fyjcjs',
                'handler': 'mds_parcelas'
            },
            3: {
                'name': 'MDS - Saldo Detalhado por Conta',
                'url': 'https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*tbmepQbsdfmbtQbhbtNC&event=*fyjcjs',
                'handler': 'mds_saldo'
            }
        }

    def start(self) -> Dict[str, Any]:
        """Start the terminal interface."""
        try:
            while self.running:
                self.show_main_menu()
                choice = self.get_user_input("Digite sua opcao (1-4): ")
                
                try:
                    choice_num = int(choice)
                    if choice_num == 4:
                        self.running = False
                        return {'status': 'exit', 'message': 'Saindo...'}
                    elif choice_num in [1, 2, 3]:
                        self.handle_site_selection(choice_num)
                    else:
                        self.show_error("Opcao invalida. Tente novamente.")
                except ValueError:
                    self.show_error("Opcao invalida. Tente novamente.")
                    
            return {'status': 'completed'}
            
        except KeyboardInterrupt:
            return {'status': 'interrupted', 'message': 'Processo interrompido pelo usuario'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def show_main_menu(self):
        """Show the main menu."""
        self.clear_screen()
        print("========================================")
        print("    WEB SCRAPER AUTOMATIZADO - IA")
        print("========================================")
        print("")
        print("Selecione o site para coleta de dados:")
        print("")
        print("1. Portal Saude MG - Deliberacoes")
        print("2. MDS - Parcelas Pagas")
        print("3. MDS - Saldo Detalhado por Conta")
        print("4. Sair")
        print("")

    def handle_site_selection(self, site_num: int):
        """Handle site selection and show configuration screen."""
        self.current_site = site_num
        site_info = self.sites[site_num]
        
        if site_num == 1:
            self.show_portal_saude_config()
        elif site_num == 2:
            self.show_mds_parcelas_config()
        elif site_num == 3:
            self.show_mds_saldo_config()

    def show_portal_saude_config(self):
        """Show Portal Saude MG configuration screen."""
        while True:
            self.clear_screen()
            print("========================================")
            print("   PORTAL SAUDE MG - DELIBERACOES")
            print("========================================")
            print("")
            print("Site: portal-antigo.saude.mg.gov.br/deliberacoes")
            print("")
            print("Configuracoes automaticas aplicadas:")
            print("- Formato: PDF")
            print("- Categoria: Resolucoes")
            print("- Ordenacao: Mais recente")
            print("")
            print("Configure os filtros:")
            print("")
            
            # Get year
            year = self.get_year_input("1. Ano (obrigatorio):")
            if year is None:
                continue
                
            # Get month
            month = self.get_month_input("2. Mes:")
            if month is None:
                continue
            
            print("")
            print("3. Iniciar coleta")
            print("4. Voltar ao menu principal")
            print("")
            
            choice = self.get_user_input("Digite sua opcao (3-4): ")
            
            if choice == "3":
                config = {
                    'site': 'portal_saude_mg',
                    'year': year,
                    'month': month,
                    'url': self.sites[1]['url']
                }
                self.current_config = config  # Store config for later reference
                self.run_scraping_task(config)
                break
            elif choice == "4":
                break
            else:
                self.show_error("Opcao invalida. Tente novamente.")

    def show_mds_parcelas_config(self):
        """Show MDS Parcelas Pagas configuration screen."""
        while True:
            self.clear_screen()
            print("========================================")
            print("      MDS - PARCELAS PAGAS")
            print("========================================")
            print("")
            print("Site: aplicacoes.mds.gov.br/suaswebcons")
            print("")
            print("Configuracoes automaticas aplicadas:")
            print("- UF: MG")
            print("- Esfera Administrativa: Municipal")
            print("")
            print("Configure os filtros:")
            print("")
            
            # Get year
            year = self.get_year_input("1. Ano (obrigatorio):")
            if year is None:
                continue
            
            # Get municipality option
            print("2. Municipio:")
            print("   1) Digitar nome do municipio")
            print("   2) Processar todos os municipios de MG")
            print("")
            
            mun_choice = self.get_user_input("   Digite sua opcao (1-2): ")
            
            municipality = None
            if mun_choice == "1":
                municipality = self.get_user_input("   Digite o nome do municipio: ").strip()
                if not municipality:
                    self.show_error("Nome do municipio e obrigatorio.")
                    continue
            elif mun_choice == "2":
                municipality = "ALL_MG"
            else:
                self.show_error("Opcao invalida.")
                continue
            
            print("")
            print("3. Iniciar coleta")
            print("4. Voltar ao menu principal")
            print("")
            
            choice = self.get_user_input("Digite sua opcao (3-4): ")
            
            if choice == "3":
                config = {
                    'site': 'mds_parcelas',
                    'year': year,
                    'municipality': municipality,
                    'url': self.sites[2]['url']
                }
                self.current_config = config  # Store config for later reference
                self.run_scraping_task(config)
                break
            elif choice == "4":
                break
            else:
                self.show_error("Opcao invalida. Tente novamente.")

    def show_mds_saldo_config(self):
        """Show MDS Saldo Detalhado configuration screen."""
        while True:
            self.clear_screen()
            print("========================================")
            print("    MDS - SALDO DETALHADO POR CONTA")
            print("========================================")
            print("")
            print("Site: aplicacoes.mds.gov.br/suaswebcons")
            print("")
            print("Configuracoes automaticas aplicadas:")
            print("- UF: MG")
            print("- Esfera Administrativa: Municipal")
            print("")
            print("Configure os filtros:")
            print("")
            
            # Get year
            year = self.get_year_input("1. Ano (obrigatorio):")
            if year is None:
                continue
            
            # Get month (required for this site)
            month = self.get_month_input("2. Mes (obrigatorio):", required=True)
            if month is None:
                continue
            
            # Get municipality option
            print("3. Municipio:")
            print("   1) Digitar nome do municipio")
            print("   2) Processar todos os municipios de MG")
            print("")
            
            mun_choice = self.get_user_input("   Digite sua opcao (1-2): ")
            
            municipality = None
            if mun_choice == "1":
                municipality = self.get_user_input("   Digite o nome do municipio: ").strip()
                if not municipality:
                    self.show_error("Nome do municipio e obrigatorio.")
                    continue
            elif mun_choice == "2":
                municipality = "ALL_MG"
            else:
                self.show_error("Opcao invalida.")
                continue
            
            print("")
            print("4. Iniciar coleta")
            print("5. Voltar ao menu principal")
            print("")
            
            choice = self.get_user_input("Digite sua opcao (4-5): ")
            
            if choice == "4":
                config = {
                    'site': 'mds_saldo',
                    'year': year,
                    'month': month,
                    'municipality': municipality,
                    'url': self.sites[3]['url']
                }
                self.current_config = config  # Store config for later reference
                self.run_scraping_task(config)
                break
            elif choice == "5":
                break
            else:
                self.show_error("Opcao invalida. Tente novamente.")

    def get_year_input(self, prompt: str) -> Optional[int]:
        """Get and validate year input."""
        print(prompt)
        year_str = self.get_user_input("   Digite o ano (ex: 2024): ")
        
        try:
            year = int(year_str)
            if 2015 <= year <= 2024:
                return year
            else:
                self.show_error("Ano deve estar entre 2015 e 2024.")
                return None
        except ValueError:
            self.show_error("Ano invalido. Digite um numero.")
            return None

    def get_month_input(self, prompt: str, required: bool = False) -> Optional[int]:
        """Get and validate month input."""
        print(prompt)
        if not required:
            print("   1) Janeiro    2) Fevereiro   3) Marco")
            print("   4) Abril      5) Maio        6) Junho")
            print("   7) Julho      8) Agosto      9) Setembro")
            print("   10) Outubro   11) Novembro   12) Dezembro")
            print("   13) Todos os meses")
        else:
            print("   1) Janeiro    2) Fevereiro   3) Marco")
            print("   4) Abril      5) Maio        6) Junho")
            print("   7) Julho      8) Agosto      9) Setembro")
            print("   10) Outubro   11) Novembro   12) Dezembro")
        
        print("")
        max_option = 13 if not required else 12
        month_str = self.get_user_input(f"   Digite sua opcao (1-{max_option}): ")
        
        try:
            month = int(month_str)
            if 1 <= month <= max_option:
                return month
            else:
                self.show_error(f"Opcao deve estar entre 1 e {max_option}.")
                return None
        except ValueError:
            self.show_error("Opcao invalida. Digite um numero.")
            return None

    def run_scraping_task(self, config: Dict[str, Any]):
        """Run the scraping task with progress tracking."""
        self.show_processing_screen(config)
        
        try:
            # Import and run the appropriate scraper
            if config['site'] == 'portal_saude_mg':
                from src.modules.sites.portal_saude_mg import PortalSaudeMGScraper
                scraper = PortalSaudeMGScraper()
                result = scraper.execute_scraping(config)
            elif config['site'] == 'mds_parcelas':
                from src.modules.sites.mds_parcelas import MDSParcelasScraper
                scraper = MDSParcelasScraper()
                result = scraper.execute_scraping(config)
            elif config['site'] == 'mds_saldo':
                from src.modules.sites.mds_saldo import MDSSaldoScraper
                scraper = MDSSaldoScraper()
                result = scraper.execute_scraping(config)
            else:
                raise ValueError(f"Unknown site: {config['site']}")
            
            if result.get('success', False):
                self.show_success_screen(result)
            else:
                self.show_error_screen(result)
                
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'site': config['site']
            }
            self.show_error_screen(error_result)

    def show_processing_screen(self, config: Dict[str, Any]):
        """Show processing screen with progress indicators."""
        self.clear_screen()
        print("========================================")
        print("           EM PROCESSAMENTO")
        print("========================================")
        print("")
        print(f"Site: {self.sites[self.current_site]['name']}")
        print(f"Configuracao: {self.format_config_summary(config)}")
        print("")
        print("Status atual: Iniciando processo...")
        print("")
        
        # Show progress steps
        steps = [
            "Conectando ao site",
            "Aplicando filtros", 
            "Coletando links de download",
            "Baixando arquivos",
            "Processando dados",
            "Finalizando"
        ]
        
        for i, step in enumerate(steps):
            print(f"[ ] {step}")
        
        print("")
        print("Aguarde... O processo pode levar alguns minutos.")
        print("")
        print("Pressione Ctrl+C para cancelar")

    def show_success_screen(self, result: Dict[str, Any]):
        """Show success screen with results."""
        self.clear_screen()
        print("========================================")
        print("         PROCESSO CONCLUIDO")
        print("========================================")
        print("")
        print("Status: SUCESSO")
        print("")
        print("Resumo da coleta:")
        print(f"- Site processado: {self.sites[self.current_site]['name']}")
        print(f"- Filtros aplicados: {self.format_config_summary(self.current_config)}")
        print(f"- Arquivos coletados: {result.get('files_downloaded', 0)} arquivos")
        print(f"- Tamanho total: {result.get('total_size_mb', 0):.1f} MB")
        print(f"- Tempo decorrido: {result.get('duration_minutes', 0):.1f} minutos")
        print("")
        print(f"Arquivos salvos em: {result.get('download_path', 'downloads/')}")
        print("")
        print("1. Abrir pasta de downloads")
        print("2. Processar outro site")
        print("3. Sair")
        print("")
        
        choice = self.get_user_input("Digite sua opcao (1-3): ")
        
        if choice == "1":
            self.open_downloads_folder(result.get('download_path'))
        elif choice == "2":
            return
        elif choice == "3":
            self.running = False

    def show_error_screen(self, result: Dict[str, Any]):
        """Show error screen."""
        self.clear_screen()
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
        
        choice = self.get_user_input("Digite sua opcao (1-4): ")
        
        if choice == "1":
            if self.current_config:
                self.run_scraping_task(self.current_config)
            else:
                self.show_error("Configuracao nao encontrada. Retornando ao menu principal.")
        elif choice == "2":
            return
        elif choice == "3":
            self.show_error_logs()
        elif choice == "4":
            self.running = False

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
        self.clear_screen()
        print("========================================")
        print("         LOGS DE ERRO")
        print("========================================")
        print("")
        print("Logs detalhados salvos em: logs/")
        print("")
        print("Para análise técnica, verifique os arquivos de log.")
        print("")
        input("Pressione Enter para continuar...")

    def format_config_summary(self, config: Dict[str, Any]) -> str:
        """Format configuration summary for display."""
        parts = []
        
        if 'year' in config:
            parts.append(f"Ano: {config['year']}")
        
        if 'month' in config and config['month'] != 13:
            months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                     'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            if 1 <= config['month'] <= 12:
                parts.append(f"Mes: {months[config['month']-1]}")
        elif config.get('month') == 13:
            parts.append("Mes: Todos")
        
        if 'municipality' in config:
            if config['municipality'] == 'ALL_MG':
                parts.append("Municipio: Todos de MG")
            else:
                parts.append(f"Municipio: {config['municipality']}")
        
        return ", ".join(parts)

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_user_input(self, prompt: str) -> str:
        """Get user input with prompt."""
        return input(prompt).strip()

    def show_error(self, message: str):
        """Show error message and wait for user."""
        print(f"\nErro: {message}")
        input("Pressione Enter para continuar...")


def run_brazilian_sites_terminal():
    """Run the Brazilian sites terminal interface."""
    terminal = BrazilianSitesTerminal()
    return terminal.start()


if __name__ == "__main__":
    result = run_brazilian_sites_terminal()
    print(f"Terminal encerrado: {result}")