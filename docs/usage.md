# Guia de Uso - Web Scraper AI

## Introdução

Este guia completo demonstra como usar o Web Scraper AI, desde instalação até casos de uso avançados.

## Instalação e Configuração

### 1. Requisitos do Sistema
```bash
# Python 3.8+
python --version

# Chrome/Chromium browser
google-chrome --version
```

### 2. Instalação de Dependências
```bash
# Instalar dependências
pip install -r requirements.txt

# Verificar instalação
python -c "import selenium, openai, pandas; print('Dependencies OK')"
```

### 3. Configuração de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

**Configurações obrigatórias no .env:**
```env
# OpenAI API (para recursos de IA)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Chrome Driver (deixe vazio para auto-download)
CHROME_DRIVER_PATH=

# Configurações de logging
LOG_LEVEL=INFO
LOG_FILE=logs/application.log

# Configurações de performance
MAX_WORKERS=3
DEFAULT_TIMEOUT=30
```

## Uso Básico

### 1. Executando a Aplicação

#### Modo Interativo (Recomendado para iniciantes)
```bash
# Iniciar no modo interativo
python main.py

# Com configurações específicas
python main.py --mode interactive --workers 5 --log-level DEBUG
```

#### Modo Daemon (Para execução contínua)
```bash
# Executar em background
python main.py --mode daemon

# Com configurações
python main.py --mode daemon --workers 10 --log-level INFO
```

### 2. Interface Interativa

Quando executado no modo interativo, você verá um menu como este:

```
🤖 Web Scraper AI - Interactive Mode
==================================================
Welcome to the interactive command interface!
Type 'help' or '?' for available commands.
==================================================

📋 Available Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. status     - Show application status
2. health     - Show health check
3. metrics    - Show performance metrics
4. create-task - Create a scraping task
5. list-tasks - List all tasks
6. cleanup    - Run maintenance cleanup
7. backup     - Create system backup
8. exit       - Exit application
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Enter command:
```

### 3. Comandos Principais

#### Status da Aplicação
```bash
# Comando: status ou 1
📊 Application Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 Initialized: ✅ Yes
▶️  Running: ✅ Yes
🌐 Site Configs: 2
⚙️  Engine Status: RUNNING
🔄 Active Tasks: 1
📦 Queue Size: 3
✅ Completed Tasks: 15
```

#### Verificação de Saúde
```bash
# Comando: health ou 2
🏥 Health Check Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Overall Status: HEALTHY
🕐 Checked at: 2024-01-15 14:30:00

🔧 Component Health:
  ✅ File Manager: operational
  ✅ Ai Client: connected
  ✅ Navigator: ready
  ✅ Pdf Processor: available
```

#### Métricas de Performance
```bash
# Comando: metrics ou 3
📈 Performance Metrics:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Tasks Completed: 45
❌ Tasks Failed: 2
📊 Success Rate: 95.74%
⏱️  Average Time: 12.50s
🕐 Uptime: 3600s

💾 Storage:
📁 Total Files: 156
💿 Total Size: 45.67 MB
```

## Configuração de Sites

### 1. Estrutura de Configuração

Crie um arquivo JSON na pasta `config/sites/` para cada site:

```json
{
  "name": "example_news_site",
  "base_url": "https://example-news.com",
  "description": "Example news website scraping",
  "extraction_rules": [
    {
      "name": "title",
      "selector": {
        "type": "css",
        "value": "h1.article-title",
        "wait_condition": "presence"
      },
      "data_type": "text",
      "required": true
    },
    {
      "name": "content",
      "selector": {
        "type": "css",
        "value": ".article-content p",
        "wait_condition": "presence"
      },
      "data_type": "text",
      "required": true
    },
    {
      "name": "author",
      "selector": {
        "type": "css",
        "value": ".author-name",
        "wait_condition": "presence"
      },
      "data_type": "text",
      "required": false,
      "default_value": "Unknown Author"
    },
    {
      "name": "publish_date",
      "selector": {
        "type": "css",
        "value": "time[datetime]",
        "wait_condition": "presence",
        "attribute": "datetime"
      },
      "data_type": "datetime",
      "required": false
    }
  ],
  "navigation": {
    "start_urls": [
      "https://example-news.com/latest",
      "https://example-news.com/tech"
    ],
    "pagination": {
      "next_button_selector": ".pagination .next",
      "max_pages": 10
    }
  },
  "scraping_config": {
    "wait_time": 3.0,
    "timeout": 30.0,
    "retry_attempts": 3,
    "use_ai_navigation": true,
    "respect_robots_txt": true
  }
}
```

### 2. Tipos de Seletores

#### CSS Selectors
```json
{
  "name": "title",
  "selector": {
    "type": "css",
    "value": "h1.main-title",
    "wait_condition": "clickable"
  }
}
```

