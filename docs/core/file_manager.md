# FileManager - Gerenciamento de Arquivos e Backup

## Visão Geral

O `FileManager` é responsável pelo gerenciamento completo do sistema de arquivos da aplicação. Organiza dados, cria backups, mantém versionamento e realiza limpeza automática para garantir eficiência e integridade dos dados.

**Localização**: `src/core/file_manager.py`

## Funcionalidade Principal

### **Responsabilidades**
- 📁 **Organização**: Estrutura hierárquica de diretórios
- 💾 **Backup**: Sistema automático de backup e versionamento
- 🧹 **Limpeza**: Remoção automática de arquivos temporários e antigos
- 📊 **Monitoramento**: Acompanhamento de uso de espaço e estatísticas
- 🔄 **Versionamento**: Controle de versões de arquivos importantes

## Arquitetura da Classe

```python
class FileManager:
    """
    Gerenciador central do sistema de arquivos.
    
    Organiza dados em estrutura hierárquica, mantém backups
    e realiza operações de limpeza automática.
    """
```

### **Estrutura de Diretórios**
```python
def __init__(self):
    self.base_dir = Path.cwd()
    self.data_dir = self.base_dir / 'data'
    self.backup_dir = self.base_dir / 'backups'
    self.temp_dir = self.base_dir / 'temp'
    self.logs_dir = self.base_dir / 'logs'
    self.config_dir = self.base_dir / 'config'
    
    # Site-specific directories
    self.sites_data_dir = self.data_dir / 'sites'
    self.processed_dir = self.data_dir / 'processed'
    self.raw_dir = self.data_dir / 'raw'
    
    self._ensure_directories()
```

### **Organização Hierárquica**
```
project_root/
├── data/
│   ├── sites/
│   │   ├── site1/
│   │   │   ├── raw/
│   │   │   ├── processed/
│   │   │   └── metadata/
│   │   └── site2/
│   ├── processed/
│   ├── raw/
│   └── exports/
├── backups/
│   ├── 2024-01-15_14-30-00/
│   ├── 2024-01-15_20-00-00/
│   └── latest -> 2024-01-15_20-00-00/
├── temp/
├── logs/
└── config/
```

## Métodos Principais

### **1. Inicialização e Setup**

#### `_ensure_directories() -> None`
**Propósito**: Cria estrutura de diretórios necessária.

```python
def _ensure_directories(self) -> None:
    directories = [
        self.data_dir, self.backup_dir, self.temp_dir,
        self.logs_dir, self.config_dir, self.sites_data_dir,
        self.processed_dir, self.raw_dir
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {directory}")
    
    logger.info("File system structure initialized")
```

#### `create_site_directory(site_name: str) -> Path`
**Propósito**: Cria estrutura de diretórios para um site específico.

```python
def create_site_directory(self, site_name: str) -> Path:
    site_dir = self.sites_data_dir / site_name
    
    # Create site subdirectories
    subdirs = ['raw', 'processed', 'metadata', 'exports']
    for subdir in subdirs:
        (site_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Created directory structure for site: {site_name}")
    return site_dir
```

### **2. Salvamento de Dados**

#### `save_raw_data(site_name: str, data: Any, filename: str = None) -> Path`
**Propósito**: Salva dados brutos de scraping.

```python
def save_raw_data(self, site_name: str, data: Any, filename: str = None) -> Path:
    site_dir = self.create_site_directory(site_name)
    raw_dir = site_dir / 'raw'
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_data_{timestamp}.json"
    
    file_path = raw_dir / filename
    
    try:
        if isinstance(data, (dict, list)):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(data))
        
        logger.info(f"Raw data saved: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save raw data: {e}")
        raise FileOperationError(f"Cannot save raw data: {e}")
```

#### `save_processed_data(site_name: str, data: Any, format_type: str = 'json') -> Path`
**Propósito**: Salva dados processados em formato específico.

```python
def save_processed_data(self, site_name: str, data: Any, format_type: str = 'json') -> Path:
    site_dir = self.create_site_directory(site_name)
    processed_dir = site_dir / 'processed'
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"processed_data_{timestamp}.{format_type}"
    file_path = processed_dir / filename
    
    try:
        if format_type == 'json':
            self._save_as_json(file_path, data)
        elif format_type == 'csv':
            self._save_as_csv(file_path, data)
        elif format_type == 'excel':
            self._save_as_excel(file_path, data)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Create metadata
        self._save_metadata(site_name, file_path, format_type)
        
        logger.info(f"Processed data saved: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Failed to save processed data: {e}")
        raise FileOperationError(f"Cannot save processed data: {e}")
```

### **3. Sistema de Backup**

