# Arquitetura do Web Scraper AI

## Visão Geral da Arquitetura

O Web Scraper AI é construído usando uma arquitetura em camadas que segue princípios SOLID e padrões de design estabelecidos. O sistema é modular, extensível e mantém separação clara de responsabilidades.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                     │
├─────────────────────────────────────────────────────────────┤
│  CLI Interface  │  Interactive Mode  │    Daemon Mode       │
│  (Entry Point)  │  (User Commands)   │  (Background Tasks)  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────┤
│               WebScraperApplication                         │
│           (Central Orchestration)                           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     CORE LAYER                              │
├─────────────────────────────────────────────────────────────┤
│  Scraper Engine │  File Manager  │   Task Management        │
│  (Multi-thread) │  (Backup/Org)  │   (Queue/Status)         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                             │
├─────────────────────────────────────────────────────────────┤
│   AI Services   │  Scraping Svc  │  Processing Svc          │
│   (OpenAI/Nav)  │  (Selenium)    │  (CSV/PDF/Excel)         │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   MODULE LAYER                              │
├─────────────────────────────────────────────────────────────┤
│  Site Modules   │  Base Module   │  Site Factory            │
│  (Specific)     │  (Template)    │  (Creation)              │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                               │
├─────────────────────────────────────────────────────────────┤
│  Data Models    │  Config Mgmt   │  File Storage            │
│  (Dataclasses)  │  (Settings)    │  (Local/Backup)          │
└─────────────────────────────────────────────────────────────┘
```

## Padrões de Design Implementados

### 1. **Singleton Pattern**
- **Logger**: `src/utils/logger.py`
- **Settings**: `src/utils/settings.py`
- **Application**: `src/core/application.py`

**Justificativa**: Garante instância única para recursos compartilhados globalmente.

### 2. **Template Method Pattern**
- **Base Site Module**: `src/modules/base_site_module.py`

**Justificativa**: Define algoritmo de scraping com passos customizáveis por site.

### 3. **Factory Pattern**
- **Site Factory**: `src/modules/site_factory.py`

**Justificativa**: Criação dinâmica de módulos de site baseada em configuração.

### 4. **Strategy Pattern**
- **Processors**: `src/processing/`
- **Scrapers**: `src/scraping/`

**Justificativa**: Algoritmos intercambiáveis para diferentes tipos de processamento.

### 5. **Observer Pattern**
- **Task Status**: Sistema de notificação de status de tarefas

**Justificativa**: Desacoplamento entre execução e monitoramento de tarefas.

## Fluxo de Dados

### 1. **Inicialização**
```python
main.py → CLI Interface → Application → Core Components
```

### 2. **Criação de Tarefa**
```python
User Input → Site Config → Scraping Task → Task Queue
```

### 3. **Execução de Scraping**
```python
Task Queue → Scraper Engine → Site Module → Selenium Scraper → AI Navigator
```

### 4. **Processamento de Dados**
```python
Raw Data → Processor (CSV/PDF/Excel) → AI Processing → File Storage
```

### 5. **Gerenciamento de Arquivos**
```python
File Storage → File Manager → Backup System → Archive
```

## Componentes Principais

### **User Interface Layer**
Responsável pela interação com o usuário:
- **CLI Interface**: Parsing de argumentos e inicialização
- **Interactive Mode**: Interface de comandos interativa
- **Daemon Mode**: Execução em background

### **Application Layer**
Orquestração central do sistema:
- **WebScraperApplication**: Coordena todos os componentes
- Gerenciamento de estado global
- Configuração e inicialização de serviços

### **Core Layer**
Motor de execução e gerenciamento:
- **Scraper Engine**: Execução multi-threaded de tarefas
- **File Manager**: Organização e backup de arquivos
- **Task Management**: Fila e status de tarefas

### **Service Layer**
Serviços especializados:
- **AI Services**: Integração com OpenAI e agentes inteligentes
- **Scraping Services**: Selenium WebDriver e utilitários web
- **Processing Services**: Processamento de diferentes formatos

### **Module Layer**
Sistema de módulos plugáveis:
- **Site Modules**: Implementações específicas por site
- **Base Module**: Template para novos módulos
- **Site Factory**: Criação dinâmica de módulos

### **Data Layer**
Modelos e persistência:
- **Data Models**: Dataclasses para estruturas de dados
- **Configuration**: Gerenciamento de configurações
- **Storage**: Sistema de arquivos local e backup

## Princípios Arquiteturais

### **1. Separação de Responsabilidades**
Cada camada tem responsabilidade bem definida:
- UI: Interação com usuário
- Application: Orquestração
- Core: Execução
- Service: Funcionalidades específicas
- Module: Extensibilidade
- Data: Persistência

### **2. Inversão de Dependência**
Camadas superiores dependem de abstrações, não implementações:
```python
# Interface abstrata
class BaseScraper(ABC)
    
