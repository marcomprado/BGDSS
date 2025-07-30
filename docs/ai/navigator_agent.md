# NavigatorAgent - Navegação Inteligente

## Visão Geral

O `NavigatorAgent` utiliza IA para navegação inteligente em websites, analisando estrutura de páginas, tomando decisões de navegação e resolvendo desafios complexos de scraping automaticamente.

**Localização**: `src/ai/navigator_agent.py`

## Funcionalidade Principal

### **Responsabilidades**
- 🧭 **Navegação Inteligente**: Análise automática de estrutura de páginas
- 🤖 **Tomada de Decisão**: Escolha automática de estratégias de scraping
- 🔍 **Detecção de Elementos**: Identificação inteligente de seletores
- 🛡️ **Bypass de Proteções**: Contorno inteligente de anti-bot measures
- 📊 **Análise de Conteúdo**: Compreensão semântica do conteúdo

## Arquitetura da Classe

```python
class NavigatorAgent:
    """
    Agente de navegação inteligente usando IA para análise
    e tomada de decisões em web scraping.
    """
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.navigation_history: List[NavigationStep] = []
        self.learned_patterns: Dict[str, Any] = {}
```

## Métodos Principais

### **1. Análise de Página**

#### `analyze_page_structure(driver: WebDriver, url: str) -> PageAnalysis`
**Propósito**: Analisa estrutura e conteúdo da página atual.

```python
def analyze_page_structure(self, driver: WebDriver, url: str) -> PageAnalysis:
    try:
        # Get page source and metadata
        html_content = driver.page_source
        page_title = driver.title
        current_url = driver.current_url
        
        # Extract key elements
        key_elements = self._extract_key_elements(driver)
        
        # AI analysis of page structure
        analysis_prompt = f\"\"\"
        Analyze this webpage structure and provide navigation insights:
        
        URL: {url}
        Title: {page_title}
        Key Elements Found: {key_elements}
        
        HTML Sample: {html_content[:2000]}
        
        Provide JSON response with:
        1. page_type (e.g., "product_list", "article", "form", "login")
        2. navigation_elements (links, buttons, forms)
        3. data_elements (content sections, tables, lists)
        4. anti_bot_indicators (captcha, rate limiting signs)
        5. recommended_strategy (how to proceed with scraping)
        \"\"\"
        
        ai_analysis = self.openai_client.analyze_content(
            analysis_prompt, 
            analysis_type="structure"
        )
        
        return PageAnalysis(
            url=current_url,
            title=page_title,
            page_type=ai_analysis.get('page_type', 'unknown'),
            elements=key_elements,
            ai_insights=ai_analysis,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Page analysis failed: {e}")
        raise NavigationError(f"Failed to analyze page: {e}")
```

#### `detect_optimal_selectors(driver: WebDriver, target_content: str) -> List[str]`
**Propósito**: Detecta seletores CSS/XPath ideais para conteúdo específico.

### **2. Navegação Inteligente**

#### `navigate_to_content(driver: WebDriver, target_description: str) -> NavigationResult`
**Propósito**: Navega automaticamente para conteúdo específico.

```python
def navigate_to_content(self, driver: WebDriver, target_description: str) -> NavigationResult:
    try:
        current_analysis = self.analyze_page_structure(driver, driver.current_url)
        
        navigation_prompt = f\"\"\"
        I need to navigate to: {target_description}
        
        Current page analysis: {current_analysis.ai_insights}
        Available navigation elements: {current_analysis.elements.get('navigation', [])}
        
        Provide step-by-step navigation instructions in JSON:
        {{
            "strategy": "click_link|fill_form|scroll|wait",
            "target_selector": "CSS or XPath selector",
            "actions": [
                {{"action": "click", "selector": "...", "description": "..."}},
                {{"action": "wait", "condition": "...", "timeout": 10}}
            ],
            "expected_outcome": "description of expected result",
            "fallback_strategy": "alternative approach if primary fails"
        }}
        \"\"\"
        
        navigation_plan = self.openai_client.generate_completion(
            navigation_prompt,
            max_tokens=800,
            temperature=0.3
        )
        
        # Execute navigation plan
        result = self._execute_navigation_plan(driver, navigation_plan)
        
        # Record navigation step
        self._record_navigation_step(current_analysis, navigation_plan, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        raise NavigationError(f"Failed to navigate to content: {e}")
```

#### `handle_dynamic_content(driver: WebDriver, wait_strategy: str = "auto") -> bool`
**Propósito**: Lida com conteúdo carregado dinamicamente.

### **3. Resolução de Problemas**

#### `bypass_anti_bot_measures(driver: WebDriver) -> Dict[str, Any]`
**Propósito**: Identifica e contorna medidas anti-bot.

