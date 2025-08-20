# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for BGDSS - Brazilian Government Data Scraping System

This spec file configures the build process for creating an executable version
of the BGDSS application that runs on Windows, macOS, and Linux.
"""

import sys
import os
from pathlib import Path

# Get the absolute path to the project directory
project_dir = os.path.abspath('.')

# Define paths
main_script = os.path.join(project_dir, 'main.py')
config_dir = os.path.join(project_dir, 'config')

# Determine platform-specific settings
if sys.platform == 'win32':
    chromedriver_name = 'chromedriver.exe'
    icon_file = None  # Add path to .ico file if you have one
elif sys.platform == 'darwin':
    chromedriver_name = 'chromedriver'
    icon_file = None  # Add path to .icns file if you have one
else:  # Linux
    chromedriver_name = 'chromedriver'
    icon_file = None

# Check if chromedriver exists in drivers directory
chromedriver_path = os.path.join(project_dir, 'drivers', chromedriver_name)
if not os.path.exists(chromedriver_path):
    # Try in project root
    chromedriver_path = os.path.join(project_dir, chromedriver_name)
    if not os.path.exists(chromedriver_path):
        print(f"WARNING: ChromeDriver not found at {chromedriver_path}")
        print("The executable will need ChromeDriver installed on the system or downloaded at runtime")
        chromedriver_path = None

a = Analysis(
    [main_script],
    pathex=[project_dir],
    binaries=[
        # Include ChromeDriver if found
        (chromedriver_path, 'drivers') if chromedriver_path else None,
    ] if chromedriver_path else [],
    datas=[
        # Include configuration files
        (os.path.join(config_dir, 'sites_config.json'), 'config'),
        # Note: .env file should NOT be bundled - it should be created/edited by user
    ],
    hiddenimports=[
        # Selenium and webdriver imports
        'selenium',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.firefox.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        
        # OpenAI and AI-related imports
        'openai',
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
        
        # Data processing
        'pandas',
        'openpyxl',
        'xlsxwriter',
        
        # PDF processing
        'PyPDF2',
        'pdfplumber',
        
        # Web requests
        'requests',
        'urllib3',
        
        # System utilities
        'psutil',
        'dotenv',
        
        # Terminal UI
        'colorama',
        'termcolor',
        
        # Additional imports that might be dynamically loaded
        'encodings.utf_8',
        'encodings.latin_1',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'tkinter',
        'test',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console=True for terminal-based application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# For macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='BGDSS.app',
        icon=icon_file,
        bundle_identifier='com.bgdss.scraper',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSRequiresAquaSystemAppearance': 'False',
        },
    )

print("\n" + "="*60)
print("BGDSS PyInstaller Build Configuration")
print("="*60)
print(f"Platform: {sys.platform}")
print(f"Main script: {main_script}")
print(f"ChromeDriver: {'Included' if chromedriver_path else 'Not included (will use system or download at runtime)'}")
print(f"Output name: bgdss{'.exe' if sys.platform == 'win32' else ''}")
print("="*60)
print("\nIMPORTANT: After building, remember to:")
print("1. Copy your .env file to the same directory as the executable")
print("2. The app will create ~/Documents/BGDSS (Windows) or ~/BGDSS (Mac/Linux) for data storage")
print("3. Ensure ChromeDriver is available (bundled, system-installed, or will be downloaded)")
print("="*60 + "\n")