# WebScraperApplication - Orquestração Central

## Visão Geral

A classe `WebScraperApplication` é o coração do sistema Web Scraper AI. Ela atua como orquestrador central, coordenando todos os componentes e gerenciando o ciclo de vida da aplicação.

**Localização**: `src/core/application.py`

## Funcionalidade Principal

### **Responsabilidades**
- 🏗️ **Inicialização**: Configura e inicializa todos os componentes do sistema
- 🔄 **Orquestração**: Coordena interações entre diferentes módulos
- 📊 **Monitoramento**: Fornece status e métricas da aplicação
- 🛡️ **Gerenciamento de Estado**: Mantém estado global da aplicação
- 🔧 **Configuração**: Gerencia configurações do sistema

## Arquitetura da Classe

```python
class WebScraperApplication:
    """
    Classe principal da aplicação Web Scraper AI.
    
    Implementa padrão Singleton para garantir instância única.
    Coordena todos os componentes do sistema.
    """
```

### **Singleton Pattern**
```python
_instance = None
_lock = threading.Lock()

def __new__(cls):
    if cls._instance is None:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
    return cls._instance
```

**Justificativa**: Garante que existe apenas uma instância da aplicação, evitando conflitos de estado e recursos.

## Métodos Principais

### **1. Inicialização**

#### `initialize() -> None`
**Propósito**: Inicializa todos os componentes da aplicação.

**Fluxo de Execução**:
1. Verifica se já está inicializada
2. Carrega configurações do sistema
3. Inicializa logger
4. Configura componentes AI
5. Inicializa sistema de arquivos
6. Carrega configurações de sites
7. Cria instância do motor de scraping
8. Marca como inicializada

```python
def initialize(self) -> None:
    if self._initialized:
        return
    
    logger.info("Initializing Web Scraper AI Application...")
    
    # Load configurations
    self._load_system_config()
    
    # Initialize AI components
    self._init_ai_components()
    
    # Initialize file manager
    self.file_manager = FileManager()
    
    # Load site configurations
    self._load_site_configs()
    
    # Initialize scraper engine
    max_workers = self.application_config.get('engine', {}).get('max_workers', 3)
    self.engine = ScraperEngine(max_workers=max_workers)
    
    self._initialized = True
    logger.info("✅ Application initialized successfully!")
```

#### `start() -> None`
**Propósito**: Inicia os serviços da aplicação.

**Funcionalidade**:
- Valida inicialização
- Inicia motor de scraping
- Configura monitoramento
- Marca como executando

### **2. Gerenciamento de Configuração**

#### `_load_system_config() -> None`
**Propósito**: Carrega configurações do sistema.

**Configurações Carregadas**:
- Configurações de AI (OpenAI, navegação)
- Configurações do motor (workers, timeouts)
- Configurações de arquivo (paths, backup)
- Configurações de logging

#### `add_site_config(site_config: SiteConfig) -> None`
**Propósito**: Adiciona nova configuração de site.

**Validações**:
- Verifica se configuração é válida
- Evita duplicatas
- Valida URLs e seletores

### **3. Gerenciamento de Tarefas**

#### `create_scraping_task(site_name: str, priority: TaskPriority = TaskPriority.NORMAL) -> ScrapingTask`
**Propósito**: Cria nova tarefa de scraping.

**Processo**:
1. Valida se site existe nas configurações
2. Cria instância de `ScrapingTask`
3. Adiciona à fila do motor
4. Retorna tarefa criada

**Exemplo de Uso**:
```python
task = app.create_scraping_task('example_site', TaskPriority.HIGH)
logger.info(f"Task created: {task.task_id}")
```

### **4. Monitoramento e Status**

#### `get_application_status() -> Dict[str, Any]`
**Propósito**: Retorna status completo da aplicação.

**Informações Retornadas**:
```python
{
    "initialized": bool,
    "running": bool,
    "site_configs_loaded": int,
    "engine_status": {
        "status": str,
        "active_tasks": int,
        "queue_size": int,
        "completed_tasks": int
    },
    "components": {
        "file_manager": bool,
        "ai_client": bool,
        "navigator": bool,
        "pdf_processor": bool
    }
}
```

#### `health_check() -> Dict[str, Any]`
**Propósito**: Realiza verificação de saúde de todos os componentes.

**Verificações**:
- Status dos componentes core
- Conectividade AI
- Disponibilidade de recursos
- Estado do sistema de arquivos

#### `get_metrics() -> Dict[str, Any]`
**Propósito**: Coleta métricas de performance.

**Métricas Coletadas**:
```python
{
    "engine": {
        "tasks_completed": int,
        "tasks_failed": int,
        "success_rate": float,
        "average_task_time": float,
        "uptime_seconds": float
    },
    "storage": {
        "total_files": int,
        "total_size": int
    }
}
```

