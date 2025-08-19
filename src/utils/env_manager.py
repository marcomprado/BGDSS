"""
Environment file manager for .env file operations.
Handles reading, writing, and updating .env files while preserving structure and comments.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime

from src.utils.logger import logger


class EnvManager:
    """Manages .env file operations with structure preservation."""
    
    def __init__(self, env_path: Optional[Path] = None):
        """Initialize the environment manager.
        
        Args:
            env_path: Path to the .env file. Defaults to project root .env
        """
        if env_path is None:
            self.env_path = Path(__file__).parent.parent.parent / '.env'
        else:
            self.env_path = Path(env_path)
    
    def exists(self) -> bool:
        """Check if .env file exists."""
        return self.env_path.exists()
    
    def create_from_template(self) -> None:
        """Create a new .env file with default template."""
        template = """# Web Scraper AI - Environment Configuration
# Configuração do ambiente para o sistema BGDSS

# ====================================
# CONFIGURAÇÃO DE IA (Obrigatório)
# ====================================
# Provider de IA (openai, openrouter)
AI_PROVIDER=openai

# URL base do provider (opcional para OpenAI, obrigatório para OpenRouter)
AI_BASE_URL=

# Chave de API do provider
# Para OpenAI: https://platform.openai.com/api-keys
# Para OpenRouter: https://openrouter.ai/keys
OPENAI_API_KEY=

# Modelo a ser usado (obrigatório - sem valor padrão)
# Exemplos OpenAI: gpt-4, gpt-3.5-turbo
# Exemplos OpenRouter: openai/gpt-4, anthropic/claude-3-opus
OPENAI_MODEL=gpt-3.5-turbo

# Configurações específicas do provider (JSON string, opcional)
AI_PROVIDER_CONFIG=

# Máximo de tokens por requisição (padrão: 25000)
OPENAI_MAX_TOKENS=25000

# Temperatura para geração (0.0-1.0, padrão: 0.7)
OPENAI_TEMPERATURE=0.7

# ====================================
# CONFIGURAÇÃO DE WEB SCRAPING
# ====================================
# Timeout para downloads em segundos (padrão: 30)
DOWNLOAD_TIMEOUT=30

# Tempo de espera padrão entre ações (padrão: 10)
DEFAULT_WAIT_TIME=10

# Número máximo de tentativas em caso de falha (padrão: 3)
MAX_RETRIES=3

# ====================================
# CONFIGURAÇÃO DE LOGGING
# ====================================
# Nível de log: DEBUG, INFO, WARNING, ERROR (padrão: INFO)
LOG_LEVEL=INFO
"""
        self.env_path.write_text(template, encoding='utf-8')
        logger.info(f"Created new .env file at {self.env_path}")
    
    def backup(self) -> Optional[Path]:
        """Create a backup of the current .env file.
        
        Returns:
            Path to the backup file if created, None otherwise
        """
        if not self.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.env_path.parent / f'.env.backup_{timestamp}'
        
        try:
            shutil.copy2(self.env_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def read_all(self) -> Dict[str, str]:
        """Read all key-value pairs from .env file.
        
        Returns:
            Dictionary of environment variables
        """
        if not self.exists():
            return {}
        
        env_vars = {}
        try:
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value and value[0] == value[-1] and value[0] in ('"', "'"):
                            value = value[1:-1]
                        env_vars[key] = value
        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
        
        return env_vars
    
    def read_value(self, key: str) -> Optional[str]:
        """Read a specific value from .env file.
        
        Args:
            key: The environment variable key
            
        Returns:
            The value if found, None otherwise
        """
        env_vars = self.read_all()
        return env_vars.get(key)
    
    def update_values(self, updates: Dict[str, str]) -> bool:
        """Update multiple values in .env file while preserving structure.
        
        Args:
            updates: Dictionary of key-value pairs to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.exists():
            logger.error(".env file does not exist")
            return False
        
        try:
            # Read all lines
            with open(self.env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Track which keys have been updated
            updated_keys = set()
            
            # Update existing keys
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                # Skip comments and empty lines
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Check if this line contains a key to update
                if '=' in stripped:
                    key, _ = stripped.split('=', 1)
                    key = key.strip()
                    
                    if key in updates:
                        # Preserve any inline comments
                        if '#' in line and not line.strip().startswith('#'):
                            # Line has an inline comment
                            pre_comment = line.split('#')[0].rstrip()
                            comment = '#' + line.split('#', 1)[1]
                            lines[i] = f"{key}={updates[key]} {comment}"
                        else:
                            # No inline comment
                            lines[i] = f"{key}={updates[key]}\n"
                        updated_keys.add(key)
            
            # Add new keys that weren't in the file
            new_keys = set(updates.keys()) - updated_keys
            if new_keys:
                # Add a newline if file doesn't end with one
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] += '\n'
                
                # Add new keys at the end
                lines.append('\n# Added by configuration terminal\n')
                for key in new_keys:
                    lines.append(f"{key}={updates[key]}\n")
            
            # Write back to file
            with open(self.env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            logger.info(f"Updated {len(updates)} values in .env file")
            return True
            
        except Exception as e:
            logger.error(f"Error updating .env file: {e}")
            return False
    
    def update_value(self, key: str, value: str) -> bool:
        """Update a single value in .env file.
        
        Args:
            key: The environment variable key
            value: The new value
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_values({key: value})
    
    def get_ai_config(self) -> Dict[str, str]:
        """Get all AI-related configuration values.
        
        Returns:
            Dictionary with AI configuration
        """
        all_vars = self.read_all()
        ai_keys = [
            'OPENAI_API_KEY',
            'AI_PROVIDER', 
            'AI_BASE_URL',
            'OPENAI_MODEL',
            'AI_PROVIDER_CONFIG',
            'AI_PROVIDER_PREFERENCE',
            'OPENAI_MAX_TOKENS',
            'OPENAI_TEMPERATURE'
        ]
        
        return {key: all_vars.get(key, '') for key in ai_keys}
    
    def validate_ai_config(self) -> Tuple[bool, List[str]]:
        """Validate if AI configuration is complete.
        
        Returns:
            Tuple of (is_valid, list_of_missing_fields)
        """
        config = self.get_ai_config()
        missing = []
        
        # Required fields
        if not config.get('OPENAI_API_KEY'):
            missing.append('API Key')
        
        if not config.get('OPENAI_MODEL'):
            missing.append('Modelo de IA')
        
        return (len(missing) == 0, missing)