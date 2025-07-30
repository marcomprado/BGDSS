"""
File manager for organizing downloads, temporary files, backups, and versioning.
"""

import shutil
import hashlib
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os

from src.utils.logger import logger
from src.utils.exceptions import FileProcessingError
from src.models.download_result import DownloadResult
from config.settings import settings


@dataclass
class FileInfo:
    """Information about a managed file."""
    
    path: Path
    size: int
    created_at: datetime
    modified_at: datetime
    checksum: str
    file_type: str
    tags: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'path': str(self.path),
            'size': self.size,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'checksum': self.checksum,
            'file_type': self.file_type,
            'tags': self.tags,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileInfo':
        return cls(
            path=Path(data['path']),
            size=data['size'],
            created_at=datetime.fromisoformat(data['created_at']),
            modified_at=datetime.fromisoformat(data['modified_at']),
            checksum=data['checksum'],
            file_type=data['file_type'],
            tags=data['tags'],
            metadata=data['metadata']
        )


@dataclass
class BackupInfo:
    """Information about a backup."""
    
    backup_id: str
    created_at: datetime
    file_count: int
    total_size: int
    backup_path: Path
    description: str
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'backup_id': self.backup_id,
            'created_at': self.created_at.isoformat(),
            'file_count': self.file_count,
            'total_size': self.total_size,
            'backup_path': str(self.backup_path),
            'description': self.description,
            'tags': self.tags
        }


