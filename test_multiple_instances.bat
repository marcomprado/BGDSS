@echo off
setlocal enabledelayedexpansion

echo ================================================
echo  TESTE DE MULTIPLAS INSTANCIAS BGDSS
echo ================================================
echo.
echo Este script testa a execucao simultanea de 
echo multiplas instancias do BGDSS para verificar
echo se o problema de conflito de sessao foi resolvido.
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

echo [INFO] Iniciando 3 instancias simultaneas...
echo.

:: Iniciar Portal Saude MG em nova janela
echo [1/3] Iniciando Portal Saude MG...
start "BGDSS - Portal Saude MG" cmd /c "python main.py --site 1 && pause"

:: Pequeno delay para evitar conflito inicial
timeout /t 1 /nobreak >nul

:: Iniciar MDS Parcelas em nova janela
echo [2/3] Iniciando MDS Parcelas...
start "BGDSS - MDS Parcelas" cmd /c "python main.py --site 2 && pause"

:: Pequeno delay para evitar conflito inicial
timeout /t 1 /nobreak >nul

:: Iniciar MDS Saldo em nova janela
echo [3/3] Iniciando MDS Saldo...
start "BGDSS - MDS Saldo" cmd /c "python main.py --site 3 && pause"

echo.
echo ================================================
echo  Todas as instancias foram iniciadas!
echo ================================================
echo.
echo Verifique as janelas abertas para ver se
echo os scrapers estao funcionando corretamente.
echo.
echo Se houver erros de conflito de sessao Chrome,
echo eles aparecerao nas janelas individuais.
echo.
pause