"""
OpenAI client with retry logic, rate limiting, and error handling.
"""

import time
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
import openai
from openai import OpenAI

from src.utils.exceptions import AIError
from src.utils.logger import logger
from config.settings import settings


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int = 60, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            self.calls = [call for call in self.calls if call > now - self.period]
            
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.calls = [call for call in self.calls if call > now - self.period]
            
            self.calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper


class OpenAIClient:
    """Enhanced OpenAI client with retry logic and error handling."""
    
    def __init__(self, api_key: Optional[str] = None, max_retries: int = 3):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OpenAI API key not provided - AI features will be disabled")
            self.client = None
            self.enabled = False
            return
        
        self.client = OpenAI(api_key=self.api_key)
        self.enabled = True
        self.max_retries = max_retries
        self.default_model = settings.OPENAI_MODEL
        self.default_temperature = settings.OPENAI_TEMPERATURE
        self.default_max_tokens = settings.OPENAI_MAX_TOKENS
        
        self._rate_limiter = RateLimiter(max_calls=50, period=60)
        
        logger.info("OpenAI client initialized")
    
    def _handle_api_error(self, error: Exception, attempt: int) -> None:
        """Handle API errors with appropriate logging and raising."""
        error_message = str(error)
        
        if isinstance(error, openai.RateLimitError):
            logger.warning(f"Rate limit error on attempt {attempt}: {error_message}")
            if attempt < self.max_retries:
                time.sleep(min(2 ** attempt, 60))
            else:
                raise AIError("Rate limit exceeded", api_error=error_message)
        
        elif isinstance(error, openai.AuthenticationError):
            logger.error(f"Authentication error: {error_message}")
            raise AIError("Invalid API key", api_error=error_message)
        
        elif isinstance(error, openai.APIError):
            logger.error(f"API error on attempt {attempt}: {error_message}")
            if attempt < self.max_retries:
                time.sleep(2 ** attempt)
            else:
                raise AIError("OpenAI API error", api_error=error_message)
        
        else:
            logger.error(f"Unexpected error on attempt {attempt}: {error_message}")
            raise AIError("Unexpected error", api_error=error_message)
    
    @RateLimiter(max_calls=50, period=60)
    def chat_completion(self,
                       messages: List[Dict[str, str]],
                       model: Optional[str] = None,
                       temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None,
                       **kwargs) -> Dict[str, Any]:
        """Create a chat completion with retry logic."""
        if not self.enabled:
            raise AIError("OpenAI client is disabled - API key not provided")
        
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens or self.default_max_tokens
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Sending chat completion request (attempt {attempt + 1})")
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                result = {
                    'content': response.choices[0].message.content,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    },
                    'model': response.model,
                    'finish_reason': response.choices[0].finish_reason
                }
                
                logger.info(f"Chat completion successful. Tokens used: {result['usage']['total_tokens']}")
                return result
                
            except Exception as e:
                self._handle_api_error(e, attempt + 1)
        
        raise AIError("Max retries exceeded for chat completion")
    
    def create_prompt(self, 
                     system_prompt: str,
                     user_content: str,
                     assistant_context: Optional[str] = None) -> List[Dict[str, str]]:
        """Create a properly formatted message list for the API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        if assistant_context:
            messages.insert(1, {"role": "assistant", "content": assistant_context})
        
        return messages
    
    def analyze_webpage(self, html_content: str, task_description: str) -> Dict[str, Any]:
        """Analyze webpage content for specific task."""
        if not self.enabled:
            logger.warning("AI analysis not available - returning basic analysis")
            return {
                'content': 'AI analysis disabled - OpenAI API key not provided',
                'analysis': 'Basic HTML parsing only',
                'recommendations': ['Configure OpenAI API key for AI-powered analysis']
            }
        
        system_prompt = """You are a web scraping assistant that analyzes HTML content.
        Provide clear, structured responses about the webpage content and how to interact with it.
        Focus on identifying downloadable files, forms, and navigation elements."""
        
        user_content = f"""Task: {task_description}
        
        HTML Content (truncated):
        {html_content[:8000]}
        
        Please analyze this webpage and provide:
        1. Summary of the page content
        2. Downloadable files found (if any)
        3. Forms and input fields
        4. Navigation recommendations
        5. Any potential issues or warnings"""
        
        messages = self.create_prompt(system_prompt, user_content)
        return self.chat_completion(messages)
    
    def extract_structured_data(self, 
                               text_content: str,
                               extraction_template: Dict[str, str]) -> Dict[str, Any]:
        """Extract structured data from text using a template."""
        if not self.enabled:
            logger.warning("AI extraction not available - returning empty result")
            return {
                'error': 'AI extraction disabled - OpenAI API key not provided',
                'data': {},
                'extracted_fields': list(extraction_template.keys())
            }
        
        system_prompt = """You are a data extraction specialist.
        Extract structured data from the provided text according to the template.
        Return data in JSON format. Be precise and accurate."""
        
        template_str = "\n".join([f"- {key}: {desc}" for key, desc in extraction_template.items()])
        
        user_content = f"""Extract the following information from the text:
        
        Template:
        {template_str}
        
        Text Content:
        {text_content[:10000]}
        
        Return the extracted data as a valid JSON object."""
        
        messages = self.create_prompt(system_prompt, user_content)
        
        response = self.chat_completion(
            messages,
            response_format={"type": "json_object"}
        )
        
        try:
            import json
            return json.loads(response['content'])
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from AI")
            return {'error': 'Failed to parse response', 'raw_content': response['content']}
    
    def generate_navigation_instructions(self,
                                       current_state: str,
                                       target_goal: str,
                                       available_actions: List[str]) -> str:
        """Generate step-by-step navigation instructions."""
        system_prompt = """You are a web navigation expert.
        Provide clear, actionable instructions for navigating websites.
        Be specific about which elements to click and what to look for."""
        
        user_content = f"""Current State: {current_state}
        
        Goal: {target_goal}
        
        Available Actions:
        {chr(10).join([f"- {action}" for action in available_actions])}
        
        Provide step-by-step instructions to reach the goal."""
        
        messages = self.create_prompt(system_prompt, user_content)
        response = self.chat_completion(messages, temperature=0.3)
        
        return response['content']
    
    def validate_extraction_result(self,
                                  extracted_data: Dict[str, Any],
                                  validation_rules: Dict[str, str]) -> Dict[str, Any]:
        """Validate extracted data against rules."""
        system_prompt = """You are a data validation specialist.
        Check if the extracted data meets the validation requirements.
        Provide detailed feedback on any issues found."""
        
        rules_str = "\n".join([f"- {field}: {rule}" for field, rule in validation_rules.items()])
        
        user_content = f"""Validate this data:
        
        Data:
        {extracted_data}
        
        Validation Rules:
        {rules_str}
        
        Return a validation report with:
        1. Overall validity (true/false)
        2. Field-by-field validation results
        3. Specific issues found
        4. Suggestions for correction"""
        
        messages = self.create_prompt(system_prompt, user_content)
        response = self.chat_completion(messages, temperature=0.1)
        
        return {
            'validation_report': response['content'],
            'tokens_used': response['usage']['total_tokens']
        }
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count for a text string."""
        return len(text) // 4
    
    def check_health(self) -> bool:
        """Check if the OpenAI API is accessible."""
        try:
            response = self.chat_completion(
                [{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False