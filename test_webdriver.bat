@echo off
setlocal enabledelayedexpansion

echo ================================================
echo  TESTE DE WEBDRIVER - BGDSS
echo ================================================
echo.
echo Este script testa se o WebDriver funciona
echo corretamente quando executado via .bat
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

echo [INFO] Testando criacao do WebDriver...
echo.

:: Criar script Python de teste
echo import sys > test_webdriver.py
echo import os >> test_webdriver.py
echo sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) >> test_webdriver.py
echo. >> test_webdriver.py
echo print("Importando configuracoes...") >> test_webdriver.py
echo from config.webdriver_config import create_configured_driver >> test_webdriver.py
echo. >> test_webdriver.py
echo print("Criando WebDriver...") >> test_webdriver.py
echo try: >> test_webdriver.py
echo     driver = create_configured_driver(profile='government_sites', headless=True) >> test_webdriver.py
echo     print("SUCESSO: WebDriver criado com sucesso!") >> test_webdriver.py
echo     driver.get("https://www.google.com") >> test_webdriver.py
echo     print(f"Titulo da pagina: {driver.title}") >> test_webdriver.py
echo     driver.quit() >> test_webdriver.py
echo     print("WebDriver encerrado corretamente.") >> test_webdriver.py
echo except Exception as e: >> test_webdriver.py
echo     print(f"ERRO: Falha ao criar WebDriver: {e}") >> test_webdriver.py
echo     import traceback >> test_webdriver.py
echo     traceback.print_exc() >> test_webdriver.py

:: Executar teste
python test_webdriver.py

:: Limpar arquivo temporário
del test_webdriver.py

echo.
echo ================================================
echo  Teste concluido!
echo ================================================
echo.
pause