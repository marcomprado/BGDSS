# OpenAIClient - Integração com IA

## Visão Geral

O `OpenAIClient` é a interface principal para integração com os serviços de OpenAI. Fornece uma camada de abstração robusta para chamadas de API, gerenciamento de tokens, tratamento de erros e otimização de performance.

**Localização**: `src/ai/openai_client.py`

## Funcionalidade Principal

### **Responsabilidades**
- 🤖 **API Integration**: Comunicação com serviços OpenAI
- 🔑 **Authentication**: Gerenciamento seguro de chaves de API
- 💰 **Token Management**: Controle e otimização de uso de tokens
- 🔄 **Retry Logic**: Tratamento inteligente de falhas e rate limits
- 📊 **Monitoring**: Coleta de métricas de uso e performance

## Arquitetura da Classe

```python
class OpenAIClient:
    """
    Cliente para integração com APIs da OpenAI.
    
    Fornece interface robusta com retry automático, gerenciamento
    de tokens e monitoramento de uso.
    """
```

### **Configuração e Inicialização**
```python
def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
    self.api_key = api_key or os.getenv('OPENAI_API_KEY')
    self.model = model
    self.client = openai.OpenAI(api_key=self.api_key)
    self.usage_stats = OpenAIUsageStats()
    self._validate_configuration()
```

### **Validação de Configuração**
```python
def _validate_configuration(self) -> None:
    if not self.api_key:
        raise OpenAIConfigurationError("OpenAI API key not provided")
    
    if not self.api_key.startswith('sk-'):
        raise OpenAIConfigurationError("Invalid OpenAI API key format")
    
    logger.info(f"OpenAI Client initialized with model: {self.model}")
```

## Métodos Principais

### **1. Comunicação com API**

#### `generate_completion(prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str`
**Propósito**: Gera completion de texto usando GPT.

```python
def generate_completion(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """
    Generate text completion using OpenAI GPT models.
    
    Args:
        prompt: Input text prompt
        max_tokens: Maximum tokens to generate
        temperature: Creativity level (0.0-1.0)
    
    Returns:
        Generated text completion
    """
    
    try:
        start_time = time.time()
        
        response = self._make_api_call(
            method='chat.completions.create',
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract response text
        completion_text = response.choices[0].message.content
        
        # Update usage statistics
        self._update_usage_stats(response.usage, time.time() - start_time)
        
        logger.debug(f"Completion generated: {len(completion_text)} characters")
        return completion_text
        
    except Exception as e:
        logger.error(f"Completion generation failed: {e}")
        raise OpenAIAPIError(f"Failed to generate completion: {e}")
```

#### `generate_chat_response(messages: List[Dict], temperature: float = 0.7) -> str`
**Propósito**: Gera resposta em formato de chat.

```python
def generate_chat_response(self, messages: List[Dict], temperature: float = 0.7) -> str:
    """
    Generate chat response using conversation history.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        temperature: Response creativity level
    
    Returns:
        AI-generated response
    """
    
    try:
        # Validate message format
        self._validate_messages(messages)
        
        # Calculate token usage estimate
        estimated_tokens = self._estimate_tokens(messages)
        if estimated_tokens > 3000:  # Conservative limit
            logger.warning(f"High token usage estimated: {estimated_tokens}")
        
        start_time = time.time()
        
        response = self._make_api_call(
            method='chat.completions.create',
            messages=messages,
            model=self.model,
            temperature=temperature
        )
        
        chat_response = response.choices[0].message.content
        
        # Update statistics
        self._update_usage_stats(response.usage, time.time() - start_time)
        
        return chat_response
        
    except Exception as e:
        logger.error(f"Chat response generation failed: {e}")
        raise OpenAIAPIError(f"Failed to generate chat response: {e}")
```

### **2. Análise e Processamento**

#### `analyze_content(content: str, analysis_type: str = "general") -> Dict[str, Any]`
**Propósito**: Analisa conteúdo usando IA.

```python
def analyze_content(self, content: str, analysis_type: str = "general") -> Dict[str, Any]:
    """
    Analyze content using AI to extract insights and structure.
    
    Args:
        content: Text content to analyze
        analysis_type: Type of analysis ('general', 'sentiment', 'keywords', 'summary')
    
    Returns:
        Dictionary with analysis results
    """
    
    analysis_prompts = {
        'general': """
        Analyze the following content and provide:
        1. Main topics and themes
        2. Key information extracted
        3. Content structure and organization
        4. Important entities (people, places, organizations)
        
        Content: {content}
        
        Provide response in JSON format.
        """,
        
        'sentiment': """
        Analyze the sentiment of this content:
        - Overall sentiment (positive/negative/neutral)
        - Confidence score (0-1)
        - Key emotional indicators
        
        Content: {content}
        
        Respond in JSON format.
        """,
        
        'keywords': """
        Extract key information from this content:
        - Top 10 keywords
        - Key phrases
        - Important concepts
        - Categories/tags
        
        Content: {content}
        
        Respond in JSON format.
        """,
        
        'summary': """
        Create a comprehensive summary of this content:
        - Executive summary (2-3 sentences)
        - Key points (bullet format)
        - Important details
        - Conclusions
        
        Content: {content}
        
        Respond in JSON format.
        """
    }
    
    try:
        prompt = analysis_prompts.get(analysis_type, analysis_prompts['general'])
        formatted_prompt = prompt.format(content=content[:4000])  # Limit content size
        
        response = self.generate_completion(
            prompt=formatted_prompt,
            max_tokens=1500,
            temperature=0.3  # Lower temperature for more focused analysis
        )
        
        # Try to parse JSON response
        try:
            analysis_result = json.loads(response)
        except json.JSONDecodeError:
            # Fallback to text response
            analysis_result = {
                'analysis_type': analysis_type,
                'raw_response': response,
                'parsed': False
            }
        
        analysis_result['content_length'] = len(content)
        analysis_result['analysis_timestamp'] = datetime.now().isoformat()
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Content analysis failed: {e}")
        raise OpenAIAPIError(f"Failed to analyze content: {e}")
```

