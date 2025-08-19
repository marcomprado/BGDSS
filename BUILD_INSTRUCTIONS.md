# BGDSS - Build Instructions for Windows Executable

Este documento fornece instruções completas para criar um executável Windows da aplicação BGDSS.

## Pré-requisitos

### 1. Python e Dependências
```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Instalar PyInstaller
pip install pyinstaller
```

### 2. ChromeDriver (Necessário)
Baixe o ChromeDriver compatível com sua versão do Chrome:
1. Visite: https://chromedriver.chromium.org/downloads
2. Baixe a versão correspondente à sua versão do Chrome
3. Coloque `chromedriver.exe` na pasta raiz do projeto

**Ou** use o script automático:
```bash
python build_executable.py  # Baixa automaticamente se necessário
```

## Métodos de Build

### Método 1: Script Automático (Recomendado)
```bash
# Build básico
python build_executable.py

# Build com limpeza prévia
python build_executable.py --clean

# Build debug (para depuração)
python build_executable.py --debug

# Build com pacote de distribuição
python build_executable.py --package
```

### Método 2: PyInstaller Direto
```bash
# Build usando o arquivo spec
pyinstaller bgdss.spec

# Build básico sem spec
pyinstaller --onefile --console main.py
```

## Arquivo .spec Personalizado

O arquivo `bgdss.spec` inclui:
- ✅ Todos os módulos necessários (selenium, openai, pandas, etc.)
- ✅ Suporte para ChromeDriver empacotado
- ✅ Arquivos de configuração incluídos
- ✅ Módulos de sistema (termios, msvcrt)
- ✅ Compressão UPX para menor tamanho

## Estrutura de Arquivos para Build

```
bgdss/
├── main.py                    # Arquivo principal
├── bgdss.spec                 # Configuração PyInstaller
├── build_executable.py       # Script de build automático
├── chromedriver.exe           # Driver do Chrome (necessário)
├── requirements.txt           # Dependências Python
├── config/                    # Configurações (incluído no exe)
│   ├── settings.py
│   ├── webdriver_config.py
│   └── sites_config.json
├── src/                       # Código fonte
└── .env                       # Variáveis de ambiente (não incluído)
```

## Correções Implementadas

### 1. **Paths Compatíveis com Executável**
- `src/utils/resource_utils.py` - Funções para detectar ambiente executável
- Paths relativos convertidos para absolutos
- Suporte para `sys._MEIPASS` (PyInstaller)

### 2. **WebDriver Empacotado**
- Detecção automática de ChromeDriver empacotado
- Fallback para drivers do sistema
- Evita WebDriverManager em executáveis

### 3. **Diretórios de Dados Persistentes**
- **Desenvolvimento**: Usa pasta do projeto
- **Executável**: Usa `%USERPROFILE%/Documents/BGDSS` (Windows)
- Criação automática de pastas necessárias

### 4. **Módulos de Sistema**
- Detecção melhorada de ambiente executável
- Fallbacks para termios/msvcrt em executáveis
- Mensagens informativas para usuário

## Teste do Executável

### 1. Teste Básico
```bash
# No diretório dist/
./bgdss.exe --help
```

### 2. Teste com Configuração
1. Copie `.env` para o mesmo diretório do executável
2. Execute: `./bgdss.exe`
3. Verifique criação de pastas (downloads, logs)

### 3. Teste Funcional
1. Execute um scraping simples
2. Verifique logs em `logs/`
3. Verifique downloads em `downloads/`

## Distribuição

### Arquivos Necessários para Usuário Final:
1. `bgdss.exe` - O executável principal
2. `.env` - Arquivo de configuração (criar no destino)
3. `SETUP.txt` - Instruções de uso

### Configuração no Destino:
```bash
# Criar .env no mesmo diretório do executável
echo "OPENAI_API_KEY=sua_chave_aqui" > .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env
```

## Resolução de Problemas

### 1. **ChromeDriver não encontrado**
```
ERROR: ChromeDriver not found
```
**Solução**: Baixar chromedriver.exe e colocar no mesmo diretório do executável

### 2. **Paths incorretos**
```
ERROR: Cannot find config files
```
**Solução**: Executável deve estar empacotado com `bgdss.spec`

### 3. **Módulos não encontrados**
```
ModuleNotFoundError: No module named 'xxx'
```
**Solução**: Adicionar módulo em `hiddenimports` no `bgdss.spec`

### 4. **Permissões no Windows**
```
PermissionError: Access denied
```
**Solução**: Executar como administrador ou escolher pasta com permissões

### 5. **Antivírus bloqueando**
- Executáveis PyInstaller podem ser detectados como falso positivo
- Adicionar exceção no antivírus
- Usar assinatura digital se possível

## Tamanho e Performance

### Otimizações Implementadas:
- **UPX Compression**: Reduz tamanho do executável
- **Excludes**: Remove módulos desnecessários (tkinter, matplotlib)
- **One-file**: Executável único (sem dependências externas)

### Tamanho Esperado:
- **Com UPX**: ~80-120 MB
- **Sem UPX**: ~150-200 MB

## Builds para Diferentes Sistemas

### Windows:
```bash
python build_executable.py
# Gera: bgdss.exe
```

### Linux/macOS (cross-build não recomendado):
- Executar build no sistema alvo
- Usar wine para testar executável Windows

## Automação CI/CD

Exemplo para GitHub Actions:
```yaml
- name: Build Windows Executable
  run: |
    pip install -r requirements.txt
    pip install pyinstaller
    python build_executable.py --clean
```

## Logs e Depuração

### Durante o Build:
- Logs do PyInstaller em `build/`
- Warnings sobre módulos não encontrados

### Durante Execução:
- Logs da aplicação em `logs/` (pasta criada pelo executável)
- Usar `--debug` para mais informações

## Próximos Passos

1. ✅ Testar executável em máquina Windows limpa
2. ✅ Verificar funcionamento sem Python instalado
3. ✅ Testar com diferentes versões do Windows
4. ✅ Documentar instalação para usuários finais
5. ✅ Configurar distribuição automática (opcional)