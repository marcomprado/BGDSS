"""
Parallel Site Runner - Subprocess execution with separate terminal windows

Provides functionality to run all three Brazilian government sites
simultaneously using separate terminal windows via subprocess.
"""

import subprocess
import sys
import os
import platform


def run_all_sites_parallel(portal_saude_ui, mds_parcelas_ui, mds_saldo_ui):
    """
    Execute all three sites in separate terminal windows.
    
    Args:
        portal_saude_ui: Portal Saude MG UI instance (not used in subprocess approach)
        mds_parcelas_ui: MDS Parcelas UI instance (not used in subprocess approach)
        mds_saldo_ui: MDS Saldo UI instance (not used in subprocess approach)
    """
    print("========================================")
    print("    EXECUÇÃO PARALELA - 3 SITES")
    print("========================================")
    print("")
    print("Abrindo 3 janelas separadas para cada site...")
    print("")
    print("Sites que serão executados:")
    print("1. Portal Saude MG - Resoluções")
    print("2. MDS - Parcelas Pagas") 
    print("3. MDS - Saldo Detalhado por Conta")
    print("")
    
    # Get the current script path
    current_dir = os.getcwd()
    main_script = os.path.join(current_dir, "main.py")
    python_cmd = sys.executable
    
    try:
        print("🚀 Abrindo janelas dos sites...")
        
        # Open separate terminal windows based on OS
        os_name = platform.system().lower()
        
        if os_name == "darwin":  # macOS
            _open_macos_terminals(python_cmd, main_script)
        elif os_name == "windows":  # Windows
            _open_windows_terminals(python_cmd, main_script)
        else:  # Linux and others
            _open_linux_terminals(python_cmd, main_script)
        
        print("")
        print("✅ 3 janelas abertas com sucesso!")
        print("Cada site está rodando em sua própria janela.")
        print("Configure e execute cada um independentemente.")
        print("")
        
    except Exception as e:
        print(f"❌ Erro ao abrir janelas: {str(e)}")
        print("Tentando método alternativo...")
        _fallback_execution(python_cmd, main_script)
    
    input("Pressione Enter para continuar...")


def _open_macos_terminals(python_cmd, main_script):
    """Open terminals on macOS using osascript."""
    sites = [
        ("Portal Saude MG", 1),
        ("MDS Parcelas", 2), 
        ("MDS Saldo", 3)
    ]
    
    for site_name, site_num in sites:
        cmd = f'''tell application "Terminal"
            do script "{python_cmd} {main_script} --site={site_num}"
            set custom title of front window to "{site_name}"
        end tell'''
        
        subprocess.Popen(['osascript', '-e', cmd])


def _open_windows_terminals(python_cmd, main_script):
    """Open terminals on Windows using start command with error handling."""
    sites = [1, 2, 3]
    site_names = ["Portal-Saude", "MDS-Parcelas", "MDS-Saldo"]
    
    for i, site_num in enumerate(sites):
        try:
            # Use cmd /c instead of /k to avoid keeping terminal open on error
            # Escape quotes properly for Windows command line
            cmd = f'start "{site_names[i]}" cmd /k ""{python_cmd}" "{main_script}" --site={site_num}""'
            process = subprocess.Popen(cmd, shell=True, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            
            # Brief check if process started successfully
            import time
            time.sleep(0.5)
            if process.poll() is not None and process.returncode != 0:
                # Try fallback method without start command
                fallback_cmd = f'"{python_cmd}" "{main_script}" --site={site_num}'
                print(f"[AVISO] Falha ao abrir terminal para {site_names[i]}, tentando execução direta...")
                subprocess.Popen(fallback_cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0)
                
        except (OSError, subprocess.SubprocessError) as e:
            print(f"[ERRO] Não foi possível abrir terminal para {site_names[i]}: {e}")
            print(f"       Tentando execução sem nova janela...")
            try:
                # Last resort: run without new window
                fallback_cmd = f'"{python_cmd}" "{main_script}" --site={site_num}'
                subprocess.Popen(fallback_cmd, shell=True)
            except Exception as fallback_error:
                print(f"[ERRO CRÍTICO] Falha completa para {site_names[i]}: {fallback_error}")


def _open_linux_terminals(python_cmd, main_script):
    """Open terminals on Linux using various terminal emulators."""
    sites = [1, 2, 3]
    site_names = ["Portal-Saude", "MDS-Parcelas", "MDS-Saldo"]
    
    # Try different terminal emulators
    terminals = [
        'gnome-terminal',
        'konsole', 
        'xfce4-terminal',
        'lxterminal',
        'xterm'
    ]
    
    terminal_cmd = None
    for term in terminals:
        try:
            subprocess.run(['which', term], check=True, capture_output=True)
            terminal_cmd = term
            break
        except subprocess.CalledProcessError:
            continue
    
    if not terminal_cmd:
        raise Exception("Nenhum terminal encontrado no sistema Linux")
    
    for i, site_num in enumerate(sites):
        if terminal_cmd == 'gnome-terminal':
            subprocess.Popen([
                'gnome-terminal', 
                '--title', site_names[i],
                '--', python_cmd, main_script, f'--site={site_num}'
            ])
        elif terminal_cmd == 'konsole':
            subprocess.Popen([
                'konsole', 
                '--title', site_names[i],
                '-e', python_cmd, main_script, f'--site={site_num}'
            ])
        else:
            subprocess.Popen([
                terminal_cmd, 
                '-e', python_cmd, main_script, f'--site={site_num}'
            ])


def _fallback_execution(python_cmd, main_script):
    """Fallback method using simple subprocess calls."""
    print("Executando método alternativo sem janelas separadas...")
    sites = [1, 2, 3]
    processes = []
    
    for site_num in sites:
        process = subprocess.Popen([
            python_cmd, main_script, f'--site={site_num}'
        ])
        processes.append(process)
    
    # Wait for all to complete
    for process in processes:
        process.wait()
    
    print("✅ Todos os sites concluídos!")