@echo off
setlocal

:: Verificar se está rodando como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [ADMIN] Executando com privilegios de administrador
    goto :run
) else (
    echo [INFO] Solicitando privilegios de administrador...
    echo.
    
    :: Reexecutar com privilegios elevados usando PowerShell
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:run
:: Mudar para o diretório do script
cd /d "%~dp0"

:: Executar o programa Python
python main.py

:: Pausar para manter a janela aberta
pause