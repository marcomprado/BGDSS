# Configuração de Sites para Web Scraping

Este diretório contém as configurações específicas para cada site que será extraído pelo Web Scraper AI.

## Como Usar

### 1. Configuração via Arquivos JSON

Cada site deve ter seu próprio arquivo JSON neste diretório. O nome do arquivo deve ser descritivo (ex: `linkedin_jobs.json`, `indeed_br.json`).

### 2. Estrutura do Arquivo de Configuração

```json
{
  "name": "Nome do Site",
  "base_url": "https://exemplo.com",
  "description": "Descrição do que o site faz",
  
  "selectors": {
    "elemento_principal": {
      "type": "css|xpath|id|class",
      "value": "seletor_do_elemento",
      "attribute": "text|href|src|outro_atributo"
    }
  },
  
  "ai_instructions": {
    "extraction_template": {
      "campo1": "Instrução para extrair campo1",
      "campo2": "Instrução para extrair campo2"
    }
  }
}
```

### 3. Campos Principais

#### Configuração Básica
- `name`: Nome identificador do site
- `base_url`: URL principal do site
- `description`: Descrição opcional

#### Seletores (`selectors`)
Define como encontrar elementos na página:
- `type`: Tipo do seletor (css, xpath, id, class)
- `value`: O seletor propriamente dito
- `attribute`: Qual atributo extrair (text, href, etc.)

#### Autenticação (`auth_config`)
Para sites que requerem login:
- `required`: Se autenticação é obrigatória
- `credentials_env_prefix`: Prefixo para credenciais no .env

#### Instruções de IA (`ai_instructions`)
- `extraction_template`: Diz à IA como extrair cada campo
- `post_processing_instructions`: Como processar os dados extraídos

### 4. Configuração via Interface

Você também pode configurar sites usando a interface avançada:

```bash
python main.py --mode advanced
```

No menu, escolha "Site Configuration" para:
- Criar novas configurações
- Editar configurações existentes  
- Testar configurações
- Validar seletores

### 5. Credenciais de Sites

Para sites que requerem autenticação, configure as credenciais no arquivo `.env`:

```
# Para um site com credentials_env_prefix: "LINKEDIN"
LINKEDIN_USERNAME=seu_email@exemplo.com
LINKEDIN_PASSWORD=sua_senha
```

### 6. Exemplos Disponíveis

- `example_job_site.json`: Modelo para sites de vagas
- (Adicione seus próprios exemplos aqui)

### 7. Tipos de Sites Suportados

- **Sites de Vagas**: LinkedIn, Indeed, Catho, etc.
- **E-commerce**: Amazon, Mercado Livre, etc.
- **Notícias**: Sites de notícias e blogs
- **Dados Públicos**: Sites governamentais, APIs
- **Genérico**: Qualquer site com estrutura definida

### 8. Dicas

1. **Teste os seletores** antes de executar o scraping completo
2. **Use seletores específicos** para evitar elementos incorretos
3. **Configure timeouts adequados** para sites lentos
4. **Respeite robots.txt** e políticas do site
5. **Use delays entre requisições** para não sobrecarregar o servidor

### 9. Troubleshooting

- Se seletores não funcionam, use o inspetor do navegador
- Para sites dinâmicos, aguarde o carregamento completo
- Sites com CAPTCHA podem precisar intervenção manual
- Verifique se o User-Agent está adequado

### 10. Suporte

Para dúvidas sobre configuração:
1. Consulte o arquivo de exemplo
2. Use a interface avançada para testes
3. Verifique os logs para detalhes de erros