### **5. Manutenção e Backup**

#### `cleanup_old_data() -> Dict[str, Any]`
**Propósito**: Realiza limpeza de dados antigos.

**Operações**:
- Remove arquivos temporários
- Arquiva dados antigos
- Remove tarefas completadas da memória
- Otimiza storage

#### `create_backup(description: str = "") -> Dict[str, Any]`
**Propósito**: Cria backup do sistema.

**Processo**:
1. Compacta dados importantes
2. Inclui configurações
3. Salva metadados do backup
4. Retorna informações do backup

### **6. Finalização**

#### `stop() -> None`
**Propósito**: Para a aplicação graciosamente.

**Processo**:
1. Para motor de scraping
2. Finaliza tarefas ativas
3. Salva estado atual
4. Limpa recursos
5. Marca como parada

## Componentes Gerenciados

### **1. FileManager**
```python
self.file_manager = FileManager()
```
**Responsabilidade**: Gerenciamento de arquivos, backup e organização.

### **2. ScraperEngine**
```python
self.engine = ScraperEngine(max_workers=max_workers)
```
**Responsabilidade**: Execução multi-threaded de tarefas de scraping.

### **3. AI Components**
```python
self.ai_client = OpenAIClient()
self.navigator = NavigatorAgent(self.ai_client)
self.pdf_processor = PDFProcessorAgent(self.ai_client)
```
**Responsabilidade**: Integração com serviços de IA.

### **4. Site Configurations**
```python
self.site_configs: Dict[str, SiteConfig] = {}
```
**Responsabilidade**: Armazena configurações de sites para scraping.

## Tratamento de Erros

### **Inicialização**
```python
try:
    self._init_ai_components()
except Exception as e:
    logger.warning(f"AI components initialization failed: {e}")
    # Application continues without AI features
```

### **Operações Críticas**
```python
def create_scraping_task(self, site_name: str, priority: TaskPriority = TaskPriority.NORMAL) -> ScrapingTask:
    if not self._initialized:
        raise ApplicationNotInitializedError("Application must be initialized before creating tasks")
    
    if site_name not in self.site_configs:
        raise SiteConfigNotFoundError(f"Site configuration '{site_name}' not found")
```

## Configuração

### **Configurações de AI**
```python
ai_config = {
    'enable_openai': True,
    'enable_navigator': True,
    'enable_pdf_processor': True,
    'openai_api_key': os.getenv('OPENAI_API_KEY')
}
```

### **Configurações do Motor**
```python
engine_config = {
    'max_workers': 3,
    'task_timeout': 300,
    'retry_attempts': 3
}
```

## Padrões de Design Utilizados

### **1. Singleton**
- Garante instância única da aplicação
- Evita conflitos de estado

### **2. Facade**
- Fornece interface simplificada para sistema complexo
- Esconde complexidade interna

### **3. Dependency Injection**
- Componentes são injetados na inicialização
- Facilita testes e manutenção

## Exemplos de Uso

### **Inicialização Básica**
```python
from src.core.application import app

# Initialize application
app.initialize()
app.start()

# Check status
status = app.get_application_status()
print(f"App running: {status['running']}")
```

### **Criação de Tarefa**
```python
# Add site configuration
site_config = SiteConfig(name="example", base_url="https://example.com")
app.add_site_config(site_config)

# Create scraping task
task = app.create_scraping_task("example", TaskPriority.HIGH)
print(f"Task created: {task.task_id}")
```

### **Monitoramento**
```python
# Health check
health = app.health_check()
print(f"System health: {health['status']}")

# Metrics
metrics = app.get_metrics()
print(f"Success rate: {metrics['engine']['success_rate']:.2%}")
```

## Integração com Outros Componentes

### **CLI Interface**
```python
# cli_interface.py
from src.core.application import app

app.initialize()
app.start()
```

### **Interactive Mode**
```python
# interactive_mode.py
def __init__(self, app: WebScraperApplication):
    self.app = app
```

### **Site Modules**
```python
# base_site_module.py
def execute(self, app: WebScraperApplication) -> DownloadResult:
    # Access to all app resources
    scraper = app.create_scraper()
    ai_navigator = app.navigator
```

## Logs e Debugging

### **Logging Estruturado**
```python
logger.info("Application started", extra={
    "component": "application",
    "workers": max_workers,
    "ai_enabled": bool(self.ai_client)
})
```

### **Debug Information**
```python
def _debug_status(self) -> None:
    logger.debug(f"Site configs: {len(self.site_configs)}")
    logger.debug(f"Engine status: {self.engine.status if self.engine else 'None'}")
    logger.debug(f"AI components: {bool(self.ai_client)}")
```

---

**A classe WebScraperApplication é fundamental para o funcionamento do sistema, fornecendo coordenação centralizada e interface unificada para todos os componentes.**