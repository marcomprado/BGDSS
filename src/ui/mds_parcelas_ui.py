#!/usr/bin/env python3
"""
MDS Parcelas Pagas Terminal Interface

Interface específica para o MDS - Parcelas Pagas com funcionalidades de seleção
de ano e município.
"""

from typing import Dict, Optional, Any
from datetime import datetime

class MDSParcelasUI:
    """
    Interface do usuário específica para MDS Parcelas Pagas.
    """
    
    def __init__(self, terminal_instance):
        self.terminal = terminal_instance
    
    def show_config_screen(self) -> Optional[Dict[str, Any]]:
        """Show MDS Parcelas Pagas configuration screen."""
        while True:
            self.terminal.clear_screen()
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
            
            mun_choice = self.terminal.get_user_input("   Digite sua opcao (1-2): ")
            
            municipality = None
            if mun_choice == "1":
                municipality = self.terminal.get_user_input("   Digite o nome do municipio: ").strip()
                if not municipality:
                    self.terminal.show_error("Nome do municipio e obrigatorio.")
                    continue
            elif mun_choice == "2":
                municipality = "ALL_MG"
            else:
                self.terminal.show_error("Opcao invalida.")
                continue
            
            print("")
            print("1. Iniciar coleta")
            print("2. Voltar ao menu principal")
            print("")
            
            choice = self.terminal.get_user_input("Digite sua opcao (1-2): ")
            
            if choice == "1":
                config = {
                    'site': 'mds_parcelas',
                    'year': year,
                    'municipality': municipality,
                    'url': 'https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*dpotvmubsQbsdfmbtQbhbtNC&event=*fyjcjs'
                }
                return config
            elif choice == "2":
                return None
            else:
                self.terminal.show_error("Opcao invalida. Tente novamente.")
    
    def get_year_input(self, prompt: str) -> Optional[int]:
        """Get and validate year input for MDS Parcelas."""
        print(prompt)
        print("   Digite um ano específico (ex: 2024)")
        print("")
        year_str = self.terminal.get_user_input("   Digite o ano: ")
        
        try:
            year = int(year_str)
            
            # Allow any reasonable year (from 2000 to current year + 20)
            current_year = datetime.now().year
            if 2000 <= year <= current_year + 20:
                return year
            else:
                self.terminal.show_error(f"Ano deve estar entre 2000 e {current_year + 20}.")
                return None
        except ValueError:
            self.terminal.show_error("Entrada invalida. Digite um numero.")
            return None