#### `create_backup(description: str = "") -> Dict[str, Any]`
**Propósito**: Cria backup completo do sistema.

```python
def create_backup(self, description: str = "") -> Dict[str, Any]:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_id = f"backup_{timestamp}"
    backup_path = self.backup_dir / backup_id
    
    try:
        backup_path.mkdir(parents=True)
        
        # Backup data directory
        data_backup = backup_path / 'data'
        shutil.copytree(self.data_dir, data_backup)
        
        # Backup configurations
        config_backup = backup_path / 'config'
        if self.config_dir.exists():
            shutil.copytree(self.config_dir, config_backup)
        
        # Create backup metadata
        metadata = {
            'backup_id': backup_id,
            'created_at': timestamp,
            'description': description,
            'files_backed_up': self._count_files(backup_path),
            'total_size': self._calculate_size(backup_path),
            'data_integrity_hash': self._calculate_hash(backup_path)
        }
        
        # Save metadata
        metadata_file = backup_path / 'backup_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update latest symlink
        latest_link = self.backup_dir / 'latest'
        if latest_link.exists():
            latest_link.unlink()
        latest_link.symlink_to(backup_id)
        
        logger.info(f"Backup created successfully: {backup_id}")
        return metadata
        
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        # Cleanup partial backup
        if backup_path.exists():
            shutil.rmtree(backup_path)
        raise BackupError(f"Backup creation failed: {e}")
```

#### `restore_backup(backup_id: str) -> bool`
**Propósito**: Restaura sistema a partir de backup.

#### `list_backups() -> List[Dict[str, Any]]`
**Propósito**: Lista todos os backups disponíveis.

#### `cleanup_old_backups(keep_count: int = 10) -> Dict[str, Any]`
**Propósito**: Remove backups antigos mantendo quantidade especificada.

### **4. Limpeza e Manutenção**

#### `cleanup_temp_files() -> Dict[str, Any]`
**Propósito**: Remove arquivos temporários.

```python
def cleanup_temp_files(self) -> Dict[str, Any]:
    deleted_files = 0
    freed_bytes = 0
    
    try:
        for temp_file in self.temp_dir.glob('*'):
            if temp_file.is_file():
                # Check file age
                file_age = time.time() - temp_file.stat().st_mtime
                if file_age > 3600:  # 1 hour
                    file_size = temp_file.stat().st_size
                    temp_file.unlink()
                    deleted_files += 1
                    freed_bytes += file_size
        
        result = {
            'deleted_files': deleted_files,
            'freed_bytes': freed_bytes,
            'freed_mb': freed_bytes / (1024 * 1024)
        }
        
        logger.info(f"Temp cleanup: {deleted_files} files, {result['freed_mb']:.2f} MB freed")
        return result
        
    except Exception as e:
        logger.error(f"Temp cleanup failed: {e}")
        raise CleanupError(f"Temp cleanup failed: {e}")
```

#### `archive_old_data(days_old: int = 30) -> Dict[str, Any]`
**Propósito**: Arquiva dados antigos.

#### `optimize_storage() -> Dict[str, Any]`
**Propósito**: Otimiza uso de storage (compressão, deduplicação).

### **5. Monitoramento e Estatísticas**

#### `get_storage_stats() -> Dict[str, Any]`
**Propósito**: Retorna estatísticas de uso de storage.

```python
def get_storage_stats(self) -> Dict[str, Any]:
    try:
        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_directory': {},
            'by_file_type': {},
            'largest_files': []
        }
        
        # Analyze each main directory
        for directory in [self.data_dir, self.backup_dir, self.temp_dir, self.logs_dir]:
            if directory.exists():
                dir_stats = self._analyze_directory(directory)
                stats['by_directory'][directory.name] = dir_stats
                stats['total_files'] += dir_stats['file_count']
                stats['total_size'] += dir_stats['total_size']
        
        # File type analysis
        stats['by_file_type'] = self._analyze_file_types()
        
        # Largest files
        stats['largest_files'] = self._find_largest_files(limit=10)
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        return {'error': str(e)}
```

#### `get_backup_status() -> Dict[str, Any]`
**Propósito**: Status do sistema de backup.

#### `get_disk_usage() -> Dict[str, Any]`
**Propósito**: Uso de disco do sistema.

### **6. Utilitários Internos**

#### `_save_metadata(site_name: str, file_path: Path, format_type: str) -> None`
**Propósito**: Salva metadados do arquivo.

