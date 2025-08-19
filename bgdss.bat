@echo off
setlocal enabledelayedexpansion

:: Verificar se Python está instalado
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH do sistema.
    echo        Instale Python ou adicione ao PATH e tente novamente.
    echo.
    pause
    exit /b 1
)

:: Verificar se está rodando como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [ADMIN] Executando com privilegios de administrador
    goto :run
) else (
    echo [INFO] Tentando solicitar privilegios de administrador...
    echo        Se falhar, o programa continuara sem privilegios elevados.
    echo.
    
    :: Tentar reexecutar com privilegios elevados
    powershell -Command "try { Start-Process '%~f0' -Verb RunAs -ErrorAction Stop } catch { exit 1 }" >nul 2>&1
    if %errorLevel% == 0 (
        exit /b
    ) else (
        echo [AVISO] Nao foi possivel obter privilegios de administrador.
        echo         Continuando execucao normal...
        echo         Algumas funcionalidades podem nao funcionar corretamente.
        echo.
        timeout /t 3 /nobreak >nul
        goto :run
    )
)

:run
:: Mudar para o diretório do script
cd /d "%~dp0"

:: Verificar se main.py existe
if not exist "main.py" (
    echo [ERRO] Arquivo main.py nao encontrado no diretorio atual.
    echo        Verifique se esta executando o script no diretorio correto.
    echo.
    pause
    exit /b 1
)

:: Executar o programa Python
echo [INFO] Iniciando BGDSS - Brazilian Government Data Scraping System
echo.
python main.py

:: Verificar se o programa executou com sucesso
if %errorLevel% neq 0 (
    echo.
    echo [ERRO] O programa terminou com codigo de erro: %errorLevel%
    echo        Verifique os logs para mais informacoes.
)

:: Pausar para manter a janela aberta
echo.
pause