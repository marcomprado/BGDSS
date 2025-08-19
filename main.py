#!/usr/bin/env python3
"""
Web Scraper AI - Main Entry Point

FUNCIONALIDADE:
    Este arquivo serve como ponto de entrada principal da aplicação Web Scraper AI
    para sites do governo brasileiro. Sua responsabilidade é inicializar a interface
    terminal especializada para coleta de dados governamentais.

RESPONSABILIDADES:
    - Ponto de entrada único da aplicação
    - Inicialização da interface terminal
    - Tratamento de código de saída do sistema
    - Gerenciamento de interrupções do usuário

"""

import sys
import argparse

from src.ui.terminal import run_brazilian_sites_terminal


def main() -> int:
    """Main application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Brazilian Government Sites Web Scraper')
    parser.add_argument('--site', type=int, choices=[1, 2, 3], 
                       help='Run specific site: 1=Portal Saude MG, 2=MDS Parcelas, 3=MDS Saldo')
    args = parser.parse_args()
    
    try:
        # Run the main application
        if args.site:
            # Run specific site directly
            result = run_brazilian_sites_terminal(direct_site=args.site)
        else:
            # Run normal interactive terminal
            result = run_brazilian_sites_terminal()
        
        if result.get('status') == 'exit':
            return 0
        elif result.get('status') == 'interrupted':
            print("\nProcesso interrompido pelo usuário.")
            return 130  # Standard exit code for Ctrl+C
        elif result.get('status') == 'error':
            print(f"\nErro: {result.get('error', 'Erro desconhecido')}")
            return 1
        else:
            return 0
            
    except KeyboardInterrupt:
        print("\nProcesso interrompido pelo usuário.")
        return 130
    except Exception as e:
        print(f"\nErro fatal: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())