```python
def _save_metadata(self, site_name: str, file_path: Path, format_type: str) -> None:
    site_dir = self.sites_data_dir / site_name
    metadata_dir = site_dir / 'metadata'
    
    metadata = {
        'file_path': str(file_path),
        'file_name': file_path.name,
        'format_type': format_type,
        'created_at': datetime.now().isoformat(),
        'file_size': file_path.stat().st_size,
        'checksum': self._calculate_file_hash(file_path)
    }
    
    metadata_file = metadata_dir / f"{file_path.stem}_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
```

#### `_calculate_hash(path: Path) -> str`
**Propósito**: Calcula hash para verificação de integridade.

#### `_compress_directory(source: Path, destination: Path) -> None`
**Propósito**: Comprime diretório para backup.

## Tratamento de Erros

### **Exceções Customizadas**
```python
class FileOperationError(Exception):
    """Erro em operação de arquivo"""

class BackupError(Exception):
    """Erro no sistema de backup"""

class CleanupError(Exception):
    """Erro em operação de limpeza"""

class StorageError(Exception):
    """Erro relacionado a storage"""
```

### **Recuperação de Falhas**
```python
def _safe_file_operation(self, operation, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return operation(*args, **kwargs)
        except (OSError, IOError) as e:
            if attempt == max_retries - 1:
                raise FileOperationError(f"Operation failed after {max_retries} attempts: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
```

## Configuração

### **Configurações de Storage**
```python
storage_config = {
    'max_backup_count': 10,
    'backup_compression': True,
    'temp_file_retention_hours': 1,
    'archive_after_days': 30,
    'auto_cleanup_enabled': True,
    'disk_usage_warning_threshold': 0.8  # 80%
}
```

### **Configurações de Limpeza**
```python
cleanup_config = {
    'temp_files_max_age': 3600,      # 1 hour
    'log_files_max_age': 2592000,    # 30 days
    'backup_retention_days': 90,     # 3 months
    'auto_cleanup_interval': 86400   # 24 hours
}
```

## Padrões de Design Utilizados

### **1. Facade Pattern**
- Interface simples para operações complexas de arquivo
- Esconde complexidade do sistema de arquivos

### **2. Template Method**
- Operações de backup seguem template comum
- Customização por tipo de dados

### **3. Strategy Pattern**
- Diferentes estratégias de compressão
- Diferentes formatos de salvamento

## Exemplos de Uso

### **Uso Básico**
```python
from src.core.file_manager import FileManager

# Initialize file manager
fm = FileManager()

# Save scraped data
data = {'title': 'Example', 'content': 'Sample content'}
file_path = fm.save_raw_data('example_site', data)

# Create backup
backup_info = fm.create_backup("Before major update")
print(f"Backup created: {backup_info['backup_id']}")

# Cleanup
cleanup_result = fm.cleanup_temp_files()
print(f"Freed {cleanup_result['freed_mb']:.2f} MB")
```

### **Monitoramento**
```python
def monitor_storage(fm: FileManager):
    stats = fm.get_storage_stats()
    
    print(f"Total files: {stats['total_files']}")
    print(f"Total size: {stats['total_size'] / (1024**3):.2f} GB")
    
    # Check disk usage
    disk_usage = fm.get_disk_usage()
    if disk_usage['usage_percent'] > 0.8:
        print("⚠️ Warning: Disk usage above 80%")
```

### **Backup Automático**
```python
def auto_backup_schedule(fm: FileManager):
    """Daily backup with cleanup"""
    try:
        # Create backup
        backup_info = fm.create_backup("Scheduled daily backup")
        
        # Cleanup old backups
        cleanup_result = fm.cleanup_old_backups(keep_count=7)
        
        logger.info(f"Auto backup completed: {backup_info['backup_id']}")
        
    except Exception as e:
        logger.error(f"Auto backup failed: {e}")
```

## Integração com Outros Componentes

### **Com Application**
```python
# application.py
self.file_manager = FileManager()
```

### **Com Scrapers**
```python
# scraper resultado
result_path = file_manager.save_raw_data(
    site_name=task.site_config_name,
    data=scraped_data
)
```

### **Com Processors**
```python
# após processamento
processed_path = file_manager.save_processed_data(
    site_name=site_name,
    data=processed_data,
    format_type='csv'
)
```

## Logs e Debugging

### **Logging Estruturado**
```python
logger.info("File operation completed", extra={
    "operation": "save_raw_data",
    "site": site_name,
    "file_size": file_path.stat().st_size,
    "file_path": str(file_path)
})
```

### **Métricas de Performance**
```python
def _track_operation_time(self, operation_name: str):
    start_time = time.time()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{operation_name} took {duration:.2f}s")
            return result
        return wrapper
    return decorator
```

---

**O FileManager garante organização, integridade e eficiência no gerenciamento de todos os arquivos do sistema Web Scraper AI.**