class FileManager:
    """Comprehensive file management system."""
    
    def __init__(self):
        self.base_dir = settings.BASE_DIR
        self.downloads_dir = settings.DOWNLOADS_DIR
        self.raw_dir = settings.RAW_DOWNLOADS_DIR
        self.processed_dir = settings.PROCESSED_DOWNLOADS_DIR
        self.temp_dir = settings.TEMP_DIR
        
        self.backups_dir = self.base_dir / 'backups'
        self.archive_dir = self.base_dir / 'archive'
        self.index_file = self.base_dir / 'file_index.json'
        
        self._ensure_directories()
        self._load_file_index()
        
        logger.info("FileManager initialized")
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.downloads_dir,
            self.raw_dir,
            self.processed_dir,
            self.temp_dir,
            self.backups_dir,
            self.archive_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def _load_file_index(self) -> None:
        """Load file index from disk."""
        self.file_index: Dict[str, FileInfo] = {}
        
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                
                for path_str, file_data in data.items():
                    self.file_index[path_str] = FileInfo.from_dict(file_data)
                
                logger.info(f"Loaded {len(self.file_index)} files from index")
                
            except Exception as e:
                logger.error(f"Failed to load file index: {e}")
                self.file_index = {}
    
    def _save_file_index(self) -> None:
        """Save file index to disk."""
        try:
            data = {path: info.to_dict() for path, info in self.file_index.items()}
            
            with open(self.index_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("File index saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save file index: {e}")
    
    def register_file(self, 
                     file_path: Union[str, Path],
                     file_type: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> FileInfo:
        """Register a file in the management system."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileProcessingError(f"File not found: {file_path}")
        
        try:
            stat = file_path.stat()
            checksum = self._calculate_checksum(file_path)
            
            file_info = FileInfo(
                path=file_path,
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                checksum=checksum,
                file_type=file_type or self._detect_file_type(file_path),
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self.file_index[str(file_path)] = file_info
            self._save_file_index()
            
            logger.info(f"Registered file: {file_path.name}")
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to register file {file_path}: {e}")
            raise FileProcessingError(f"File registration failed: {e}")
    
    def organize_downloads(self, task_id: Optional[str] = None) -> Dict[str, int]:
        """Organize files in the downloads directory."""
        try:
            stats = {
                'moved_files': 0,
                'organized_dirs': 0,
                'errors': 0
            }
            
            for file_path in self.raw_dir.iterdir():
                if file_path.is_file():
                    try:
                        organized_path = self._get_organized_path(file_path, task_id)
                        
                        if organized_path != file_path:
                            organized_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(file_path), str(organized_path))
                            
                            self._update_file_index_path(str(file_path), str(organized_path))
                            
                            stats['moved_files'] += 1
                            logger.debug(f"Moved file: {file_path.name} -> {organized_path}")
                        
                    except Exception as e:
                        logger.error(f"Failed to organize file {file_path}: {e}")
                        stats['errors'] += 1
            
            stats['organized_dirs'] = len(list(self.processed_dir.iterdir()))
            
            logger.info(f"Organization complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to organize downloads: {e}")
            raise FileProcessingError(f"Download organization failed: {e}")
    
    def _get_organized_path(self, file_path: Path, task_id: Optional[str] = None) -> Path:
        """Get the organized path for a file."""
        file_type = self._detect_file_type(file_path)
        date_folder = datetime.now().strftime('%Y-%m-%d')
        
        if task_id:
            organized_path = self.processed_dir / task_id / date_folder / file_type / file_path.name
        else:
            organized_path = self.processed_dir / date_folder / file_type / file_path.name
        
        counter = 1
        original_path = organized_path
        
        while organized_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            organized_path = original_path.with_name(f"{stem}_{counter}{suffix}")
            counter += 1
        
        return organized_path
    
    def _update_file_index_path(self, old_path: str, new_path: str) -> None:
        """Update file path in the index."""
        if old_path in self.file_index:
            file_info = self.file_index[old_path]
            file_info.path = Path(new_path)
            
            del self.file_index[old_path]
            self.file_index[new_path] = file_info
            
            self._save_file_index()
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> Dict[str, int]:
        """Clean up temporary files older than specified age."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            stats = {
                'deleted_files': 0,
                'freed_bytes': 0,
                'errors': 0
            }
            
            for file_path in self.temp_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if file_time < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            
                            stats['deleted_files'] += 1
                            stats['freed_bytes'] += file_size
                            
                            self.file_index.pop(str(file_path), None)
                            
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file_path}: {e}")
                        stats['errors'] += 1
            
            for dir_path in list(self.temp_dir.rglob('*')):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    try:
                        dir_path.rmdir()
                    except:
                        pass
            
            self._save_file_index()
            
            logger.info(f"Temp cleanup complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}")
            raise FileProcessingError(f"Temp cleanup failed: {e}")
    
    def create_backup(self, 
                     description: str,
                     include_patterns: Optional[List[str]] = None,
                     exclude_patterns: Optional[List[str]] = None,
                     tags: Optional[List[str]] = None) -> BackupInfo:
        """Create a backup of managed files."""
        try:
            backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.backups_dir / f"{backup_id}.zip"
            
            include_patterns = include_patterns or ['**/*']
            exclude_patterns = exclude_patterns or []
            tags = tags or []
            
            files_to_backup = self._get_files_for_backup(include_patterns, exclude_patterns)
            
            total_size = 0
            file_count = 0
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in files_to_backup:
                    try:
                        if file_path.exists():
                            relative_path = file_path.relative_to(self.base_dir)
                            zip_file.write(file_path, relative_path)
                            
                            file_count += 1
                            total_size += file_path.stat().st_size
                            
                    except Exception as e:
                        logger.warning(f"Failed to backup file {file_path}: {e}")
            
            backup_info = BackupInfo(
                backup_id=backup_id,
                created_at=datetime.now(),
                file_count=file_count,
                total_size=total_size,
                backup_path=backup_path,
                description=description,
                tags=tags
            )
            
            self._save_backup_info(backup_info)
            
            logger.info(f"Backup created: {backup_id} ({file_count} files, {total_size} bytes)")
            return backup_info
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise FileProcessingError(f"Backup creation failed: {e}")
    
    def _get_files_for_backup(self, 
                             include_patterns: List[str],
                             exclude_patterns: List[str]) -> List[Path]:
        """Get list of files matching backup criteria."""
        files_to_backup = []
        
        for pattern in include_patterns:
            for file_path in self.base_dir.glob(pattern):
                if file_path.is_file():
                    should_exclude = False
                    
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        files_to_backup.append(file_path)
        
        return list(set(files_to_backup))
    
    def _save_backup_info(self, backup_info: BackupInfo) -> None:
        """Save backup information."""
        backup_index_file = self.backups_dir / 'backup_index.json'
        
        try:
            if backup_index_file.exists():
                with open(backup_index_file, 'r') as f:
                    backup_index = json.load(f)
            else:
                backup_index = {}
            
            backup_index[backup_info.backup_id] = backup_info.to_dict()
            
            with open(backup_index_file, 'w') as f:
                json.dump(backup_index, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save backup info: {e}")
    
    def restore_backup(self, backup_id: str, target_dir: Optional[Path] = None) -> bool:
        """Restore files from a backup."""
        try:
            backup_path = self.backups_dir / f"{backup_id}.zip"
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            target_dir = target_dir or self.base_dir / 'restored' / backup_id
            target_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                zip_file.extractall(target_dir)
            
            logger.info(f"Backup restored: {backup_id} -> {target_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup {backup_id}: {e}")
            return False
    
    def archive_old_files(self, days_old: int = 90) -> Dict[str, int]:
        """Archive files older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            stats = {
                'archived_files': 0,
                'freed_bytes': 0,
                'errors': 0
            }
            
            archive_date_dir = self.archive_dir / datetime.now().strftime('%Y-%m')
            archive_date_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path_str, file_info in list(self.file_index.items()):
                if file_info.created_at < cutoff_date and file_info.path.exists():
                    try:
                        archive_path = archive_date_dir / file_info.path.name
                        
                        counter = 1
                        while archive_path.exists():
                            stem = archive_path.stem
                            suffix = archive_path.suffix
                            archive_path = archive_path.with_name(f"{stem}_{counter}{suffix}")
                            counter += 1
                        
                        shutil.move(str(file_info.path), str(archive_path))
                        
                        file_info.path = archive_path
                        file_info.tags.append('archived')
                        
                        stats['archived_files'] += 1
                        stats['freed_bytes'] += file_info.size
                        
                    except Exception as e:
                        logger.warning(f"Failed to archive file {file_info.path}: {e}")
                        stats['errors'] += 1
            
            self._save_file_index()
            
            logger.info(f"Archival complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to archive old files: {e}")
            raise FileProcessingError(f"File archival failed: {e}")
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics."""
        try:
            stats = {
                'directories': {},
                'file_types': {},
                'total_files': 0,
                'total_size': 0,
                'index_size': len(self.file_index)
            }
            
            directories_to_check = [
                ('raw', self.raw_dir),
                ('processed', self.processed_dir),
                ('temp', self.temp_dir),
                ('backups', self.backups_dir),
                ('archive', self.archive_dir)
            ]
            
            for name, directory in directories_to_check:
                dir_stats = self._get_directory_stats(directory)
                stats['directories'][name] = dir_stats
                stats['total_files'] += dir_stats['file_count']
                stats['total_size'] += dir_stats['total_size']
            
            for file_info in self.file_index.values():
                file_type = file_info.file_type
                if file_type not in stats['file_types']:
                    stats['file_types'][file_type] = {'count': 0, 'size': 0}
                
                stats['file_types'][file_type]['count'] += 1
                stats['file_types'][file_type]['size'] += file_info.size
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {e}")
            return {}
    
    def _get_directory_stats(self, directory: Path) -> Dict[str, Any]:
        """Get statistics for a specific directory."""
        stats = {
            'file_count': 0,
            'total_size': 0,
            'subdirectories': 0
        }
        
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    stats['file_count'] += 1
                    stats['total_size'] += item.stat().st_size
                elif item.is_dir() and item != directory:
                    stats['subdirectories'] += 1
        except:
            pass
        
        return stats
    
    def find_duplicates(self) -> Dict[str, List[str]]:
        """Find duplicate files based on checksums."""
        duplicates = {}
        checksum_map = {}
        
        for file_path, file_info in self.file_index.items():
            checksum = file_info.checksum
            
            if checksum in checksum_map:
                if checksum not in duplicates:
                    duplicates[checksum] = [checksum_map[checksum]]
                duplicates[checksum].append(file_path)
            else:
                checksum_map[checksum] = file_path
        
        logger.info(f"Found {len(duplicates)} sets of duplicate files")
        return duplicates
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    def _detect_file_type(self, file_path: Path) -> str:
        """Detect file type from extension."""
        extension = file_path.suffix.lower()
        
        type_mapping = {
            '.pdf': 'pdf',
            '.xlsx': 'excel', '.xls': 'excel',
            '.docx': 'word', '.doc': 'word',
            '.csv': 'csv',
            '.txt': 'text',
            '.json': 'json',
            '.png': 'image', '.jpg': 'image', '.jpeg': 'image', '.gif': 'image',
            '.zip': 'archive', '.rar': 'archive', '.7z': 'archive',
            '.html': 'html', '.htm': 'html'
        }
        
        return type_mapping.get(extension, 'unknown')
    
    def get_file_info(self, file_path: Union[str, Path]) -> Optional[FileInfo]:
        """Get information about a managed file."""
        return self.file_index.get(str(file_path))
    
    def search_files(self, 
                    query: str,
                    search_tags: bool = True,
                    search_metadata: bool = True,
                    file_type: Optional[str] = None) -> List[FileInfo]:
        """Search for files based on criteria."""
        results = []
        query_lower = query.lower()
        
        for file_info in self.file_index.values():
            if file_type and file_info.file_type != file_type:
                continue
            
            match = False
            
            if query_lower in file_info.path.name.lower():
                match = True
            
            if search_tags and any(query_lower in tag.lower() for tag in file_info.tags):
                match = True
            
            if search_metadata:
                metadata_str = json.dumps(file_info.metadata).lower()
                if query_lower in metadata_str:
                    match = True
            
            if match:
                results.append(file_info)
        
        return results