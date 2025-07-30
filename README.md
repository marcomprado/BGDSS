# Web Scraper AI - Sites Governamentais Brasileiros

**Sistema especializado de web scraping para sites governamentais brasileiros com extração de dados real**

Um sistema focado e otimizado para extração automatizada de dados de sites governamentais brasileiros, implementando scraping real com HTTP requests e análise inteligente de conteúdo.

## 🎯 Características Principais

### 🏛️ **Sites Governamentais Suportados**
- **Portal Saude MG**: Download de PDFs (deliberações e resoluções)
- **MDS Parcelas Pagas**: Extração de dados de pagamentos municipais
- **MDS Saldo Detalhado**: Consulta de saldos detalhados por conta

### 🚀 **Scraping Real**
- **HTTP Requests**: Comunicação real com sites usando `requests` e `BeautifulSoup`
- **Download de Arquivos**: Download efetivo de PDFs, CSVs e outros documentos
- **Análise de Formulários**: Detecção e análise de interfaces governamentais
- **Tratamento de Autenticação**: Suporte para sistemas que requerem login

### 🧠 **Processamento Inteligente**
- **Detecção de Conteúdo**: Identificação automática de tipos de dados
- **Extração Estruturada**: Conversão de tabelas HTML para CSV
- **Validação de Arquivos**: Verificação de integridade de downloads
- **Relatórios de Status**: Análise detalhada de acessibilidade dos sites

### 📁 **Organização Automática**
- **Estrutura de Pastas**: Organização por site, ano, mês e município
- **Nomenclatura Padronizada**: Nomes de arquivos consistentes e descritivos
- **Logging Detalhado**: Rastreamento completo de todas as operações
- **Gerenciamento de Erros**: Fallbacks e recuperação automática

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- Conexão com internet estável

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/web_scraper_ai.git
cd web_scraper_ai
```

### 2. Instale dependências
```bash
pip install -r requirements.txt
```

### 3. Configure variáveis de ambiente (opcional)
```bash
cp .env.example .env
# Edite .env com sua chave OpenAI se desejar recursos de IA
```

### 4. Execute o sistema
```bash
python main.py
```

## 📋 Uso

### Interface Terminal
O sistema apresenta um menu interativo para seleção de sites:

```
========================================
    WEB SCRAPER AUTOMATIZADO - IA
========================================

Selecione o site para coleta de dados:

1. Portal Saude MG - Deliberacoes
2. MDS - Parcelas Pagas
3. MDS - Saldo Detalhado por Conta
4. Sair

Digite sua opcao (1-4):
```

### Exemplo: Portal Saude MG
1. Selecione a opção 1
2. Escolha o ano (ex: 2024)
3. Escolha o mês (ou "Todos os meses")
4. O sistema irá:
   - Acessar o site do Portal Saude MG
   - Localizar PDFs disponíveis
   - Fazer download dos documentos
   - Organizar em pastas por data

### Uso Programático
```python
from src.modules.sites.portal_saude_mg import PortalSaudeMGScraper

# Inicializar scraper
scraper = PortalSaudeMGScraper()

# Configurar parâmetros
config = {
    'year': 2024,
    'month': 1,  # Janeiro
    'url': 'https://portal-antigo.saude.mg.gov.br/deliberacoes/documents'
}

# Executar scraping
result = scraper.execute_scraping(config)

print(f"Arquivos baixados: {result['files_downloaded']}")
print(f"Tamanho total: {result['total_size_mb']:.2f} MB")
```

## 📊 Testes

### Teste Completo
Execute o teste abrangente de todos os scrapers:

```bash
python test_all_scrapers.py
```

### Resultados Esperados
- **Portal Saude MG**: ✅ Download de PDFs reais
- **MDS Parcelas**: ✅ Acesso ao sistema (requer autenticação para dados completos)
- **MDS Saldo**: ✅ Acesso ao sistema (requer autenticação para dados completos)

## 🏗️ Arquitetura

```
web_scraper_ai/
├── src/
│   ├── modules/sites/           # Scrapers específicos
│   │   ├── portal_saude_mg.py   # Portal Saude MG
│   │   ├── mds_parcelas.py      # MDS Parcelas Pagas
│   │   └── mds_saldo.py         # MDS Saldo Detalhado
│   ├── ui/
│   │   └── terminal.py  # Interface terminal
│   ├── ai/
│   │   ├── openai_client.py     # Cliente OpenAI (opcional)
│   │   └── navigator_agent.py   # Agente de navegação
│   └── utils/
│       ├── logger.py            # Sistema de logging
│       └── exceptions.py        # Exceções customizadas
├── config/
│   └── settings.py              # Configurações do sistema
├── downloads/                   # Arquivos baixados
│   ├── portal_saude_mg/         # PDFs do Portal Saude
│   ├── mds_parcelas_pagas/      # Dados MDS Parcelas
│   └── mds_saldo_detalhado/     # Dados MDS Saldo
├── logs/                        # Logs do sistema
└── main.py                      # Ponto de entrada
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente (.env)
```env
# Opcional - apenas para recursos de IA
OPENAI_API_KEY=sua_chave_openai_aqui

# Configurações de timeout
DOWNLOAD_TIMEOUT=30
DEFAULT_WAIT_TIME=10
MAX_RETRIES=3

# Nível de logging
LOG_LEVEL=INFO
```

