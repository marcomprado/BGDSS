@echo off
setlocal enabledelayedexpansion

:: Script para executar BGDSS sem privilegios de administrador
:: Use este script se o bgdss.bat falhar com WinError 5

echo ===============================================
echo  BGDSS - Execucao sem Privilegios Elevados
echo ===============================================
echo.

:: Verificar se Python está instalado
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH do sistema.
    echo        Instale Python ou adicione ao PATH e tente novamente.
    echo        Para adicionar Python ao PATH:
    echo        1. Abra 'Configuracoes do Sistema' (sysdm.cpl)
    echo        2. Aba 'Avancado' ^> 'Variaveis de Ambiente'
    echo        3. Adicione o caminho do Python na variavel PATH
    echo.
    pause
    exit /b 1
)

:: Mudar para o diretório do script
cd /d "%~dp0"

:: Verificar se main.py existe
if not exist "main.py" (
    echo [ERRO] Arquivo main.py nao encontrado no diretorio atual.
    echo        Caminho atual: %CD%
    echo        Verifique se esta executando o script no diretorio correto.
    echo.
    pause
    exit /b 1
)

:: Verificar dependências básicas
echo [INFO] Verificando dependencias do Python...
python -c "import sys; print(f'Python {sys.version}')" 2>nul
if %errorLevel% neq 0 (
    echo [AVISO] Erro ao verificar versao do Python.
    echo         Continuando mesmo assim...
)

:: Verificar se requirements.txt existe e sugerir instalação
if exist "requirements.txt" (
    echo [INFO] Arquivo requirements.txt encontrado.
    echo        Se for a primeira execucao, execute:
    echo        pip install -r requirements.txt
    echo.
)

:: Executar o programa Python
echo [INFO] Iniciando BGDSS - Brazilian Government Data Scraping System
echo [INFO] Modo: Execucao sem privilegios elevados
echo.
python main.py

:: Verificar se o programa executou com sucesso
if %errorLevel% neq 0 (
    echo.
    echo [ERRO] O programa terminou com codigo de erro: %errorLevel%
    echo        Possiveis causas:
    echo        - Dependencias nao instaladas (execute: pip install -r requirements.txt)
    echo        - Erro de configuracao (verifique arquivo .env)
    echo        - Problema de conexao com internet
    echo        - Verifique os logs na pasta 'logs/' para mais detalhes
) else (
    echo.
    echo [SUCESSO] Programa executado com sucesso!
)

:: Pausar para manter a janela aberta
echo.
echo Pressione qualquer tecla para fechar...
pause >nul