#### `extract_structured_data(html_content: str, target_fields: List[str]) -> Dict[str, Any]`
**Propósito**: Extrai dados estruturados de HTML usando IA.

### **3. Gerenciamento de API e Retry**

#### `_make_api_call(method: str, **kwargs) -> Any`
**Propósito**: Realiza chamada de API com retry automático.

```python
def _make_api_call(self, method: str, **kwargs) -> Any:
    """
    Make API call with automatic retry and error handling.
    
    Implements exponential backoff for rate limits and temporary failures.
    """
    
    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            # Get the actual API method
            api_method = self._get_api_method(method)
            
            # Make the API call
            response = api_method(**kwargs)
            
            logger.debug(f"API call successful: {method}")
            return response
            
        except openai.RateLimitError as e:
            if attempt == max_retries - 1:
                raise OpenAIRateLimitError(f"Rate limit exceeded after {max_retries} attempts")
            
            # Exponential backoff for rate limits
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1})")
            time.sleep(delay)
            
        except openai.APIError as e:
            if attempt == max_retries - 1:
                raise OpenAIAPIError(f"API error after {max_retries} attempts: {e}")
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"API error, retrying in {delay:.2f}s: {e}")
            time.sleep(delay)
            
        except Exception as e:
            logger.error(f"Unexpected error in API call: {e}")
            raise OpenAIAPIError(f"Unexpected API error: {e}")
```

#### `_get_api_method(method_name: str) -> callable`
**Propósito**: Obtém método da API dinamicamente.

### **4. Monitoramento e Estatísticas**

#### `get_usage_stats() -> Dict[str, Any]`
**Propósito**: Retorna estatísticas de uso.

```python
def get_usage_stats(self) -> Dict[str, Any]:
    """Get comprehensive usage statistics."""
    
    return {
        'total_requests': self.usage_stats.total_requests,
        'successful_requests': self.usage_stats.successful_requests,
        'failed_requests': self.usage_stats.failed_requests,
        'total_tokens_used': self.usage_stats.total_tokens_used,
        'total_cost_estimate': self.usage_stats.estimated_cost,
        'average_response_time': self.usage_stats.average_response_time,
        'success_rate': self.usage_stats.success_rate,
        'requests_by_model': self.usage_stats.requests_by_model,
        'tokens_by_operation': self.usage_stats.tokens_by_operation,
        'peak_usage_day': self.usage_stats.peak_usage_day,
        'current_rate_limit_status': self._check_rate_limit_status()
    }
```

#### `_update_usage_stats(usage_info: Any, response_time: float) -> None`
**Propósito**: Atualiza estatísticas de uso.

#### `estimate_cost(tokens_used: int, model: str = None) -> float`
**Propósito**: Estima custo baseado no uso de tokens.

### **5. Utilitários e Validação**

#### `_validate_messages(messages: List[Dict]) -> None`
**Propósito**: Valida formato das mensagens de chat.

```python
def _validate_messages(self, messages: List[Dict]) -> None:
    """Validate chat message format."""
    
    if not isinstance(messages, list):
        raise ValueError("Messages must be a list")
    
    for i, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"Message {i} must be a dictionary")
        
        if 'role' not in message:
            raise ValueError(f"Message {i} missing 'role' field")
        
        if 'content' not in message:
            raise ValueError(f"Message {i} missing 'content' field")
        
        if message['role'] not in ['system', 'user', 'assistant']:
            raise ValueError(f"Message {i} has invalid role: {message['role']}")
```

#### `_estimate_tokens(content: Any) -> int`
**Propósito**: Estima número de tokens para conteúdo.

#### `_check_rate_limit_status() -> Dict[str, Any]`
**Propósito**: Verifica status atual de rate limits.

## Sistema de Estatísticas

