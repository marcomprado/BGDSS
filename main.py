#!/usr/bin/env python3
"""
Web Scraper AI - Main Entry Point

FUNCIONALIDADE:
    Este arquivo serve como ponto de entrada principal da aplicação Web Scraper AI.
    Sua única responsabilidade é delegar a execução para a interface CLI apropriada,
    mantendo o código limpo e organizado.

RESPONSABILIDADES:
    - Ponto de entrada único da aplicação
    - Delegação para interface CLI
    - Tratamento de código de saída do sistema
    - Inicialização básica do ambiente Python

INTEGRAÇÃO NO SISTEMA:
    - Usado como comando principal: python main.py
    - Interface com sistema operacional via sys.exit()
    - Conecta com src.ui.cli_interface para funcionalidade completa
    - Suporte a argumentos de linha de comando via CLI

PADRÕES DE DESIGN:
    - Facade Pattern: Interface simples para sistema complexo
    - Single Responsibility: Apenas ponto de entrada

EXEMPLO DE USO:
    $ python main.py --mode interactive --workers 5
    $ python main.py --mode daemon --log-level DEBUG
"""

import sys

from src.ui.cli_interface import cli


def main() -> int:
    """Main application entry point."""
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())