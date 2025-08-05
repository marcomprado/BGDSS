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
from typing import Dict, Any

from .portal_saude_ui import PortalSaudeUI
from .mds_parcelas_ui import MDSParcelasUI
from .mds_saldo_ui import MDSSaldoUI


class BrazilianSitesTerminal:
    """
    Main terminal interface for Brazilian government sites data extraction.
    """
    
    def __init__(self):
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
        
        # Initialize UI components
        self.portal_saude_ui = PortalSaudeUI(self)
        self.mds_parcelas_ui = MDSParcelasUI(self)
        self.mds_saldo_ui = MDSSaldoUI(self)

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
        """Handle site selection and delegate to appropriate UI."""
        if site_num == 1:
            self.portal_saude_ui.execute_complete_flow()
        elif site_num == 2:
            result = self.mds_parcelas_ui.show_config_screen()
            if result:
                print("MDS Parcelas functionality coming soon...")
                input("Press Enter to continue...")
        elif site_num == 3:
            result = self.mds_saldo_ui.show_config_screen()
            if result:
                print("MDS Saldo functionality coming soon...")
                input("Press Enter to continue...")


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