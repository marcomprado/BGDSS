# ScraperEngine - Motor de Execução Multi-threaded

## Visão Geral

O `ScraperEngine` é o motor de execução responsável pelo processamento paralelo de tarefas de scraping. Implementa um sistema robusto de filas, workers e gerenciamento de estado para maximizar a eficiência e confiabilidade.

**Localização**: `src/core/scraper_engine.py`

## Funcionalidade Principal

### **Responsabilidades**
- 🔄 **Execução Paralela**: Processa múltiplas tarefas simultaneamente
- 📋 **Gerenciamento de Fila**: Controla ordem e prioridade de execução
- 👷 **Pool de Workers**: Gerencia threads de trabalho
- 📊 **Monitoramento**: Rastreia status e métricas de performance
- 🛡️ **Recuperação de Erros**: Retry automático e tratamento de falhas

## Arquitetura da Classe

```python
class ScraperEngine:
    """
    Motor de execução multi-threaded para tarefas de scraping.
    
    Gerencia fila de tarefas, pool de workers e execução paralela.
    Fornece monitoramento e recuperação automática de falhas.
    """
```

### **Componentes Principais**
```python
def __init__(self, max_workers: int = 3):
    self.max_workers = max_workers
    self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
    self.active_tasks: Dict[str, ScrapingTask] = {}
    self.completed_tasks: Dict[str, ScrapingTask] = {}
    self.failed_tasks: Dict[str, ScrapingTask] = {}
    self.executor: Optional[ThreadPoolExecutor] = None
    self._running = False
    self._lock = threading.Lock()
    self.metrics = EngineMetrics()
```

## Métodos Principais

### **1. Controle de Execução**

#### `start() -> None`
**Propósito**: Inicia o motor de execução.

**Processo**:
1. Valida se não está já executando
2. Cria ThreadPoolExecutor
3. Inicia worker threads
4. Marca como executando
5. Inicia coleta de métricas

```python
def start(self) -> None:
    if self._running:
        logger.warning("Engine is already running")
        return
    
    logger.info(f"Starting scraper engine with {self.max_workers} workers...")
    
    self.executor = ThreadPoolExecutor(
        max_workers=self.max_workers,
        thread_name_prefix="scraper-worker"
    )
    
    self._running = True
    self.metrics.start_time = time.time()
    
    # Start worker threads
    for i in range(self.max_workers):
        self.executor.submit(self._worker_loop)
    
    logger.info("✅ Scraper engine started successfully!")
```

#### `stop() -> None`
**Propósito**: Para o motor graciosamente.

**Processo**:
1. Marca como não executando
2. Finaliza tarefas ativas
3. Shutdown do ThreadPoolExecutor
4. Salva métricas finais

#### `_worker_loop() -> None`
**Propósito**: Loop principal dos workers.

**Funcionamento**:
```python
def _worker_loop(self) -> None:
    worker_id = threading.current_thread().name
    logger.debug(f"Worker {worker_id} started")
    
    while self._running:
        try:
            # Get task from queue (timeout to check _running status)
            try:
                priority, task_id, task = self.task_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            # Execute task
            self._execute_task(task)
            
            # Mark task as done
            self.task_queue.task_done()
            
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}")
            time.sleep(1)  # Brief pause on error
    
    logger.debug(f"Worker {worker_id} stopped")
```

### **2. Gerenciamento de Tarefas**

#### `add_task(task: ScrapingTask) -> None`
**Propósito**: Adiciona tarefa à fila de execução.

**Processo**:
1. Valida se engine está executando
2. Adiciona à fila com prioridade
3. Atualiza contadores
4. Log da adição

```python
def add_task(self, task: ScrapingTask) -> None:
    if not self._running:
        raise EngineNotRunningError("Engine must be started before adding tasks")
    
    # Priority queue uses tuple (priority, task_id, task)
    # Lower numbers = higher priority
    priority_value = task.priority.value
    
    with self._lock:
        self.task_queue.put((priority_value, task.task_id, task))
        task.status = TaskStatus.QUEUED
        task.queued_at = datetime.now()
    
    logger.info(f"Task {task.task_id} added to queue (priority: {task.priority.name})")
```

