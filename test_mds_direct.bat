@echo off
setlocal enabledelayedexpansion

echo ================================================
echo  TESTE DIRETO MDS - BGDSS
echo ================================================
echo.
echo Este script testa diretamente os scrapers MDS
echo para identificar problemas de execucao via .bat
echo.

:: Mudar para o diretório do script
cd /d "%~dp0"

:: Verificar Python
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERRO] Python nao encontrado.
    pause
    exit /b 1
)

echo [INFO] Escolha o teste a executar:
echo.
echo 1. Testar MDS Parcelas
echo 2. Testar MDS Saldo
echo 3. Testar ambos
echo.
set /p choice="Digite sua escolha (1-3): "

if "%choice%"=="1" goto test_parcelas
if "%choice%"=="2" goto test_saldo
if "%choice%"=="3" goto test_both
echo Escolha invalida!
pause
exit /b 1

:test_parcelas
echo.
echo [INFO] Testando MDS Parcelas...
python main.py --site 2
goto end

:test_saldo
echo.
echo [INFO] Testando MDS Saldo...
python main.py --site 3
goto end

:test_both
echo.
echo [INFO] Testando MDS Parcelas...
start "MDS Parcelas Test" cmd /k "python main.py --site 2 && pause"
timeout /t 2 /nobreak >nul
echo.
echo [INFO] Testando MDS Saldo...
start "MDS Saldo Test" cmd /k "python main.py --site 3 && pause"

:end
echo.
echo ================================================
echo  Teste iniciado!
echo ================================================
echo.
echo Verifique os logs em 'logs/' para detalhes.
echo.
pause