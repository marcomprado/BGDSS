#!/usr/bin/env python3
"""
Build script for BGDSS executable

This script automates the process of building the BGDSS executable
with all necessary components and dependencies.

Usage:
    python build_executable.py [--clean] [--debug]

Options:
    --clean: Clean build directories before building
    --debug: Create debug version with verbose output
"""

import argparse
import os
import sys
import shutil
import subprocess
from pathlib import Path
import requests
from zipfile import ZipFile


def download_chromedriver():
    """Download ChromeDriver if not present."""
    script_dir = Path(__file__).parent
    
    # Check if ChromeDriver already exists
    existing_drivers = [
        script_dir / 'chromedriver.exe',
        script_dir / 'chromedriver',
        script_dir / 'drivers' / 'chromedriver.exe',
        script_dir / 'drivers' / 'chromedriver',
    ]
    
    for driver_path in existing_drivers:
        if driver_path.exists():
            print(f"ChromeDriver already exists: {driver_path}")
            return str(driver_path)
    
    print("ChromeDriver not found. Downloading...")
    
    # Create drivers directory if it doesn't exist
    drivers_dir = script_dir / 'drivers'
    drivers_dir.mkdir(exist_ok=True)
    
    try:
        # Get the latest ChromeDriver version
        from selenium import __version__ as selenium_version
        print(f"Selenium version: {selenium_version}")
        
        # Use webdriver-manager to download
        from webdriver_manager.chrome import ChromeDriverManager
        
        manager = ChromeDriverManager()
        driver_path = manager.install()
        
        # Copy to our drivers directory
        if sys.platform == 'win32':
            target_path = drivers_dir / 'chromedriver.exe'
        else:
            target_path = drivers_dir / 'chromedriver'
        
        shutil.copy2(driver_path, target_path)
        
        # Make executable on Unix systems
        if sys.platform != 'win32':
            os.chmod(target_path, 0o755)
        
        print(f"ChromeDriver downloaded to: {target_path}")
        return str(target_path)
        
    except Exception as e:
        print(f"Failed to download ChromeDriver automatically: {e}")
        print("Please download ChromeDriver manually from:")
        print("https://chromedriver.chromium.org/downloads")
        print("And place it in the project root or drivers/ directory")
        return None


def clean_build_dirs():
    """Clean build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"Cleaning {dir_path}")
            shutil.rmtree(dir_path)


def check_requirements():
    """Check if all requirements are installed."""
    print("Checking requirements...")
    
    try:
        import selenium
        import webdriver_manager
        import requests
        import pandas
        import openai
        import pymupdf4llm
        print("✓ All main requirements found")
        return True
    except ImportError as e:
        print(f"✗ Missing requirement: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False


def build_executable(debug=False, clean=False):
    """Build the executable using PyInstaller."""
    script_dir = Path(__file__).parent
    spec_file = script_dir / 'bgdss.spec'
    
    if not spec_file.exists():
        print("Error: bgdss.spec file not found")
        return False
    
    # Clean if requested
    if clean:
        clean_build_dirs()
    
    # Check requirements
    if not check_requirements():
        return False
    
    # Download ChromeDriver if needed
    chromedriver_path = download_chromedriver()
    if not chromedriver_path:
        print("Warning: Continuing without ChromeDriver")
    
    # Build command
    cmd = ['pyinstaller']
    
    if debug:
        cmd.extend(['--debug', 'all'])
        cmd.append('--console')
    
    cmd.append(str(spec_file))
    
    print(f"Building executable with command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Build successful!")
            
            # Find the executable
            dist_dir = script_dir / 'dist'
            if dist_dir.exists():
                exe_files = list(dist_dir.glob('*.exe')) or list(dist_dir.glob('bgdss*'))
                if exe_files:
                    exe_path = exe_files[0]
                    print(f"✓ Executable created: {exe_path}")
                    print(f"✓ Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
                    
                    # Test the executable
                    print("Testing executable...")
                    test_result = subprocess.run([str(exe_path), '--help'], 
                                               capture_output=True, text=True, timeout=10)
                    if test_result.returncode == 0:
                        print("✓ Executable test passed")
                    else:
                        print("⚠ Executable test failed, but build completed")
                else:
                    print("⚠ Build completed but executable not found in dist/")
            
            return True
        else:
            print("✗ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Build timed out")
        return False
    except FileNotFoundError:
        print("✗ PyInstaller not found. Install with: pip install pyinstaller")
        return False
    except Exception as e:
        print(f"✗ Build error: {e}")
        return False


def create_distribution_package():
    """Create a distribution package with necessary files."""
    script_dir = Path(__file__).parent
    dist_dir = script_dir / 'dist'
    
    if not dist_dir.exists():
        print("No dist directory found")
        return
    
    # Find the executable
    exe_files = list(dist_dir.glob('*.exe')) or list(dist_dir.glob('bgdss*'))
    if not exe_files:
        print("No executable found")
        return
    
    exe_path = exe_files[0]
    
    # Create package directory
    package_dir = dist_dir / 'bgdss_package'
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Copy executable
    shutil.copy2(exe_path, package_dir / exe_path.name)
    
    # Copy essential files
    files_to_copy = [
        'README.md',
        'requirements.txt',
        '.env.example' if (script_dir / '.env.example').exists() else None,
    ]
    
    for file_name in files_to_copy:
        if file_name and (script_dir / file_name).exists():
            shutil.copy2(script_dir / file_name, package_dir / file_name)
    
    # Create usage instructions
    instructions = """# BGDSS - Brazilian Government Data Scraping System

## Setup Instructions

1. Place this executable in a folder where you want to store the data
2. Create a .env file in the same directory with your API keys:
   ```
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-4o-mini
   ```
3. Run the executable: ./bgdss.exe (Windows) or ./bgdss (Linux/macOS)
4. The first run will create necessary directories (downloads, logs)
5. Data will be saved in the 'downloads' folder

## Notes

- The application requires internet connection
- Downloads and logs are stored in the same directory as the executable
- For AI features, you need a valid OpenAI API key
- Basic scraping works without API keys

## Support

For issues and documentation: https://github.com/your-repo/bgdss
"""
    
    with open(package_dir / 'SETUP.txt', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"✓ Distribution package created: {package_dir}")
    print(f"✓ Package size: {sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MB")


def main():
    parser = argparse.ArgumentParser(description='Build BGDSS executable')
    parser.add_argument('--clean', action='store_true', help='Clean build directories')
    parser.add_argument('--debug', action='store_true', help='Create debug build')
    parser.add_argument('--package', action='store_true', help='Create distribution package')
    
    args = parser.parse_args()
    
    print("BGDSS Executable Builder")
    print("=" * 40)
    
    success = build_executable(debug=args.debug, clean=args.clean)
    
    if success:
        print("\n" + "=" * 40)
        print("Build completed successfully!")
        
        if args.package:
            create_distribution_package()
        
        print("\nNext steps:")
        print("1. Test the executable in dist/ directory")
        print("2. Create .env file with your API keys")
        print("3. Distribute the executable to target machines")
    else:
        print("\nBuild failed. Please check the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()