#### `_execute_task(task: ScrapingTask) -> None`
**Propósito**: Executa uma tarefa específica.

**Processo Detalhado**:
```python
def _execute_task(self, task: ScrapingTask) -> None:
    task_start_time = time.time()
    worker_id = threading.current_thread().name
    
    try:
        # Move to active tasks
        with self._lock:
            self.active_tasks[task.task_id] = task
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
        
        logger.info(f"[{worker_id}] Starting task {task.task_id}")
        
        # Get site module
        site_module = self._get_site_module(task.site_config_name)
        
        # Execute scraping
        result = site_module.execute(task)
        
        # Handle successful completion
        self._handle_task_success(task, result, task_start_time)
        
    except Exception as e:
        # Handle task failure
        self._handle_task_failure(task, e, task_start_time)
    
    finally:
        # Remove from active tasks
        with self._lock:
            self.active_tasks.pop(task.task_id, None)
```

### **3. Tratamento de Resultados**

#### `_handle_task_success(task: ScrapingTask, result: DownloadResult, start_time: float) -> None`
**Propósito**: Processa conclusão bem-sucedida de tarefa.

**Ações**:
1. Atualiza status da tarefa
2. Salva resultado
3. Move para tarefas completadas
4. Atualiza métricas
5. Log de sucesso

#### `_handle_task_failure(task: ScrapingTask, error: Exception, start_time: float) -> None`
**Propósito**: Processa falha de tarefa.

**Lógica de Retry**:
```python
def _handle_task_failure(self, task: ScrapingTask, error: Exception, start_time: float) -> None:
    task.error_message = str(error)
    task.retry_count += 1
    
    execution_time = time.time() - start_time
    
    if task.retry_count < task.max_retries:
        # Retry task
        logger.warning(f"Task {task.task_id} failed (attempt {task.retry_count}), retrying...")
        
        # Add back to queue with delay
        time.sleep(min(task.retry_count * 2, 30))  # Exponential backoff
        self.add_task(task)
        
    else:
        # Mark as failed
        with self._lock:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self.failed_tasks[task.task_id] = task
        
        self.metrics.record_failure(execution_time)
        logger.error(f"Task {task.task_id} failed permanently: {error}")
```

### **4. Monitoramento e Métricas**

#### `get_status() -> Dict[str, Any]`
**Propósito**: Retorna status atual do engine.

**Informações Retornadas**:
```python
{
    "status": "running" | "stopped",
    "active_tasks": int,
    "queue_size": int,
    "completed_tasks": int,
    "failed_tasks": int,
    "workers": int,
    "uptime_seconds": float
}
```

#### `get_metrics() -> Dict[str, Any]`
**Propósito**: Coleta métricas detalhadas de performance.

**Métricas Coletadas**:
```python
{
    "tasks_completed": int,
    "tasks_failed": int,
    "success_rate": float,
    "average_task_time": float,
    "total_execution_time": float,
    "uptime_seconds": float,
    "workers_utilization": float
}
```

#### `get_active_tasks() -> Dict[str, ScrapingTask]`
**Propósito**: Retorna tarefas atualmente em execução.

#### `get_completed_tasks() -> Dict[str, ScrapingTask]`
**Propósito**: Retorna tarefas completadas.

### **5. Gerenciamento de Site Modules**

#### `_get_site_module(site_name: str) -> BaseSiteModule`
**Propósito**: Obtém módulo específico para um site.

**Processo**:
1. Verifica cache de módulos
2. Usa SiteFactory para criar módulo
3. Armazena em cache para reutilização
4. Retorna instância

```python
def _get_site_module(self, site_name: str) -> BaseSiteModule:
    if site_name not in self._module_cache:
        site_factory = SiteFactory()
        module = site_factory.create_module(site_name)
        self._module_cache[site_name] = module
    
    return self._module_cache[site_name]
```

## Sistema de Métricas

### **EngineMetrics Class**
```python
@dataclass
class EngineMetrics:
    start_time: float = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0
    task_times: List[float] = field(default_factory=list)
    
    def record_success(self, execution_time: float) -> None:
        self.tasks_completed += 1
        self.total_execution_time += execution_time
        self.task_times.append(execution_time)
    
    def record_failure(self, execution_time: float) -> None:
        self.tasks_failed += 1
        self.total_execution_time += execution_time
    
    @property
    def success_rate(self) -> float:
        total = self.tasks_completed + self.tasks_failed
        return self.tasks_completed / total if total > 0 else 0.0
    
    @property
    def average_task_time(self) -> float:
        return sum(self.task_times) / len(self.task_times) if self.task_times else 0.0
```