#### XPath Selectors
```json
{
  "name": "price",
  "selector": {
    "type": "xpath",
    "value": "//span[@class='price'][1]/text()",
    "wait_condition": "presence"
  }
}
```

#### AI-Powered Selectors
```json
{
  "name": "product_description",
  "selector": {
    "type": "ai",
    "description": "Find the main product description text",
    "fallback_selector": ".description, .product-info p"
  }
}
```

## Casos de Uso Avançados

### 1. E-commerce Scraping

#### Configuração para Site de E-commerce
```json
{
  "name": "ecommerce_products",
  "base_url": "https://shop.example.com",
  "extraction_rules": [
    {
      "name": "product_name",
      "selector": {"type": "css", "value": "h1.product-title"},
      "data_type": "text",
      "required": true
    },
    {
      "name": "price",
      "selector": {"type": "css", "value": ".price-current"},
      "data_type": "decimal",
      "required": true,
      "transform": "extract_numbers"
    },
    {
      "name": "availability",
      "selector": {"type": "css", "value": ".stock-status"},
      "data_type": "text",
      "required": false
    },
    {
      "name": "images",
      "selector": {"type": "css", "value": ".product-images img"},
      "data_type": "list",
      "attribute": "src",
      "required": false
    },
    {
      "name": "specifications",
      "selector": {"type": "ai", "description": "Extract product specifications table"},
      "data_type": "structured",
      "required": false
    }
  ],
  "navigation": {
    "start_urls": ["https://shop.example.com/products"],
    "follow_links": {
      "selector": ".product-link",
      "max_depth": 2
    }
  }
}
```

#### Script de Automação
```python
#!/usr/bin/env python3
"""
Script para scraping automatizado de e-commerce
"""

from src.core.application import app
from src.models.scraping_task import TaskPriority
import time

def scrape_ecommerce_daily():
    """Executa scraping diário de produtos"""
    
    # Initialize application
    app.initialize()
    app.start()
    
    try:
        # Create scraping task
        task = app.create_scraping_task(
            site_name='ecommerce_products',
            priority=TaskPriority.HIGH
        )
        
        print(f"✅ Task created: {task.task_id}")
        
        # Monitor progress
        while True:
            status = app.get_application_status()
            active_tasks = status.get('engine_status', {}).get('active_tasks', 0)
            
            if active_tasks == 0:
                print("✅ Scraping completed!")
                break
                
            print(f"🔄 Active tasks: {active_tasks}")
            time.sleep(30)
        
        # Get metrics
        metrics = app.get_metrics()
        print(f"📊 Success rate: {metrics['engine']['success_rate']:.2%}")
        
    finally:
        app.stop()

if __name__ == "__main__":
    scrape_ecommerce_daily()
```

### 2. News Monitoring

#### Configuração para Monitoramento de Notícias
```json
{
  "name": "news_monitor",
  "base_url": "https://news.example.com",
  "extraction_rules": [
    {
      "name": "headline",
      "selector": {"type": "css", "value": "h2.headline"},
      "data_type": "text",
      "required": true
    },
    {
      "name": "summary",
      "selector": {"type": "ai", "description": "Extract article summary or first paragraph"},
      "data_type": "text",
      "required": true
    },
    {
      "name": "sentiment",
      "selector": {"type": "ai", "description": "Analyze article sentiment"},
      "data_type": "structured",
      "ai_analysis": "sentiment"
    },
    {
      "name": "keywords",
      "selector": {"type": "ai", "description": "Extract key topics and entities"},
      "data_type": "list",
      "ai_analysis": "keywords"
    }
  ],
  "scheduling": {
    "frequency": "hourly",
    "max_articles_per_run": 50
  }
}
```

### 3. Document Processing

#### Processamento de PDFs
```python
from src.ai.pdf_processor_agent import PDFProcessorAgent
from src.ai.openai_client import OpenAIClient

# Initialize PDF processor
client = OpenAIClient()
pdf_processor = PDFProcessorAgent(client)

# Process financial report
result = pdf_processor.process_pdf_file(
    "quarterly_report.pdf", 
    analysis_type="financial"
)

# Extract key financial metrics
financial_data = pdf_processor.extract_structured_data(
    "quarterly_report.pdf",
    target_fields=[
        "total_revenue", 
        "net_profit", 
        "cash_flow",
        "total_assets",
        "debt_ratio"
    ]
)

print("📊 Financial Metrics:")
for field, value in financial_data['extracted_data'].items():
    confidence = financial_data['confidence_scores'][field]
    print(f"  {field}: {value} (confidence: {confidence:.2%})")
```

## Monitoramento e Maintenance

### 1. Logs e Debugging

#### Estrutura de Logs
```
logs/
├── application.log          # Log principal
├── scraping/
│   ├── 2024-01-15/         # Logs por data
│   │   ├── tasks.log       # Log de tarefas
│   │   └── errors.log      # Log de erros
│   └── archive/            # Logs arquivados
├── ai/
│   ├── openai_usage.log    # Uso da API OpenAI
│   └── ai_analysis.log     # Análises de IA
└── performance/
    ├── metrics.log         # Métricas de performance
    └── system.log          # Métricas do sistema
```

