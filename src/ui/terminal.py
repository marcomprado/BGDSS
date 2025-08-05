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

from src.utils.logger import logger

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
                'name': 'Portal Saude MG - Resoluções',
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
        print("    WEB SCRAPER AUTOMATIZADO")
        print("========================================")
        print("")
        print("Selecione o site para coleta de dados:")
        print("")
        print("1. Portal Saude MG - Resoluções")
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
            print("   PORTAL SAUDE MG - RESOLUÇÕES")
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
            
            # Handle year range input
            year_range = None
            if year == 998:  # Intervalo personalizado de anos
                year_range = self.get_year_range_input()
                if year_range is None:
                    continue
                
            # Get month
            month = self.get_month_input("2. Mes:")
            if month is None:
                continue
                
            # Handle month range input
            month_range = None
            if month == 14:  # Intervalo personalizado de meses
                month_range = self.get_month_range_input()
                if month_range is None:
                    continue
            
            print("")
            print("1. Iniciar coleta")
            print("2. Voltar ao menu principal")
            print("")
            
            choice = self.get_user_input("Digite sua opcao (1-2): ")
            
            if choice == "1":
                config = {
                    'site': 'portal_saude_mg',
                    'year': year,
                    'month': month,
                    'url': self.sites[1]['url']
                }
                
                # Add range information if available
                if year_range:
                    config['year_range'] = year_range
                if month_range:
                    config['month_range'] = month_range
                
                self.current_config = config  # Store config for later reference
                self.run_scraping_task(config)
                break
            elif choice == "2":
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
            print("1. Iniciar coleta")
            print("2. Voltar ao menu principal")
            print("")
            
            choice = self.get_user_input("Digite sua opcao (1-2): ")
            
            if choice == "1":
                config = {
                    'site': 'mds_parcelas',
                    'year': year,
                    'municipality': municipality,
                    'url': self.sites[2]['url']
                }
                self.current_config = config  # Store config for later reference
                self.run_scraping_task(config)
                break
            elif choice == "2":
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
        print("   Digite um ano específico (ex: 2024) ou:")
        print("   1 - Todos os anos disponíveis")
        print("   2 - Intervalo personalizado de anos")
        print("")
        year_str = self.get_user_input("   Digite sua opção: ")
        
        try:
            year = int(year_str)
            
            # Special case for "all years"
            if year == 1:
                return 999  # Keep internal value as 999
            
            # Special case for "year range"
            if year == 2:
                return 998  # Keep internal value as 998
            
            # Allow any reasonable year (from 2000 to current year + 20)
            from datetime import datetime
            current_year = datetime.now().year
            if 2000 <= year <= current_year + 20:
                return year
            else:
                self.show_error(f"Ano deve estar entre 2000 e {current_year + 20}, 1 para todos os anos, ou 2 para intervalo.")
                return None
        except ValueError:
            self.show_error("Entrada invalida. Digite um numero.")
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

    def get_year_range_input(self) -> Optional[tuple]:
        """Get year range input from user."""
        print("   Configurar intervalo de anos:")
        print("")
        
        # Get start year
        start_year_str = self.get_user_input("   Ano de início (ex: 2010): ")
        try:
            start_year = int(start_year_str)
        except ValueError:
            self.show_error("Ano de início inválido.")
            return None
        
        # Get end year  
        end_year_str = self.get_user_input("   Ano de fim (ex: 2014): ")
        try:
            end_year = int(end_year_str)
        except ValueError:
            self.show_error("Ano de fim inválido.")
            return None
        
        # Validate range
        from datetime import datetime
        current_year = datetime.now().year
        
        if not (2000 <= start_year <= current_year + 20):
            self.show_error(f"Ano de início deve estar entre 2000 e {current_year + 20}.")
            return None
            
        if not (2000 <= end_year <= current_year + 20):
            self.show_error(f"Ano de fim deve estar entre 2000 e {current_year + 20}.")
            return None
            
        if start_year > end_year:
            self.show_error("Ano de início deve ser menor ou igual ao ano de fim.")
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
        start_month_str = self.get_user_input("   Mês de início (1-12): ")
        try:
            start_month = int(start_month_str)
            if not (1 <= start_month <= 12):
                self.show_error("Mês de início deve estar entre 1 e 12.")
                return None
        except ValueError:
            self.show_error("Mês de início inválido.")
            return None
        
        # Get end month
        end_month_str = self.get_user_input("   Mês de fim (1-12): ")
        try:
            end_month = int(end_month_str)
            if not (1 <= end_month <= 12):
                self.show_error("Mês de fim deve estar entre 1 e 12.")
                return None
        except ValueError:
            self.show_error("Mês de fim inválido.")
            return None
        
        # Validate range
        if start_month > end_month:
            self.show_error("Mês de início deve ser menor ou igual ao mês de fim.")
            return None
        
        month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        start_name = month_names[start_month - 1]
        end_name = month_names[end_month - 1]
        
        print(f"   Intervalo configurado: {start_name} até {end_name} ({end_month - start_month + 1} meses)")
        return (start_month, end_month)

    def run_scraping_task(self, config: Dict[str, Any]):
        """Run the scraping task with progress tracking."""
        self.show_processing_screen(config)
        
        try:
            # Import and run the appropriate scraper
            if config['site'] == 'portal_saude_mg':
                from src.modules.sites.portal_saude_mg import PortalSaudeMGScraper
                scraper = PortalSaudeMGScraper()
                
                # Handle range-based processing
                if config.get('year_range') or config.get('month_range'):
                    print("\nProcessando intervalo personalizado...")
                    result = self.process_custom_range(scraper, config)
                    
                elif config['year'] == 999:  # Todos os anos
                    print("\nProcessando todos os anos disponíveis...")
                    result = self.process_all_years(scraper, config)
                    
                elif config.get('month') == 13:  # Todos os meses de um ano específico
                    ano = str(config['year'])
                    print(f"\nProcessando todos os meses de {ano}...")
                    result = self.process_all_months_for_year(scraper, ano)
                    
                else:
                    # Ano e mês específicos (comportamento original)
                    ano = str(config['year'])
                    mes = f"{config['month']:02d}" if config.get('month') else None
                    result = scraper.execute_scraping(ano, mes)
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
        print(f"- Tempo decorrido: {result.get('duration_minutes', 0):.1f} minutos")
        
        # Mostrar resumo adicional se disponível
        if result.get('summary'):
            print(f"- Resumo: {result.get('summary')}")
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

    def process_custom_range(self, scraper, config: Dict[str, Any]) -> Dict[str, Any]:
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
            print(f"\\nIntervalo de anos: {start_year} até {end_year} ({len(years_to_process)} anos)")
        else:
            # Single year from config
            years_to_process = [config['year']]
        
        # Determine months to process
        if month_range:
            start_month, end_month = month_range
            months_to_process = list(range(start_month, end_month + 1))
            month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                          'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            start_name = month_names[start_month - 1]
            end_name = month_names[end_month - 1]
            print(f"Intervalo de meses: {start_name} até {end_name} ({len(months_to_process)} meses)")
        elif config.get('month') == 13:
            # All months
            months_to_process = list(range(1, 13))
        else:
            # Single month or None
            months_to_process = [config.get('month')] if config.get('month') else [None]
        
        print(f"\\nTotal de períodos a processar: {len(years_to_process) * len(months_to_process)}")
        print("\\n" + "="*50)
        
        # Process each year
        for year_idx, year in enumerate(years_to_process):
            ano = str(year)
            print(f"\\n=== [{year_idx + 1}/{len(years_to_process)}] PROCESSANDO ANO {year} ===")
            
            year_files = 0
            year_months_processed = 0
            
            # Process each month for this year
            for month_idx, month in enumerate(months_to_process):
                if month is None:
                    # No specific month
                    try:
                        print(f"   Processando {ano} (todos os meses)...")
                        result = scraper.execute_scraping(ano, None)
                        
                        files_count = len(result.get('files_downloaded', []))
                        if files_count > 0:
                            print(f"   ✅ {ano}: {files_count} arquivos baixados")
                            all_range_results.append(result)
                            total_files_found += files_count
                            periods_processed += 1
                        else:
                            print(f"   ⚪ {ano}: Nenhum arquivo encontrado")
                            
                    except Exception as e:
                        print(f"   ❌ Erro em {ano}: {str(e)}")
                        continue
                else:
                    # Specific month
                    mes = f"{month:02d}"
                    month_name = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                                 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][month - 1]
                    
                    try:
                        print(f"   [{month_idx + 1}/{len(months_to_process)}] Processando {month_name}/{ano}...")
                        result = scraper.execute_scraping(ano, mes)
                        
                        files_count = len(result.get('files_downloaded', []))
                        if files_count > 0:
                            print(f"      ✅ {month_name}/{ano}: {files_count} arquivos baixados")
                            all_range_results.append(result)
                            total_files_found += files_count
                            year_files += files_count
                            year_months_processed += 1
                            periods_processed += 1
                        else:
                            print(f"      ⚪ {month_name}/{ano}: Nenhum arquivo encontrado")
                            # For future months, stop processing this year
                            from datetime import datetime
                            if year == years_to_process[-1] and month > datetime.now().month:
                                print(f"      🛑 Mês futuro detectado - parando este ano")
                                break
                                
                    except Exception as e:
                        print(f"      ❌ Erro em {month_name}/{ano}: {str(e)}")
                        continue
            
            # Year summary
            if months_to_process != [None]:  # Only if processing specific months
                print(f"   📊 Resumo {ano}: {year_files} arquivos em {year_months_processed} meses")
        
        # Consolidate results
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

    def process_all_years(self, scraper, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process all available years, cycling through each year and month."""
        from datetime import datetime
        current_year = datetime.now().year
        
        print("\nIniciando busca em todos os anos (2000 até atual)...")
        all_year_results = []
        total_files_found = 0
        years_processed = 0
        years_with_data = []
        
        # Começar do ano atual e voltar no tempo (mais eficiente)
        for year in range(current_year, 1999, -1):
            ano = str(year)
            print(f"\n=== PROCESSANDO ANO {year} ===")
            
            try:
                if config.get('month') == 13:  # Todos os meses para este ano
                    year_result = self.process_all_months_for_year(scraper, ano)
                else:
                    # Mês específico para este ano
                    mes = f"{config['month']:02d}" if config.get('month') else None
                    year_result = scraper.execute_scraping(ano, mes)
                
                files_in_year = len(year_result.get('files_downloaded', []))
                
                if files_in_year > 0:
                    print(f"   ✅ Ano {year}: {files_in_year} arquivos encontrados")
                    all_year_results.append(year_result)
                    total_files_found += files_in_year
                    years_processed += 1
                    years_with_data.append(year)
                else:
                    print(f"   ⚪ Ano {year}: Nenhum arquivo encontrado")
                    
                    # Se não encontrar dados por 3 anos consecutivos, parar
                    if len(years_with_data) > 0 and (years_with_data[-1] - year) > 3:
                        print(f"   🛑 Sem dados por mais de 3 anos consecutivos - parando busca")
                        break
                        
            except Exception as e:
                print(f"   ❌ Erro no ano {year}: {str(e)}")
                continue
        
        # Consolidar resultados de todos os anos
        return self.consolidate_yearly_results(all_year_results, years_processed, total_files_found, years_with_data)
    
    def process_all_months_for_year(self, scraper, ano: str) -> Dict[str, Any]:
        """Process all months for a specific year."""
        all_results = []
        total_files_found = 0
        months_processed = 0
        
        month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                     'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        for month_num in range(1, 13):  # Janeiro a dezembro
            mes = f"{month_num:02d}"
            month_name = month_names[month_num - 1]
            
            print(f"   [{month_num}/12] Processando {month_name} ({mes}/{ano})...")
            
            try:
                result = scraper.execute_scraping(ano, mes)
                
                # Parar se não houver links (provável mês futuro)
                if result.get('total_files', 0) == 0:
                    print(f"      Nenhum resultado encontrado para {month_name} - parando meses")
                    break
                
                files_count = len(result.get('files_downloaded', []))
                print(f"      ✅ {month_name}: {files_count} arquivos baixados")
                
                all_results.append(result)
                total_files_found += files_count
                months_processed += 1
                
            except Exception as e:
                print(f"      ❌ Erro em {month_name}: {str(e)}")
                continue
        
        # Consolidar resultados de todos os meses para este ano
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