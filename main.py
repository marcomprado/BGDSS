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
from src.ui.config_terminal import run_configuration
from src.utils.env_manager import EnvManager


def main() -> int:
    """Main application entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Brazilian Government Sites Web Scraper')
    parser.add_argument('--site', type=int, choices=[1, 2, 3], 
                       help='Run specific site: 1=Portal Saude MG, 2=MDS Parcelas, 3=MDS Saldo')
    parser.add_argument('--config', action='store_true',
                       help='Open configuration terminal to set up API keys and providers')
    args = parser.parse_args()
    
    try:
        # Check if --config flag was used
        if args.config:
            # Force configuration screen
            if not run_configuration(force=True):
                print("\nConfiguração cancelada.")
                return 0
        else:
            # Check if configuration is needed
            env_manager = EnvManager()
            
            # Create .env if it doesn't exist
            if not env_manager.exists():
                print("\nPrimeira execução detectada. Iniciando configuração...")
                print("-" * 50)
                if not run_configuration(force=True):
                    print("\nConfiguração é necessária para executar o sistema.")
                    return 1
            else:
                # Check if API key is configured
                config = env_manager.get_ai_config()
                if not config.get('OPENAI_API_KEY') or not config.get('OPENAI_MODEL'):
                    print("\nConfiguração de IA não encontrada.")
                    print("O sistema precisa ser configurado antes do primeiro uso.")
                    print("-" * 50)
                    if not run_configuration(force=False):
                        print("\nAviso: Sem configuração de IA, algumas funcionalidades estarão desabilitadas.")
                        # Continue anyway - the app can work without AI for basic scraping
        
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