#### Configuração de Log Level
```bash
# Debug (muito detalhado)
python main.py --log-level DEBUG

# Info (padrão)
python main.py --log-level INFO

# Warning (apenas avisos e erros)
python main.py --log-level WARNING

# Error (apenas erros)
python main.py --log-level ERROR
```

### 2. Backup e Recovery

#### Backup Manual
```bash
# Comando: backup ou 7
💾 Creating System Backup...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Backup Created Successfully!
🆔 Backup ID: backup_2024-01-15_14-30-00
📁 Files: 1,245
💿 Size: 156.78 MB
📅 Created: 2024-01-15 14:30:00
```

#### Backup Automático
```python
import schedule
import time
from src.core.application import app

def automated_backup():
    """Backup automático diário"""
    try:
        backup_info = app.create_backup("Automated daily backup")
        print(f"✅ Backup created: {backup_info['backup_id']}")
        
        # Cleanup old backups (manter apenas 7)
        cleanup_result = app.file_manager.cleanup_old_backups(keep_count=7)
        print(f"🧹 Cleaned up {cleanup_result['removed_backups']} old backups")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")

# Agendar backup diário às 2:00 AM
schedule.every().day.at("02:00").do(automated_backup)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. Cleanup e Manutenção

#### Limpeza Manual
```bash
# Comando: cleanup ou 6
🧹 Running Maintenance Cleanup...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Cleanup Completed Successfully!
🗑️  Temp Files: 45 files deleted
💾 Space Freed: 23.45 MB
📦 Archived: 12 files
🗂️  Old Tasks: 156 removed from memory
```

#### Limpeza Automática
```python
from src.core.application import app
import threading
import time

def periodic_cleanup():
    """Limpeza automática a cada 6 horas"""
    while True:
        try:
            # Wait 6 hours
            time.sleep(6 * 3600)
            
            # Run cleanup
            cleanup_result = app.cleanup_old_data()
            print(f"🧹 Auto cleanup: {cleanup_result}")
            
        except Exception as e:
            print(f"❌ Auto cleanup failed: {e}")

# Start cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()
```

## Troubleshooting

### 1. Problemas Comuns

#### WebDriver Issues
```bash
# Error: ChromeDriver not found
# Solution: Install or update Chrome
sudo apt-get update
sudo apt-get install google-chrome-stable

# Or download ChromeDriver manually
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
```

#### OpenAI API Issues
```python
# Test OpenAI connection
from src.ai.openai_client import OpenAIClient

try:
    client = OpenAIClient()
    response = client.generate_completion("Test connection", max_tokens=10)
    print("✅ OpenAI connection OK")
except Exception as e:
    print(f"❌ OpenAI error: {e}")
```

#### Memory Issues
```bash
# Monitor memory usage
python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"

# Reduce workers if needed
python main.py --workers 1
```

### 2. Performance Optimization

#### Configurações Recomendadas

**Para máquina de desenvolvimento:**
```env
MAX_WORKERS=2
DEFAULT_TIMEOUT=30
LOG_LEVEL=INFO
```

**Para servidor de produção:**
```env
MAX_WORKERS=8
DEFAULT_TIMEOUT=60
LOG_LEVEL=WARNING
```

**Para recursos limitados:**
```env
MAX_WORKERS=1
DEFAULT_TIMEOUT=45
LOG_LEVEL=ERROR
```

## Integrações

### 1. Integração com Databases

```python
import sqlite3
from src.core.application import app

def save_to_database(scraping_result):
    """Salva resultados no banco de dados"""
    
    conn = sqlite3.connect('scraping_data.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraped_data (
            id INTEGER PRIMARY KEY,
            site_name TEXT,
            url TEXT,
            title TEXT,
            content TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert data
    cursor.execute('''
        INSERT INTO scraped_data (site_name, url, title, content)
        VALUES (?, ?, ?, ?)
    ''', (
        scraping_result['site_name'],
        scraping_result['url'],
        scraping_result['data'].get('title'),
        scraping_result['data'].get('content')
    ))
    
    conn.commit()
    conn.close()
```

### 2. Integração com APIs

```python
import requests
from src.core.application import app

def send_to_webhook(data):
    """Envia dados para webhook externo"""
    
    webhook_url = "https://your-api.com/webhook"
    
    payload = {
        'source': 'web_scraper_ai',
        'timestamp': data['scraped_at'],
        'data': data['extracted_data']
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print(f"✅ Data sent to webhook: {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook failed: {e}")
```

---

**Este guia fornece uma base sólida para usar o Web Scraper AI eficientemente. Para casos de uso específicos, consulte a documentação técnica detalhada de cada componente.**