# Implementação concreta
class SeleniumScraper(BaseScraper)
```

### **3. Open/Closed Principle**
Sistema aberto para extensão, fechado para modificação:
- Novos sites: Criar novo módulo
- Novos formatos: Criar novo processor
- Novos scrapers: Implementar interface base

### **4. Single Responsibility Principle**
Cada classe tem uma única responsabilidade:
- `Logger`: Apenas logging
- `FileManager`: Apenas gerenciamento de arquivos
- `ScraperEngine`: Apenas execução de tarefas

## Fluxo de Controle

### **Inicialização do Sistema**
1. `main.py` chama `cli.run()`
2. `CLIInterface` parseia argumentos
3. `CLIInterface` configura `WebScraperApplication`
4. `Application` inicializa componentes core
5. `Application` carrega configurações de sites
6. Sistema entra no modo selecionado (interativo/daemon)

### **Execução de Tarefa de Scraping**
1. Usuário cria tarefa via UI
2. `Application` valida configuração do site
3. `ScraperEngine` adiciona tarefa à fila
4. Worker thread pega tarefa da fila
5. `SiteModule` executa lógica específica do site
6. `SeleniumScraper` realiza navegação
7. `AINavigator` auxilia em navegação complexa
8. Dados extraídos são processados
9. `FileManager` organiza e salva resultados
10. Status é atualizado e notificado

### **Processamento de Dados**
1. Dados brutos são recebidos do scraper
2. `ProcessorFactory` seleciona processor apropriado
3. Processor específico (CSV/PDF/Excel) processa dados
4. `AIPDFProcessor` pode ser usado para análise inteligente
5. Dados processados são salvos em formato estruturado
6. Metadados são atualizados

## Configuração e Extensibilidade

### **Adicionando Novo Site**
1. Criar classe herdando de `BaseSiteModule`
2. Implementar métodos abstratos
3. Registrar no `SiteFactory`
4. Criar configuração JSON do site

### **Adicionando Novo Formato**
1. Criar classe herdando de `BaseProcessor`
2. Implementar métodos de processamento
3. Registrar no sistema de processadores
4. Adicionar suporte no `FileManager`

### **Configuração de AI**
1. Configurar chaves de API no `.env`
2. Ajustar parâmetros dos agentes
3. Customizar prompts conforme necessário

## Monitoramento e Observabilidade

### **Logging**
- Logging estruturado em múltiplos níveis
- Rotação automática de logs
- Correlation IDs para rastreamento

### **Métricas**
- Métricas de performance do engine
- Estatísticas de sucesso/falha
- Tempo de execução de tarefas

### **Health Checks**
- Verificação de componentes
- Status de conectividade
- Disponibilidade de recursos

## Considerações de Performance

### **Multi-threading**
- Pool de workers configurável
- Balanceamento de carga automático
- Prevenção de resource contention

### **Memory Management**
- Cleanup automático de tarefas antigas
- Gestão eficiente de recursos Selenium
- Garbage collection otimizado

### **File I/O**
- Operações assíncronas quando possível
- Compressão de backups
- Cleanup automático de arquivos temporários

## Segurança

### **Credential Management**
- Variáveis de ambiente para secrets
- Não exposição de chaves em logs
- Validação de entrada de usuário

### **Web Scraping Ethics**
- Respeito a robots.txt
- Rate limiting configurável
- User-agent apropriado

---

*Esta arquitetura garante escalabilidade, manutenibilidade e extensibilidade do sistema Web Scraper AI.*