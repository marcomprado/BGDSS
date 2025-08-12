"""
Municipality name corrector using AI with web search capabilities.
Validates and corrects municipality names for Brazilian states.
"""

from typing import Optional
from src.ai.openai_client import OpenAIClient
from src.utils.logger import logger
from functools import lru_cache


class MunicipalityCorrector:
    """Corrects municipality names using AI with web search."""
    
    def __init__(self):
        self.ai_client = OpenAIClient()
        self._cache = {}  # Cache corrections to avoid repeated API calls
        logger.info("MunicipalityCorrector initialized")
        
    @lru_cache(maxsize=128)
    def correct_municipality_name(self, input_name: str, state_uf: str) -> str:
        """
        Correct a potentially misspelled municipality name.
        
        Args:
            input_name: The user's input for municipality name
            state_uf: The state code (e.g., 'MG', 'SP')
            
        Returns:
            Corrected municipality name or "erro4040" if not found
        """
        logger.info(f"Attempting to correct municipality name: '{input_name}' for state {state_uf}")
        
        # Check cache first
        cache_key = f"{state_uf}:{input_name.upper()}"
        if cache_key in self._cache:
            logger.info(f"Using cached result for {cache_key}")
            return self._cache[cache_key]
        
        # Skip AI call if client is not enabled
        if not self.ai_client.enabled:
            logger.warning(f"AI client not enabled, returning input as-is: {input_name}")
            return input_name
        
        try:
            # Create messages for chat completion with simplified prompt
            messages = [
                {
                    "role": "user", 
                    "content": f"""Corrigir nome de município brasileiro:

Estado: {state_uf}
Nome: "{input_name}"

IMPORTANTE: Responda APENAS com o nome correto do município OU "erro4040". NÃO use markdown, links ou formatação.

Regras:
1. Se o nome existir no estado mas tiver erro de digitação, retorne apenas o nome correto
2. Se não existir no estado, retorne apenas: erro4040

Exemplos de resposta:
- Belo Horizonte
- Brumadinho  
- erro4040

Resposta:"""
                }
            ]
            
            logger.info(f"Calling AI API for municipality correction...")
            
            # Call AI chat completion
            response = self.ai_client.chat_completion(
                messages=messages,
                temperature=0.1  # Low temperature for consistency
            )
            
            if not response:
                logger.error("Empty response from AI")
                return input_name
            
            logger.info(f"AI raw response: {response}")
            
            # Extract content from response dict
            if not isinstance(response, dict) or 'content' not in response:
                logger.error(f"Invalid response format from AI: {response}")
                return input_name
            
            content = response['content']
            if not content:
                logger.error(f"Empty content in AI response. Finish reason: {response.get('finish_reason')}")
                return input_name
            
            # Clean and validate response - remove markdown, links, and extra formatting
            result = content.strip()
            
            # Remove markdown headers (##, ###, etc)
            if result.startswith('#'):
                lines = result.split('\n')
                for line in lines:
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith('#') and not clean_line.startswith('[') and not clean_line.startswith('http'):
                        result = clean_line
                        break
            
            # Remove markdown links [text](url)
            import re
            result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)
            
            # Remove any remaining markdown formatting
            result = re.sub(r'[#*_`]', '', result)
            
            # Clean quotes and extra whitespace
            result = result.strip().strip('"').strip("'").strip()
            
            logger.info(f"AI response content: '{result}'")
            
            # Cache the result
            self._cache[cache_key] = result
            
            # Log the correction for debugging
            if result != input_name and result != "erro4040":
                logger.info(f"Municipality name corrected: '{input_name}' -> '{result}' for state {state_uf}")
            elif result == "erro4040":
                logger.info(f"Municipality '{input_name}' not found in state {state_uf}")
            
            return result
            
        except AttributeError as e:
            logger.error(f"AttributeError calling AI: {str(e)}")
            logger.warning("AI client may not have chat_completion method, returning input as-is")
            return input_name
        except Exception as e:
            logger.error(f"Error correcting municipality name: {str(e)}")
            # On error, return original input to not block user
            return input_name
    
    def clear_cache(self):
        """Clear the correction cache."""
        self._cache.clear()
        self.correct_municipality_name.cache_clear()
        logger.info("Municipality correction cache cleared")


# Singleton instance
_corrector_instance = None

def get_municipality_corrector() -> MunicipalityCorrector:
    """Get or create the singleton municipality corrector instance."""
    global _corrector_instance
    if _corrector_instance is None:
        _corrector_instance = MunicipalityCorrector()
    return _corrector_instance