```python
def bypass_anti_bot_measures(self, driver: WebDriver) -> Dict[str, Any]:
    try:
        # Detect anti-bot measures
        current_page = driver.page_source.lower()
        
        anti_bot_indicators = {
            'captcha': 'captcha' in current_page or 'recaptcha' in current_page,
            'cloudflare': 'cloudflare' in current_page,
            'rate_limit': 'rate limit' in current_page or 'too many requests' in current_page,
            'javascript_challenge': 'checking your browser' in current_page,
            'access_denied': 'access denied' in current_page or 'forbidden' in current_page
        }
        
        detected_measures = [k for k, v in anti_bot_indicators.items() if v]
        
        if not detected_measures:
            return {'status': 'no_protection_detected', 'actions_taken': []}
        
        # AI-powered strategy selection
        bypass_prompt = f\"\"\"
        Detected anti-bot measures: {detected_measures}
        Current page indicators: {anti_bot_indicators}
        
        Suggest bypass strategies in JSON format:
        {{
            "detected_protection": [list of detected measures],
            "recommended_actions": [
                {{"action": "wait", "duration": 5, "reason": "..."}},
                {{"action": "change_user_agent", "value": "...", "reason": "..."}},
                {{"action": "add_headers", "headers": {{}}, "reason": "..."}},
                {{"action": "slow_down", "delay": 3, "reason": "..."}}
            ],
            "success_probability": 0.8,
            "alternative_strategies": ["..."]
        }}
        \"\"\"
        
        strategy = self.openai_client.generate_completion(
            bypass_prompt,
            max_tokens=600,
            temperature=0.2
        )
        
        # Implement suggested strategies
        actions_taken = self._implement_bypass_strategies(driver, strategy)
        
        return {
            'status': 'bypass_attempted',
            'detected_measures': detected_measures,
            'actions_taken': actions_taken,
            'strategy_used': strategy
        }
        
    except Exception as e:
        logger.error(f"Anti-bot bypass failed: {e}")
        return {'status': 'bypass_failed', 'error': str(e)}
```

### **4. Aprendizado e Otimização**

#### `learn_from_navigation(site_name: str, navigation_history: List[NavigationStep]) -> None`
**Propósito**: Aprende padrões de navegação para otimização futura.

```python
def learn_from_navigation(self, site_name: str, navigation_history: List[NavigationStep]) -> None:
    try:
        # Extract patterns from successful navigations
        successful_steps = [step for step in navigation_history if step.success]
        
        if not successful_steps:
            logger.warning(f"No successful navigation steps to learn from for {site_name}")
            return
        
        learning_prompt = f\"\"\"
        Analyze these successful navigation patterns for {site_name}:
        
        {[step.to_dict() for step in successful_steps]}
        
        Extract reusable patterns in JSON:
        {{
            "common_selectors": ["list of frequently used selectors"],
            "navigation_patterns": ["common navigation sequences"],
            "timing_patterns": {{"average_wait_time": 2.5, "load_indicators": ["..."]}},
            "success_indicators": ["signs that navigation succeeded"],
            "optimization_suggestions": ["ways to improve efficiency"]
        }}
        \"\"\"
        
        patterns = self.openai_client.analyze_content(
            learning_prompt,
            analysis_type="patterns"
        )
        
        # Store learned patterns
        if site_name not in self.learned_patterns:
            self.learned_patterns[site_name] = {}
        
        self.learned_patterns[site_name].update(patterns)
        
        logger.info(f"Updated navigation patterns for {site_name}")
        
    except Exception as e:
        logger.error(f"Learning from navigation failed: {e}")
```

### **5. Utilitários de Navegação**

#### `wait_for_element_intelligent(driver: WebDriver, description: str, timeout: int = 30) -> WebElement`
**Propósito**: Espera inteligente por elementos baseada em descrição.

#### `extract_data_with_context(driver: WebDriver, data_description: str) -> Dict[str, Any]`
**Propósito**: Extrai dados usando compreensão contextual.

## Classes de Apoio

### **PageAnalysis**
```python
@dataclass
class PageAnalysis:
    url: str
    title: str
    page_type: str
    elements: Dict[str, List[str]]
    ai_insights: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url': self.url,
            'title': self.title,
            'page_type': self.page_type,
            'elements': self.elements,
            'ai_insights': self.ai_insights,
            'timestamp': self.timestamp.isoformat()
        }
```

### **NavigationStep**
```python
@dataclass
class NavigationStep:
    action_type: str
    selector: str
    description: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

## Exemplos de Uso

### **Análise Básica de Página**
```python
from src.ai.navigator_agent import NavigatorAgent
from src.ai.openai_client import OpenAIClient

# Initialize
client = OpenAIClient()
navigator = NavigatorAgent(client)

# Analyze current page
analysis = navigator.analyze_page_structure(driver, current_url)
print(f"Page type: {analysis.page_type}")
print(f"Key elements: {analysis.elements}")
```

### **Navegação Inteligente**
```python
# Navigate to specific content
result = navigator.navigate_to_content(
    driver, 
    "Find the product pricing information"
)

if result.success:
    print("Successfully navigated to pricing info")
else:
    print(f"Navigation failed: {result.error_message}")
```

### **Tratamento de Anti-Bot**
```python
# Handle anti-bot measures
bypass_result = navigator.bypass_anti_bot_measures(driver)

if bypass_result['status'] == 'no_protection_detected':
    print("No anti-bot protection detected")
else:
    print(f"Protection detected: {bypass_result['detected_measures']}")
    print(f"Actions taken: {bypass_result['actions_taken']}")
```

---

**O NavigatorAgent transforma web scraping em um processo inteligente e adaptativo, usando IA para superar desafios complexos de navegação.**