# BGDSS - Brazilian Government Data Scraping System

Sistema Python para extração automatizada de dados de sites do governo brasileiro com processamento inteligente de PDFs usando IA.

## O que faz

O BGDSS extrai dados de portais de transparência do governo brasileiro e processa documentos PDF usando inteligência artificial para gerar planilhas Excel estruturadas. 

O sistema baixa automaticamente PDFs de sites governamentais, extrai informações importantes usando IA, e organiza tudo em planilhas Excel prontas para análise.

## Como usar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure sua chave da OpenAI no arquivo `.env`:
   ```bash
   OPENAI_API_KEY=sua_chave_aqui
   OPENAI_MODEL=gpt-4o-mini
   ```

3. Execute o aplicativo:
   ```bash
   python main.py
   ```

4. Selecione um site do menu e configure os parâmetros (ano, mês)

## Sites suportados

### 1. Portal Saúde MG ✅ FUNCIONANDO
- **Site**: Deliberações da Secretaria de Saúde de MG
- **Status**: Completamente implementado
- **Funcionalidades**: Baixa PDFs automaticamente e extrai dados estruturados para Excel

### 2. MDS Parcelas Pagas ✅ FUNCIONANDO
- **Site**: Dados de parcelas pagas aos municípios
- **Status**: Completamente implementado
- **Funcionalidades**: Interface e scraping implementados

### 3. MDS Saldo Detalhado ✅ FUNCIONANDO
- **Site**: Dados detalhados de saldo municipal
- **Status**: Completamente implementado
- **Funcionalidades**: Interface avançada com seleção múltipla de meses

## Arquitetura

O sistema é organizado de forma modular:

- **Interface**: Terminal interativo com progresso em tempo real
- **Scrapers**: Módulos específicos para cada site governamental  
- **Processamento IA**: Extração inteligente de dados dos PDFs
- **Saída**: Geração automática de planilhas Excel organizadas

### Estrutura de pastas
```
src/
├── ai/              # Módulos de IA
├── modules/sites/   # Scrapers específicos por site
├── ui/             # Interface do terminal
└── utils/          # Utilitários e logs

downloads/          # Arquivos baixados e processados
logs/              # Logs da aplicação
```

## Requisitos

- Python 3.8+
- Navegador Chrome (para o scraping)
- Chave da API OpenAI (para processamento com IA)

## Observações

- O processamento com IA consome tokens da OpenAI
- Todos os 3 sites estão funcionais
- O Portal Saúde MG inclui processamento completo com IA
- As planilhas Excel são geradas automaticamente com dados estruturados