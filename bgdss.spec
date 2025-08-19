# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for BGDSS (Brazilian Government Data Scraping System)

This spec file ensures proper packaging of all dependencies, resources,
and drivers needed for the application to work as a Windows executable.

Usage:
    pyinstaller bgdss.spec

Requirements:
    - Download chromedriver.exe and place it in the project root
    - Ensure all dependencies are installed: pip install -r requirements.txt
    - Run: pyinstaller bgdss.spec
"""

import os
import sys
from pathlib import Path

# Get the current directory (where this spec file is located)
spec_root = Path(__file__).parent

# Define paths
main_script = spec_root / 'main.py'
config_dir = spec_root / 'config'
src_dir = spec_root / 'src'

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    # Selenium and WebDriver
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome',
    'selenium.webdriver.firefox',
    'selenium.webdriver.common',
    'selenium.webdriver.support',
    'webdriver_manager',
    'webdriver_manager.chrome',
    'webdriver_manager.firefox',
    
    # System-specific modules for keyboard input
    'termios',  # Unix/Linux/macOS
    'tty',      # Unix/Linux/macOS
    'select',   # Unix/Linux/macOS
    'msvcrt',   # Windows
    
    # PDF processing
    'pymupdf4llm',
    'fitz',  # PyMuPDF internal name
    
    # AI and OpenAI
    'openai',
    'httpx',
    
    # Data processing
    'pandas',
    'openpyxl',
    'xlsxwriter',
    'numpy',
    
    # Utilities
    'psutil',
    'python_dotenv',
    'dotenv',
    'colorlog',
    'python_dateutil',
    'dateutil',
    
    # System modules
    'platform',
    'subprocess',
    'multiprocessing',
    'threading',
    'queue',
    'json',
    'csv',
    'urllib',
    'urllib3',
    'requests',
    
    # Project modules
    'src',
    'src.ui',
    'src.utils',
    'src.modules',
    'src.modules.sites',
    'src.ai',
    'config',
]

# Data files to include
datas = [
    # Configuration files
    (str(config_dir / 'sites_config.json'), 'config'),
    (str(config_dir), 'config'),  # Include entire config directory
    
    # ChromeDriver (if present in root)
    # Note: Download chromedriver.exe and place it in project root
]

# Check for ChromeDriver and add it if present
chromedriver_paths = [
    spec_root / 'chromedriver.exe',  # Windows
    spec_root / 'chromedriver',      # Unix/Linux/macOS
    spec_root / 'drivers' / 'chromedriver.exe',
    spec_root / 'drivers' / 'chromedriver',
]

for driver_path in chromedriver_paths:
    if driver_path.exists():
        datas.append((str(driver_path), '.'))
        print(f"Including ChromeDriver: {driver_path}")
        break
else:
    print("WARNING: ChromeDriver not found. Download it and place in project root or drivers/ folder")

# GeckoDriver (optional, for Firefox support)
geckodriver_paths = [
    spec_root / 'geckodriver.exe',
    spec_root / 'geckodriver',
    spec_root / 'drivers' / 'geckodriver.exe',
    spec_root / 'drivers' / 'geckodriver',
]

for driver_path in geckodriver_paths:
    if driver_path.exists():
        datas.append((str(driver_path), '.'))
        print(f"Including GeckoDriver: {driver_path}")
        break

# Binaries - let PyInstaller handle these automatically
binaries = []

# Analysis phase
a = Analysis(
    [str(main_script)],
    pathex=[str(spec_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'sympy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='bgdss',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable (requires UPX)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console window for terminal interface
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-specific options
    version=None,
    uac_admin=False,  # Don't require admin privileges
    uac_uiaccess=False,
    # Icon (optional - add if you have an icon file)
    icon=None,  # Path to .ico file if available
)

# Optional: Create a COLLECT for debugging (one-folder distribution)
# Uncomment the lines below if you prefer a folder distribution instead of single exe
"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='bgdss'
)
"""