## Tratamento de Erros

### **Exceções Customizadas**
```python
class EngineNotRunningError(Exception):
    """Engine não está executando"""

class EngineAlreadyRunningError(Exception):
    """Engine já está executando"""

class TaskExecutionError(Exception):
    """Erro na execução de tarefa"""
```

### **Recuperação de Falhas**
- **Retry Automático**: Tarefas falham são automaticamente reexecutadas
- **Exponential Backoff**: Delay crescente entre tentativas
- **Circuit Breaker**: Para engine em caso de falhas críticas
- **Graceful Shutdown**: Finalização segura de tarefas ativas

## Configuração

### **Parâmetros do Engine**
```python
engine_config = {
    'max_workers': 3,           # Número de workers
    'task_timeout': 300,        # Timeout por tarefa (segundos)
    'retry_attempts': 3,        # Número de tentativas
    'queue_size_limit': 1000,   # Limite da fila
    'cleanup_interval': 3600    # Intervalo de limpeza (segundos)
}
```

### **Configuração de Performance**
```python
# Ajuste baseado em recursos disponíveis
workers = min(max_workers, cpu_count() * 2)
queue_size = workers * 10  # 10 tarefas por worker na fila
```

## Padrões de Design Utilizados

### **1. Producer-Consumer**
- Fila de tarefas como buffer
- Workers como consumers
- Application como producer

### **2. Thread Pool**
- Reutilização de threads
- Controle de recursos
- Balanceamento de carga

### **3. State Machine**
- Estados bem definidos para tarefas
- Transições controladas
- Rastreamento de progresso

## Exemplos de Uso

### **Inicialização e Uso Básico**
```python
from src.core.scraper_engine import ScraperEngine

# Create and start engine
engine = ScraperEngine(max_workers=5)
engine.start()

# Add tasks
for site in sites:
    task = create_scraping_task(site)
    engine.add_task(task)

# Monitor progress
while engine.get_status()['active_tasks'] > 0:
    status = engine.get_status()
    print(f"Active: {status['active_tasks']}, Queue: {status['queue_size']}")
    time.sleep(10)

# Stop engine
engine.stop()
```

### **Monitoramento Avançado**
```python
def monitor_engine(engine: ScraperEngine):
    while True:
        metrics = engine.get_metrics()
        print(f"Success Rate: {metrics['success_rate']:.2%}")
        print(f"Avg Task Time: {metrics['average_task_time']:.2f}s")
        
        status = engine.get_status()
        if status['status'] == 'stopped':
            break
        
        time.sleep(30)
```

### **Configuração Personalizada**
```python
# High-performance configuration
engine = ScraperEngine(max_workers=10)

# Low-resource configuration  
engine = ScraperEngine(max_workers=1)

# Configure task timeouts
for task in tasks:
    task.timeout = 60  # 1 minute timeout
    engine.add_task(task)
```

## Integração com Application

### **Inicialização via Application**
```python
# application.py
max_workers = self.application_config.get('engine', {}).get('max_workers', 3)
self.engine = ScraperEngine(max_workers=max_workers)
```

### **Acesso via UI**
```python
# interactive_mode.py
def show_status(self):
    if self.app.engine:
        status = self.app.engine.get_status()
        print(f"Engine Status: {status['status']}")
```

## Logs e Debugging

### **Logging Estruturado**
```python
logger.info("Task execution started", extra={
    "task_id": task.task_id,
    "worker": worker_id,
    "site": task.site_config_name,
    "priority": task.priority.name
})
```

### **Debug Mode**
```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"Queue size: {self.task_queue.qsize()}")
    logger.debug(f"Active tasks: {len(self.active_tasks)}")
    logger.debug(f"Worker utilization: {self._calculate_utilization():.2%}")
```

---

**O ScraperEngine é o coração da execução paralela, garantindo alta performance e confiabilidade no processamento de tarefas de scraping.**