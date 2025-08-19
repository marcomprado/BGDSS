"""
Configuration Terminal Interface

Interactive terminal for configuring AI provider settings and API keys.
Provides a user-friendly interface for setting up the application before first use.
"""

import os
import sys
import time
import getpass
import re
from typing import Dict, Optional, Tuple, List
from pathlib import Path

from src.utils.env_manager import EnvManager
from src.utils.logger import logger
from src.utils.keyboard_input import get_key_input, is_esc_pressed, ESC_PRESSED


class ConfigurationTerminal:
    """Interactive terminal for AI configuration setup."""
    
    # Available models (using OpenRouter as default provider)
    AVAILABLE_MODELS = [
        'openai/gpt-4',
        'openai/gpt-3.5-turbo', 
        'anthropic/claude-3-opus',
        'anthropic/claude-3-sonnet',
        'google/gemini-pro',
        'meta-llama/llama-2-70b-chat',
        'openai/gpt-oss-20b'
    ]
    
    def __init__(self):
        """Initialize the configuration terminal."""
        self.env_manager = EnvManager()
        self.current_config = {}
        self.running = True
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Display the configuration header."""
        self.clear_screen()
        print("=" * 60)
        print("         CONFIGURAÇÃO DO SISTEMA BGDSS")
        print("=" * 60)
        print("")
    
    def show_current_config(self):
        """Display current configuration status."""
        config = self.env_manager.get_ai_config()
        api_key = config.get('OPENAI_API_KEY', '')
        model = config.get('OPENAI_MODEL', '')
        
        print("CONFIGURAÇÃO ATUAL:")
        print("-" * 40)
        
        # API Key (masked)
        if api_key:
            masked_key = f"{'*' * (len(api_key) - 8)}...{api_key[-4:]}" if len(api_key) > 8 else '*' * len(api_key)
            print(f"  API Key: {masked_key} ✓")
        else:
            print(f"  API Key: [NÃO CONFIGURADA] ✗")
        
        # Model
        if model:
            print(f"  Modelo de IA: {model} ✓")
        else:
            print(f"  Modelo de IA: [NÃO CONFIGURADO] ✗")
        
        print("-" * 40)
        print("")
    
    def validate_current_config(self) -> Tuple[bool, List[str]]:
        """Check if current configuration is valid.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        return self.env_manager.validate_ai_config()
    
    def show_main_menu(self):
        """Display the main configuration menu."""
        self.show_header()
        self.show_current_config()
        
        is_valid, missing = self.validate_current_config()
        
        if not is_valid:
            print("⚠️  ATENÇÃO: Configuração incompleta!")
            print("   Campos obrigatórios faltando:")
            for field in missing:
                print(f"   - {field}")
            print("")
        else:
            print("✅ Configuração completa e válida!")
            print("")
        
        print("OPÇÕES:")
        print("1. Configurar API Key")
        print("2. Selecionar Modelo de IA")
        print("3. Testar Configuração")
        print("")
        if is_valid:
            print("0. Continuar para o sistema")
            print("ESC. Voltar ao menu principal")
        else:
            print("0. Sair (configuração necessária)")
        print("")
    
    def get_user_input(self, prompt: str) -> str:
        """Get user input with ESC detection support."""
        return get_key_input(prompt)
    
    def configure_api_key(self):
        """Configure the API key."""
        self.show_header()
        print("CONFIGURAR API KEY")
        print("-" * 40)
        
        config = self.env_manager.get_ai_config()
        
        print("Para usar as funcionalidades de IA, você precisa de uma API Key.")
        print("")
        print("Obtenha sua chave em: https://openrouter.ai/keys")
        print("(OpenRouter permite usar vários modelos de IA com uma única chave)")
        print("")
        
        current_key = config.get('OPENAI_API_KEY', '')
        if current_key:
            # Check if current key looks corrupted
            if len(current_key) > 100 or not all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in current_key):
                print(f"⚠️  API Key atual parece estar corrompida")
                print(f"   Tamanho: {len(current_key)} caracteres")
            else:
                masked_key = f"{'*' * (len(current_key) - 8)}...{current_key[-4:]}" if len(current_key) > 8 else '*' * len(current_key)
                print(f"API Key atual: {masked_key}")
            print("")
        
        print("Digite a nova API Key:")
        print("Nota: A chave será ocultada durante a digitação")
        print("Pressione Ctrl+C ou digite 'esc' para cancelar")
        print("")
        
        # Flush output and clear input buffer before getpass
        sys.stdout.flush()
        time.sleep(0.1)  # Small delay to ensure terminal is ready
        
        # Clear any pending input
        if sys.platform != 'win32':
            try:
                import termios
                termios.tcflush(sys.stdin, termios.TCIFLUSH)
            except:
                pass
        
        # Use getpass for secure input
        try:
            new_key = getpass.getpass("API Key: ").strip()
        except KeyboardInterrupt:
            print("\nCancelado.")
            time.sleep(1)
            return
        
        if not new_key or new_key.lower() in ['esc', 'escape']:
            print("\nOperação cancelada.")
            time.sleep(1)
            return
        
        # Enhanced validation - remove any non-API-key characters
        # API keys typically contain alphanumeric, hyphens, underscores
        # OpenRouter keys are like: sk-or-v1-xxxxx...
        clean_key = re.sub(r'[^a-zA-Z0-9\-_]', '', new_key)
        
        # Check if key was corrupted during input
        if clean_key != new_key:
            print("\n⚠️  Detectados caracteres inválidos na API key.")
            print(f"   Original: {new_key[:20]}...")
            print(f"   Limpa: {clean_key[:20]}...")
            confirm = input("\nUsar a versão limpa? (s/N): ").strip().lower()
            if confirm not in ['s', 'sim', 'yes', 'y']:
                print("Operação cancelada. Tente novamente.")
                input("\nPressione Enter para continuar...")
                return
            new_key = clean_key
        
        # Basic validation
        if len(new_key) < 20:
            print("\n❌ API Key muito curta. Verifique se copiou corretamente.")
            input("\nPressione Enter para continuar...")
            return
        
        # Save the API key and set default provider/base URL for OpenRouter
        updates = {
            'OPENAI_API_KEY': new_key,
            'AI_PROVIDER': 'openrouter',
            'AI_BASE_URL': 'https://openrouter.ai/api/v1'
        }
        
        if self.env_manager.update_values(updates):
            print("\n✅ API Key configurada com sucesso!")
        else:
            print("\n❌ Erro ao salvar API Key.")
        
        input("\nPressione Enter para continuar...")
    
    
    def configure_model(self):
        """Configure the AI model."""
        self.show_header()
        print("SELECIONAR MODELO DE IA")
        print("-" * 40)
        
        config = self.env_manager.get_ai_config()
        current_model = config.get('OPENAI_MODEL', '')
        
        if current_model:
            print(f"Modelo atual: {current_model}")
            print("")
        
        print("Modelos disponíveis:")
        for i, model in enumerate(self.AVAILABLE_MODELS, 1):
            print(f"{i}. {model}")
        print("")
        print("0. Digitar modelo personalizado")
        print("ESC. Cancelar")
        print("")
        
        choice = self.get_user_input("Selecione o modelo (0-7):")
        
        # Handle ESC key press
        if is_esc_pressed(choice):
            print("\nOperação cancelada.")
            time.sleep(1)
            return
        
        # Handle text-based ESC
        if choice.lower() in ['esc', 'escape']:
            print("\nOperação cancelada.")
            time.sleep(1)
            return
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                print("\nDigite o nome do modelo:")
                print("(Ex: openai/gpt-4-turbo, anthropic/claude-3-opus)")
                model_input = self.get_user_input("Modelo:")
                
                # Handle ESC in model input
                if is_esc_pressed(model_input):
                    print("\nOperação cancelada.")
                    time.sleep(1)
                    return
                
                model = model_input.strip()
            elif 1 <= choice_num <= len(self.AVAILABLE_MODELS):
                model = self.AVAILABLE_MODELS[choice_num - 1]
            else:
                print("\n❌ Opção inválida.")
                time.sleep(1)
                return
        except ValueError:
            print("\n❌ Opção inválida.")
            time.sleep(1)
            return
        
        if not model:
            print("\nOperação cancelada.")
            time.sleep(1)
            return
        
        if self.env_manager.update_value('OPENAI_MODEL', model):
            print(f"\n✅ Modelo configurado: {model}")
        else:
            print("\n❌ Erro ao configurar modelo.")
        
        input("\nPressione Enter para continuar...")
    
    
    def test_configuration(self):
        """Test the current AI configuration."""
        self.show_header()
        print("TESTAR CONFIGURAÇÃO")
        print("-" * 40)
        
        is_valid, missing = self.validate_current_config()
        
        if not is_valid:
            print("❌ Configuração incompleta!")
            print("\nCampos obrigatórios faltando:")
            for field in missing:
                print(f"  - {field}")
            print("\nConfigure os campos faltantes antes de testar.")
            input("\nPressione Enter para continuar...")
            return
        
        print("Testando conexão com o provedor de IA...")
        print("")
        
        # Import here to avoid circular dependency
        try:
            from src.ai.openai_client import OpenAIClient
            
            # Reload settings to get latest config
            from config.settings import settings
            settings.reload()
            
            # Try to initialize the client
            client = OpenAIClient()
            
            if not client.enabled:
                print("❌ Cliente de IA não pôde ser inicializado.")
                print("   Verifique se a API key está correta.")
            else:
                print("✅ Cliente de IA inicializado com sucesso!")
                print("")
                print("Enviando requisição de teste...")
                
                # Try a simple test request
                try:
                    response = client.process_text(
                        "Responda apenas com 'OK' se você está funcionando.",
                        max_tokens=10
                    )
                    
                    if response:
                        print("✅ Teste bem-sucedido! Provedor de IA está funcionando.")
                        print(f"   Resposta: {response.strip()}")
                    else:
                        print("❌ Teste falhou. Sem resposta do provedor.")
                except Exception as e:
                    print(f"❌ Erro durante o teste: {str(e)}")
                    print("   Verifique sua API key e configurações.")
        
        except ImportError as e:
            print(f"❌ Erro ao importar módulos: {e}")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def run(self, force_config: bool = False) -> bool:
        """Run the configuration terminal.
        
        Args:
            force_config: If True, always show config screen even if valid
            
        Returns:
            True if configuration is valid and user wants to continue
        """
        # Create .env if it doesn't exist
        if not self.env_manager.exists():
            print("Criando arquivo de configuração...")
            self.env_manager.create_from_template()
            time.sleep(1)
        
        # Check if configuration is already valid
        is_valid, _ = self.validate_current_config()
        
        # If valid and not forced, ask if user wants to reconfigure
        if is_valid and not force_config:
            self.show_header()
            self.show_current_config()
            print("A configuração atual está válida.")
            print("")
            print("Deseja alterar as configurações? (s/N): ", end='')
            
            choice = input().strip().lower()
            if choice not in ['s', 'sim', 'yes', 'y']:
                return True
        
        # Main configuration loop
        while self.running:
            self.show_main_menu()
            
            is_valid, _ = self.validate_current_config()
            choice = self.get_user_input("Digite sua opção:")
            
            # Handle ESC key press
            if is_esc_pressed(choice):
                if is_valid:
                    # Return to main menu
                    return True
                else:
                    print("\n⚠️  A configuração não está completa.")
                    print("   Configure ao menos a API Key antes de continuar.")
                    input("\nPressione Enter para continuar...")
                    continue
            
            # Convert to lowercase for text-based options
            choice = choice.lower()
            
            if choice == '0':
                if is_valid:
                    # Configuration is valid, continue to main app
                    return True
                else:
                    # Configuration invalid, confirm exit
                    print("\n⚠️  A configuração não está completa.")
                    print("   O sistema não funcionará corretamente sem uma configuração válida.")
                    confirm = self.get_user_input("\nDeseja sair mesmo assim? (s/N):")
                    if is_esc_pressed(confirm):
                        continue
                    if confirm.lower() in ['s', 'sim', 'yes', 'y']:
                        return False
            elif choice in ['esc', 'escape', 'voltar']:
                # Handle text-based ESC command
                if is_valid:
                    # Return to main menu
                    return True
                else:
                    print("\n⚠️  A configuração não está completa.")
                    print("   Configure ao menos a API Key antes de continuar.")
                    input("\nPressione Enter para continuar...")
            elif choice == '1':
                self.configure_api_key()
            elif choice == '2':
                self.configure_model()
            elif choice == '3':
                self.test_configuration()
            else:
                print("\n❌ Opção inválida.")
                time.sleep(1)
        
        return False


def run_configuration(force: bool = False) -> bool:
    """Run the configuration terminal.
    
    Args:
        force: If True, always show configuration screen
        
    Returns:
        True if configuration is valid and user wants to continue
    """
    terminal = ConfigurationTerminal()
    return terminal.run(force_config=force)