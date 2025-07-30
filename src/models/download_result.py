"""
Download result data models using dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any


class FileType(Enum):
    """Enumeration of supported file types."""
    
    PDF = "pdf"
    EXCEL = "excel"
    WORD = "word"
    CSV = "csv"
    JSON = "json"
    TEXT = "text"
    IMAGE = "image"
    HTML = "html"
    XML = "xml"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_extension(cls, extension: str) -> 'FileType':
        """Determine file type from extension."""
        ext_map = {
            '.pdf': cls.PDF,
            '.xls': cls.EXCEL,
            '.xlsx': cls.EXCEL,
            '.doc': cls.WORD,
            '.docx': cls.WORD,
            '.csv': cls.CSV,
            '.json': cls.JSON,
            '.txt': cls.TEXT,
            '.png': cls.IMAGE,
            '.jpg': cls.IMAGE,
            '.jpeg': cls.IMAGE,
            '.gif': cls.IMAGE,
            '.html': cls.HTML,
            '.htm': cls.HTML,
            '.xml': cls.XML
        }
        return ext_map.get(extension.lower(), cls.UNKNOWN)


class ProcessingStatus(Enum):
    """Enumeration of file processing statuses."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileMetadata:
    """Metadata information for downloaded files."""
    
    size_bytes: int = 0
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    author: Optional[str] = None
    title: Optional[str] = None
    page_count: Optional[int] = None  
    word_count: Optional[int] = None  
    checksum: Optional[str] = None  
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'size_bytes': self.size_bytes,
            'mime_type': self.mime_type,
            'encoding': self.encoding,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'author': self.author,
            'title': self.title,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'checksum': self.checksum
        }


@dataclass
class ProcessingResult:
    """Result of file processing operation."""
    
    status: ProcessingStatus = ProcessingStatus.PENDING
    processor_name: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    extracted_text: Optional[str] = None
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def calculate_duration(self) -> None:
        """Calculate processing duration."""
        if self.start_time and self.end_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'status': self.status.value,
            'processor_name': self.processor_name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'extracted_text': self.extracted_text[:1000] if self.extracted_text else None,  
            'extracted_data': self.extracted_data,
            'error_message': self.error_message,
            'warnings': self.warnings
        }


@dataclass
class DownloadResult:
    """Complete representation of a downloaded file result."""
    
    result_id: str = field(default_factory=lambda: str(uuid4()))
    
    task_id: str = ""
    
    source_url: str = ""
    
    file_name: str = ""
    file_type: FileType = FileType.UNKNOWN
    
    raw_file_path: Optional[Path] = None
    processed_file_path: Optional[Path] = None
    
    downloaded_at: datetime = field(default_factory=datetime.now)
    
    download_duration_seconds: float = 0.0
    
    metadata: FileMetadata = field(default_factory=FileMetadata)
    
    processing_results: List[ProcessingResult] = field(default_factory=list)
    
    ai_analysis: Optional[Dict[str, Any]] = None
    
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    is_archived: bool = False
    archive_path: Optional[Path] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.file_name and self.file_type == FileType.UNKNOWN:
            extension = Path(self.file_name).suffix
            self.file_type = FileType.from_extension(extension)
    
    def add_processing_result(self, result: ProcessingResult) -> None:
        """Add a processing result."""
        result.calculate_duration()
        self.processing_results.append(result)
    
    def get_latest_processing_result(self) -> Optional[ProcessingResult]:
        """Get the most recent processing result."""
        if self.processing_results:
            return max(self.processing_results, key=lambda r: r.end_time or datetime.min)
        return None
    
    def is_processed(self) -> bool:
        """Check if file has been successfully processed."""
        return any(r.status == ProcessingStatus.COMPLETED for r in self.processing_results)
    
    def get_file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.metadata.size_bytes / (1024 * 1024)
    
    def archive(self, archive_path: Path) -> None:
        """Mark file as archived."""
        self.is_archived = True
        self.archive_path = archive_path
    
    def get_all_extracted_text(self) -> str:
        """Combine all extracted text from processing results."""
        texts = []
        for result in self.processing_results:
            if result.extracted_text:
                texts.append(result.extracted_text)
        return "\n\n".join(texts)
    
    def get_all_extracted_data(self) -> Dict[str, Any]:
        """Combine all extracted data from processing results."""
        combined_data = {}
        for result in self.processing_results:
            if result.extracted_data:
                combined_data.update(result.extracted_data)
        return combined_data
    
    def validate_paths(self) -> List[str]:
        """Validate file paths exist."""
        issues = []
        
        if self.raw_file_path and not self.raw_file_path.exists():
            issues.append(f"Raw file not found: {self.raw_file_path}")
        
        if self.processed_file_path and not self.processed_file_path.exists():
            issues.append(f"Processed file not found: {self.processed_file_path}")
        
        if self.is_archived and self.archive_path and not self.archive_path.exists():
            issues.append(f"Archive file not found: {self.archive_path}")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'result_id': self.result_id,
            'task_id': self.task_id,
            'source_url': self.source_url,
            'file_name': self.file_name,
            'file_type': self.file_type.value,
            'raw_file_path': str(self.raw_file_path) if self.raw_file_path else None,
            'processed_file_path': str(self.processed_file_path) if self.processed_file_path else None,
            'downloaded_at': self.downloaded_at.isoformat(),
            'download_duration_seconds': self.download_duration_seconds,
            'metadata': self.metadata.to_dict(),
            'processing_results': [r.to_dict() for r in self.processing_results],
            'ai_analysis': self.ai_analysis,
            'tags': self.tags,
            'custom_metadata': self.custom_metadata,
            'is_archived': self.is_archived,
            'archive_path': str(self.archive_path) if self.archive_path else None,
            'is_processed': self.is_processed(),
            'file_size_mb': self.get_file_size_mb()
        }


from uuid import uuid4