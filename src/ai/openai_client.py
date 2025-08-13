"""
OpenAI client for PDF processing - text-only operations with retry logic, rate limiting, and error handling.
Optimized for document analysis and structured data extraction from PDFs.
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


def _extract_json_from_response(content: str) -> str:
    """Extract JSON from AI response, handling markdown code blocks."""
    content = content.strip()
    
    # Handle markdown-wrapped JSON response
    if content.startswith('```json'):
        # Extract JSON from markdown code block
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            return content[start_idx:end_idx]
    
    return content


class OpenAIClient:
    """OpenAI client optimized for PDF processing and text analysis."""
    
    def __init__(self, api_key: Optional[str] = None, max_retries: int = 3):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.max_retries = max_retries
        self.enabled = False
        self.client = None
        self.provider = settings.AI_PROVIDER
        self.provider_config = None
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided - PDF processing will be disabled")
            return
        
        try:
            # Parse provider config if available
            if settings.AI_PROVIDER_CONFIG:
                import json
                try:
                    self.provider_config = json.loads(settings.AI_PROVIDER_CONFIG)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid AI_PROVIDER_CONFIG JSON: {settings.AI_PROVIDER_CONFIG}")
            
            # Configure client based on provider
            if self.provider == 'openrouter':
                # OpenRouter configuration
                base_url = settings.AI_BASE_URL or "https://openrouter.ai/api/v1"
                logger.info(f"Configuring OpenRouter client with base URL: {base_url}")
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=base_url
                )
            elif settings.AI_BASE_URL:
                # Custom provider with base URL
                logger.info(f"Configuring custom AI provider with base URL: {settings.AI_BASE_URL}")
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=settings.AI_BASE_URL
                )
            else:
                # Standard OpenAI configuration
                logger.info("Configuring standard OpenAI client")
                self.client = OpenAI(api_key=self.api_key)
            
            # Model configuration from settings
            if not settings.OPENAI_MODEL:
                logger.error("OPENAI_MODEL not configured in .env file")
                raise ValueError("OPENAI_MODEL must be set in .env file")
            
            self.default_model = settings.OPENAI_MODEL
            self.enabled = True
            self.default_temperature = settings.OPENAI_TEMPERATURE or 0.1  # Lower temp for structured data
            self.default_max_tokens = settings.OPENAI_MAX_TOKENS or 5000
            self._rate_limiter = RateLimiter(max_calls=50, period=60)
            
            logger.info(f"AI client initialized with provider: {self.provider}, model: {self.default_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            self.client = None
            self.enabled = False
    
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
                if not self.client:
                    raise AIError("OpenAI client not initialized")
                
                # Add provider-specific configuration
                extra_params = {}
                if self.provider_config:
                    # Use custom provider config from JSON
                    extra_params['extra_body'] = self.provider_config
                elif self.provider == 'openrouter':
                    # Check if user specified a provider preference
                    provider_pref = settings.AI_PROVIDER_PREFERENCE.strip()
                    if provider_pref:
                        # User specified a specific provider
                        extra_params['extra_body'] = {
                            "provider": {
                                "only": [provider_pref]
                            }
                        }
                    # Else: Let OpenRouter choose automatically (no extra_body)
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **extra_params,
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
    
    def analyze_pdf_text(self, pdf_text: str, extraction_goal: str) -> Dict[str, Any]:
        """Analyze PDF text content for data extraction."""
        if not self.enabled:
            logger.warning("AI analysis not available - returning basic analysis")
            return {
                'content': 'AI analysis disabled - OpenAI API key not provided',
                'analysis': 'Basic text parsing only',
                'recommendations': ['Configure OpenAI API key for AI-powered PDF analysis']
            }
        
        system_prompt = """You are a document analysis specialist focused on extracting structured data from PDF documents.
        Analyze the provided text content and extract relevant information based on the specified goal.
        Return clear, structured responses with extracted data in a consistent format."""
        
        user_content = f"""Extraction Goal: {extraction_goal}
        
        PDF Text Content (truncated if necessary):
        {pdf_text[:15000] if len(pdf_text) > 15000 else pdf_text}
        
        Please analyze this PDF content and provide:
        1. Document type and structure summary
        2. Key data fields identified
        3. Extracted structured data
        4. Data quality assessment
        5. Any extraction issues or recommendations"""
        
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
            messages
            # Note: response_format not supported by model
        )
        
        try:
            import json
            json_content = _extract_json_from_response(response['content'])
            return json.loads(json_content)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from AI")
            return {'error': 'Failed to parse response', 'raw_content': response['content']}
    
    def extract_pdf_metadata(self, pdf_text: str) -> Dict[str, Any]:
        """Extract metadata and document information from PDF text."""
        if not self.enabled:
            return {'error': 'AI analysis disabled'}
        
        system_prompt = """You are a document metadata extraction specialist.
        Extract key metadata and document information from PDF text content.
        Focus on dates, document types, organizations, locations, and other identifying information."""
        
        user_content = f"""PDF Text Content:
        {pdf_text[:10000] if len(pdf_text) > 10000 else pdf_text}
        
        Extract the following metadata (return as JSON):
        - document_type: Type of document
        - date_created: Document creation date
        - date_period: Time period the document covers
        - organization: Issuing organization
        - location: Geographic location mentioned
        - key_subjects: Main topics/subjects
        - document_id: Any ID numbers found
        - language: Document language"""
        
        messages = self.create_prompt(system_prompt, user_content)
        response = self.chat_completion(
            messages,
            temperature=0.1
            # Note: response_format not supported by model
        )
        
        try:
            import json
            json_content = _extract_json_from_response(response['content'])
            return json.loads(json_content)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from AI")
            return {'error': 'Failed to parse response', 'raw_content': response['content']}
    
    def process_brazilian_government_pdf(self, pdf_text: str, document_type: str) -> Dict[str, Any]:
        """Process Brazilian government PDFs with domain-specific knowledge."""
        if not self.enabled:
            return {'error': 'AI processing disabled'}
        
        system_prompt = f"""You are a specialist in Brazilian government documents with expertise in {document_type}.
        Extract structured data from Brazilian government PDFs following Brazilian administrative standards.
        Pay attention to Brazilian date formats (DD/MM/YYYY), currency (R$), legal references, and administrative terminology.
        Return data in a structured JSON format suitable for database storage."""
        
        # Customize extraction based on document type
        if document_type.lower() in ['resolucao', 'deliberacao']:
            extraction_fields = """
            - numero_resolucao: Resolution number
            - data_publicacao: Publication date (DD/MM/YYYY)
            - orgao_emissor: Issuing government body
            - assunto: Subject/topic
            - categoria: Category of resolution
            - vigencia: Validity period
            - referencias_legais: Legal references cited
            """
        elif document_type.lower() in ['parcelas', 'pagamento']:
            extraction_fields = """
            - municipio: Municipality name
            - valor_parcela: Payment amount (R$)
            - data_pagamento: Payment date (DD/MM/YYYY)
            - programa: Program name
            - beneficiario: Beneficiary
            - ano_exercicio: Fiscal year
            - mes_referencia: Reference month
            """
        elif document_type.lower() in ['saldo', 'balanco']:
            extraction_fields = """
            - municipio: Municipality name
            - conta: Account name/type
            - saldo_anterior: Previous balance (R$)
            - creditos: Credits (R$)
            - debitos: Debits (R$)
            - saldo_atual: Current balance (R$)
            - data_referencia: Reference date (DD/MM/YYYY)
            """
        else:
            extraction_fields = """
            - tipo_documento: Document type
            - numero_documento: Document number
            - data: Date (DD/MM/YYYY)
            - orgao: Government body
            - valor: Amount if applicable (R$)
            - municipio: Municipality if applicable
            """
        
        user_content = f"""Document Type: {document_type}
        
        PDF Text Content:
        {pdf_text[:20000] if len(pdf_text) > 20000 else pdf_text}
        
        Extract the following structured data as JSON:
        {extraction_fields}
        
        Additional metadata:
        - data_extracao: Current date
        - confianca_extracao: Confidence level (1-10)
        - observacoes: Any extraction notes"""
        
        messages = self.create_prompt(system_prompt, user_content)
        response = self.chat_completion(
            messages,
            temperature=0.05  # Very low temperature for accuracy
            # Note: response_format not supported by model
        )
        
        try:
            import json
            from datetime import datetime
            json_content = _extract_json_from_response(response['content'])
            result = json.loads(json_content)
            result['data_extracao'] = datetime.now().isoformat()
            return result
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from AI")
            return {'error': 'Failed to parse response', 'raw_content': response['content']}
    
    def validate_extraction_result(self,
                                  extracted_data: Dict[str, Any],
                                  validation_rules: Dict[str, str]) -> Dict[str, Any]:
        """Validate extracted data against rules."""
        system_prompt = """You are a data validation specialist for Brazilian government documents.
        Check if the extracted data meets validation requirements and Brazilian data standards.
        Validate date formats (DD/MM/YYYY), currency formats (R$), and administrative data quality."""
        
        rules_str = "\n".join([f"- {field}: {rule}" for field, rule in validation_rules.items()])
        
        user_content = f"""Validate this Brazilian government data:
        
        Data:
        {extracted_data}
        
        Validation Rules:
        {rules_str}
        
        Return a validation report as JSON with:
        - valido: Overall validity (true/false)
        - campos_validos: Field-by-field validation results
        - problemas_encontrados: Specific issues found
        - sugestoes_correcao: Suggestions for correction
        - nota_qualidade: Data quality score (1-10)"""
        
        messages = self.create_prompt(system_prompt, user_content)
        response = self.chat_completion(
            messages, 
            temperature=0.1
            # Note: response_format not supported by model
        )
        
        try:
            import json
            json_content = _extract_json_from_response(response['content'])
            validation_result = json.loads(json_content)
            validation_result['tokens_used'] = response['usage']['total_tokens']
            return validation_result
        except json.JSONDecodeError:
            return {
                'error': 'Failed to parse validation response',
                'raw_content': response['content'],
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