### Configurações por Site
As configurações específicas de cada site são definidas nos módulos individuais:

- **Portal Saude MG**: `src/modules/sites/portal_saude_mg.py`
- **MDS Parcelas**: `src/modules/sites/mds_parcelas.py`
- **MDS Saldo**: `src/modules/sites/mds_saldo.py`

## 📈 Funcionalidades por Site

### Portal Saude MG
- ✅ **Acesso direto**: Sem necessidade de autenticação
- ✅ **Download real**: PDFs de deliberações e resoluções
- ✅ **Filtros**: Por ano e mês
- ✅ **Organização**: Estrutura de pastas automática

### MDS Parcelas Pagas
- ✅ **Acesso ao sistema**: Interface de consulta identificada
- 🔐 **Requer autenticação**: Para acesso completo aos dados
- ✅ **Análise de formulários**: Detecção de filtros disponíveis
- ✅ **Relatório de status**: Informações sobre acessibilidade

### MDS Saldo Detalhado
- ✅ **Acesso ao sistema**: Interface de saldo identificada
- 🔐 **Requer autenticação**: Para acesso completo aos dados
- ✅ **Detecção de conteúdo**: Identificação de dados de saldo
- ✅ **Relatório de status**: Informações sobre funcionalidades

## 🚨 Limitações e Considerações

### Sites Governamentais
- Alguns sites requerem **autenticação** para acesso completo aos dados
- **Rate limiting**: Respeita limites de requisições dos servidores
- **Disponibilidade**: Dependente da disponibilidade dos sites governamentais
- **Mudanças**: Sites podem alterar estrutura, necessitando atualizações

### Uso Ético
- ✅ **Dados públicos**: Acessa apenas informações públicas
- ✅ **Rate limiting**: Implementa delays entre requisições
- ✅ **Robots.txt**: Respeita diretrizes dos sites
- ✅ **Transparência**: Logs detalhados de todas as operações

## 🔍 Monitoramento

### Status do Sistema
```python
from src.modules.sites.portal_saude_mg import PortalSaudeMGScraper

scraper = PortalSaudeMGScraper()
status = scraper.get_site_status()

print(f"Site acessível: {status['accessible']}")
print(f"Tempo de resposta: {status['response_time_ms']:.0f}ms")
```

### Logs
```bash
# Ver logs em tempo real
tail -f logs/web_scraper_$(date +%Y%m%d).log

# Filtrar por site específico
grep "Portal Saude MG" logs/*.log
```

## 🛠️ Troubleshooting

### Problemas Comuns

1. **Sem arquivos baixados**
   - Verificar conectividade com internet
   - Confirmar se o site está acessível
   - Verificar logs para detalhes do erro

2. **Erro de dependências**
   ```bash
   pip install --upgrade requests beautifulsoup4 lxml
   ```

3. **Problemas de encoding**
   - Sistema suporta automaticamente UTF-8 e ISO-8859-1
   - Logs mostram detalhes de encoding detectado

### Desenvolvimento

Para adicionar suporte a um novo site:

1. Criar novo módulo em `src/modules/sites/`
2. Implementar métodos `execute_scraping()` e `_real_scraping()`
3. Adicionar ao menu principal em `terminal.py`
4. Criar testes específicos

## 📝 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Governo de Minas Gerais** - Portal Saude MG
- **Ministério do Desenvolvimento Social** - Sistemas MDS
- **Requests** - HTTP requests em Python
- **BeautifulSoup** - Parsing de HTML
- **OpenAI** - APIs de IA (opcional)

---

**Desenvolvido para facilitar o acesso a dados públicos governamentais brasileiros** 🇧🇷

### Status dos Scrapers
| Site | Status | Downloads | Observações |
|------|--------|-----------|-------------|
| Portal Saude MG | ✅ Funcionando | PDFs reais | Acesso direto |
| MDS Parcelas | ✅ Funcionando | Interface acessível | Requer auth para dados |
| MDS Saldo | ✅ Funcionando | Interface acessível | Requer auth para dados |