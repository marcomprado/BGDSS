#!/usr/bin/env python3
"""
MDS Saldo Detalhado Terminal Interface

Interface específica para o MDS - Saldo Detalhado por Conta com funcionalidades 
de seleção de ano, mês e município.
"""

from typing import Dict, Optional, Any
from datetime import datetime

class MDSSaldoUI:
    """
    Interface do usuário específica para MDS Saldo Detalhado por Conta.
    """
    
    def __init__(self, terminal_instance):
        self.terminal = terminal_instance
    
    def show_config_screen(self) -> Optional[Dict[str, Any]]:
        """Show MDS Saldo Detalhado configuration screen."""
        while True:
            self.terminal.clear_screen()
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
            print("4. Iniciar coleta")
            print("5. Voltar ao menu principal")
            print("")
            
            choice = self.terminal.get_user_input("Digite sua opcao (4-5): ")
            
            if choice == "4":
                config = {
                    'site': 'mds_saldo',
                    'year': year,
                    'month': month,
                    'municipality': municipality,
                    'url': 'https://aplicacoes.mds.gov.br/suaswebcons/restrito/execute.jsf?b=*tbmepQbs'
                }
                return config
            elif choice == "5":
                return None
            else:
                self.terminal.show_error("Opcao invalida. Tente novamente.")
    
    def get_year_input(self, prompt: str) -> Optional[int]:
        """Get and validate year input for MDS Saldo."""
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

    def get_month_input(self, prompt: str, required: bool = False) -> Optional[int]:
        """Get and validate month input for MDS Saldo."""
        print(prompt)
        print("   1) Janeiro    2) Fevereiro   3) Marco")
        print("   4) Abril      5) Maio        6) Junho")
        print("   7) Julho      8) Agosto      9) Setembro")
        print("   10) Outubro   11) Novembro   12) Dezembro")
        print("")
        
        month_str = self.terminal.get_user_input("   Digite sua opcao (1-12): ")
        
        try:
            month = int(month_str)
            if 1 <= month <= 12:
                return month
            else:
                self.terminal.show_error("Opcao deve estar entre 1 e 12.")
                return None
        except ValueError:
            self.terminal.show_error("Opcao invalida. Digite um numero.")
            return None