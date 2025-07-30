# Web Scraper AI - Documentação Completa

## Visão Geral

O Web Scraper AI é um sistema avançado de web scraping que integra Inteligência Artificial para automação inteligente de extração de dados. O sistema foi desenvolvido seguindo princípios de programação orientada a objetos e arquitetura modular.

## Estrutura da Documentação

### 📁 [Arquitetura](./architecture.md)
Documentação completa da arquitetura do sistema, padrões de design e organização geral.

### 📁 [Core Components](./core/)
- **[Application](./core/application.md)** - Orquestração central da aplicação
- **[Scraper Engine](./core/scraper_engine.md)** - Motor de execução multi-threaded
- **[File Manager](./core/file_manager.md)** - Gerenciamento de arquivos e backups

### 📁 [AI Components](./ai/)
- **[OpenAI Client](./ai/openai_client.md)** - Integração com APIs de IA
- **[Navigator Agent](./ai/navigator_agent.md)** - Agente de navegação inteligente
- **[PDF Processor Agent](./ai/pdf_processor_agent.md)** - Processamento inteligente de PDFs

### 📁 [Scraping Components](./scraping/)
- **[Base Scraper](./scraping/base_scraper.md)** - Classe base para scrapers
- **[Selenium Scraper](./scraping/selenium_scraper.md)** - Implementação com Selenium WebDriver
- **[Web Utilities](./scraping/web_utilities.md)** - Utilitários para web scraping

### 📁 [Processing Components](./processing/)
- **[Base Processor](./processing/base_processor.md)** - Classe base para processadores
- **[CSV Processor](./processing/csv_processor.md)** - Processamento de arquivos CSV
- **[PDF Processor](./processing/pdf_processor.md)** - Processamento de arquivos PDF
- **[Excel Processor](./processing/excel_processor.md)** - Processamento de arquivos Excel

### 📁 [Module System](./modules/)
- **[Base Site Module](./modules/base_site_module.md)** - Template Method pattern
- **[Site Factory](./modules/site_factory.md)** - Factory pattern para módulos
- **[Generic Module](./modules/generic_module.md)** - Módulo genérico
- **[Example Module](./modules/example_module.md)** - Módulo de exemplo

### 📁 [User Interface](./ui/)
- **[CLI Interface](./ui/cli_interface.md)** - Interface de linha de comando
- **[Interactive Mode](./ui/interactive_mode.md)** - Modo interativo
- **[Daemon Mode](./ui/daemon_mode.md)** - Modo daemon

### 📁 [Data Models](./models/)
- **[Site Config](./models/site_config.md)** - Configuração de sites
- **[Scraping Task](./models/scraping_task.md)** - Modelo de tarefas
- **[Download Result](./models/download_result.md)** - Resultados de download

### 📁 [Utilities](./utils/)
- **[Logger](./utils/logger.md)** - Sistema de logging
- **[Settings](./utils/settings.md)** - Gerenciamento de configurações
- **[Exceptions](./utils/exceptions.md)** - Exceções customizadas

### 📁 [Examples](./examples/)
- **[Usage Guide](./usage.md)** - Guia de uso completo
- **[Configuration Examples](./examples/configurations.md)** - Exemplos de configuração
- **[API Examples](./examples/api_examples.md)** - Exemplos de uso da API

## Características Principais

- **🤖 Integração com IA**: Uso de OpenAI para navegação e processamento inteligente
- **🔄 Multi-threading**: Execução paralela de tarefas de scraping
- **🏗️ Arquitetura Modular**: Sistema de módulos plugáveis para sites específicos
- **📊 Processamento Multi-formato**: Suporte a CSV, PDF, Excel
- **🖥️ Interface Flexível**: Modos interativo e daemon
- **📁 Gerenciamento de Arquivos**: Sistema robusto de backup e organização
- **⚡ Alta Performance**: Otimizado para grandes volumes de dados
- **🛡️ Tratamento de Erros**: Sistema robusto de recuperação de falhas

## Começando

1. **Instalação**: Veja [requirements.txt](../requirements.txt)
2. **Configuração**: Configure [.env](../.env.example)
3. **Uso**: Execute `python main.py --help` para opções
4. **Exemplos**: Consulte [Usage Guide](./usage.md)

## Contribuição

Este projeto segue padrões rigorosos de:
- Programação Orientada a Objetos
- Padrões de Design (Template Method, Factory, Singleton)
- Documentação abrangente
- Tratamento robusto de erros
- Testes unitários

---

*Documentação gerada para Web Scraper AI v1.0*