### **OpenAIUsageStats Class**
```python
@dataclass
class OpenAIUsageStats:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens_used: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    estimated_cost: float = 0.0
    total_response_time: float = 0.0
    requests_by_model: Dict[str, int] = field(default_factory=dict)
    tokens_by_operation: Dict[str, int] = field(default_factory=dict)
    daily_usage: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests
    
    def record_request(self, model: str, operation: str, tokens_used: int, 
                      response_time: float, success: bool) -> None:
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
            self.total_tokens_used += tokens_used
            self.total_response_time += response_time
            
            # Track by model
            self.requests_by_model[model] = self.requests_by_model.get(model, 0) + 1
            
            # Track by operation
            self.tokens_by_operation[operation] = self.tokens_by_operation.get(operation, 0) + tokens_used
            
            # Estimate cost (approximate)
            self.estimated_cost += self._estimate_cost(model, tokens_used)
        else:
            self.failed_requests += 1
```

## Tratamento de Erros

### **Exceções Customizadas**
```python
class OpenAIError(Exception):
    """Base exception for OpenAI client errors"""

class OpenAIConfigurationError(OpenAIError):
    """Configuration or authentication error"""

class OpenAIAPIError(OpenAIError):
    """API call error"""

class OpenAIRateLimitError(OpenAIError):
    """Rate limit exceeded error"""

class OpenAIContentError(OpenAIError):
    """Content processing error"""
```

### **Error Recovery Strategies**
```python
def _handle_api_error(self, error: Exception, attempt: int) -> bool:
    """
    Handle API errors with appropriate recovery strategy.
    
    Returns True if retry should be attempted, False otherwise.
    """
    
    if isinstance(error, openai.RateLimitError):
        # Always retry rate limits with backoff
        return attempt < 5
    
    elif isinstance(error, openai.APIConnectionError):
        # Retry connection errors
        return attempt < 3
    
    elif isinstance(error, openai.InvalidRequestError):
        # Don't retry invalid requests
        logger.error(f"Invalid request: {error}")
        return False
    
    elif isinstance(error, openai.AuthenticationError):
        # Don't retry auth errors
        logger.error(f"Authentication failed: {error}")
        return False
    
    else:
        # Retry other errors conservatively
        return attempt < 2
```

## Configuração

### **Configurações de Modelo**
```python
model_configs = {
    'gpt-3.5-turbo': {
        'max_tokens': 4096,
        'cost_per_token': 0.002 / 1000,
        'context_window': 4096
    },
    'gpt-4': {
        'max_tokens': 8192,
        'cost_per_token': 0.03 / 1000,
        'context_window': 8192
    }
}
```

### **Configurações de Rate Limiting**
```python
rate_limit_config = {
    'max_requests_per_minute': 60,
    'max_tokens_per_minute': 150000,
    'backoff_factor': 2.0,
    'max_backoff_delay': 60.0
}
```

## Exemplos de Uso

### **Uso Básico**
```python
from src.ai.openai_client import OpenAIClient

# Initialize client
client = OpenAIClient(model="gpt-3.5-turbo")

# Generate completion
response = client.generate_completion(
    prompt="Explain web scraping in simple terms",
    max_tokens=500,
    temperature=0.7
)

print(response)
```

### **Análise de Conteúdo**
```python
# Analyze scraped content
scraped_html = "<html>...</html>"
analysis = client.analyze_content(scraped_html, analysis_type="keywords")

print(f"Keywords: {analysis.get('keywords', [])}")
print(f"Summary: {analysis.get('summary', '')}")
```

### **Chat com Contexto**
```python
messages = [
    {"role": "system", "content": "You are a web scraping expert"},
    {"role": "user", "content": "How do I handle JavaScript-rendered content?"}
]

response = client.generate_chat_response(messages, temperature=0.5)
print(response)
```

### **Monitoramento de Uso**
```python
def monitor_openai_usage(client: OpenAIClient):
    stats = client.get_usage_stats()
    
    print(f"Total requests: {stats['total_requests']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"Estimated cost: ${stats['total_cost_estimate']:.4f}")
    
    if stats['total_cost_estimate'] > 10.0:
        logger.warning("High API usage detected!")
```

## Integração com Outros Componentes

### **Com Navigator Agent**
```python
# navigator_agent.py
self.openai_client = OpenAIClient()

def analyze_page_structure(self, html_content: str) -> Dict:
    return self.openai_client.analyze_content(html_content, "structure")
```

### **Com PDF Processor**
```python
# pdf_processor_agent.py
def extract_key_information(self, pdf_text: str) -> Dict:
    return self.openai_client.analyze_content(pdf_text, "summary")
```

## Logs e Debugging

### **Logging Estruturado**
```python
logger.info("OpenAI API call completed", extra={
    "model": self.model,
    "tokens_used": response.usage.total_tokens,
    "response_time": response_time,
    "operation": "completion"
})
```

### **Debug Mode**
```python
if settings.DEBUG_OPENAI:
    logger.debug(f"Prompt: {prompt[:200]}...")
    logger.debug(f"Response: {response[:200]}...")
    logger.debug(f"Token usage: {response.usage.total_tokens}")
```

---

**O OpenAIClient fornece uma interface robusta e eficiente para integração com serviços de IA, garantindo uso otimizado e monitoramento abrangente.**