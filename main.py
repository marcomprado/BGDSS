#!/usr/bin/env python3
"""
Web Scraper AI - Main Entry Point

FUNCIONALIDADE:
    Este arquivo serve como ponto de entrada principal da aplicação Web Scraper AI
    para sites do governo brasileiro. Sua responsabilidade é inicializar a interface
    terminal especializada para coleta de dados governamentais.

RESPONSABILIDADES:
    - Ponto de entrada único da aplicação
    - Inicialização da interface terminal brasileira
    - Tratamento de código de saída do sistema
    - Gerenciamento de interrupções do usuário

INTEGRAÇÃO NO SISTEMA:
    - Usado como comando principal: python main.py
    - Interface com sistema operacional via sys.exit()
    - Conecta com src.ui.terminal para funcionalidade completa
    - Interface terminal especializada para sites governamentais

SITES SUPORTADOS:
    1. Portal Saude MG - Deliberações (PDFs)
    2. MDS - Parcelas Pagas (dados CSV)
    3. MDS - Saldo Detalhado por Conta (dados CSV)

EXEMPLO DE USO:
    $ python main.py
"""

import sys

from src.ui.terminal import run_brazilian_sites_terminal


def main() -> int:
    """Main application entry point."""
    try:
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