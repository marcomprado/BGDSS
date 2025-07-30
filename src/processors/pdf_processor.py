"""
PDF processor for text extraction, table detection, and AI integration.
"""

try:
    import pymupdf4llm
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    pymupdf4llm = None

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import base64
import io

from src.ai.pdf_processor_agent import PDFProcessorAgent, PDFExtractionResult
from src.utils.logger import logger
from src.utils.exceptions import FileProcessingError
from src.models.download_result import ProcessingResult, ProcessingStatus


@dataclass
class PDFMetadata:
    """Extended PDF metadata."""
    
    title: str = ""
    author: str = ""
    subject: str = ""
    creator: str = ""
    producer: str = ""
    creation_date: str = ""
    modification_date: str = ""
    pages: int = 0
    encrypted: bool = False
    has_forms: bool = False
    has_images: bool = False
    file_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'author': self.author,
            'subject': self.subject,
            'creator': self.creator,
            'producer': self.producer,
            'creation_date': self.creation_date,
            'modification_date': self.modification_date,
            'pages': self.pages,
            'encrypted': self.encrypted,
            'has_forms': self.has_forms,
            'has_images': self.has_images,
            'file_size': self.file_size
        }


@dataclass
class TextExtractionResult:
    """Result of text extraction from PDF."""
    
    full_text: str
    page_texts: List[str]
    word_count: int
    character_count: int
    language_detected: Optional[str] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'full_text_preview': self.full_text[:500] + '...' if len(self.full_text) > 500 else self.full_text,
            'page_count': len(self.page_texts),
            'word_count': self.word_count,
            'character_count': self.character_count,
            'language_detected': self.language_detected,
            'confidence': self.confidence
        }


class PDFProcessor:
    """Processor for PDF files with AI integration."""
    
    def __init__(self, use_ai: bool = True):
        if not PDF_AVAILABLE:
            logger.warning("pymupdf4llm not available - PDF processing will be limited")
        
        self.use_ai = use_ai
        self.ai_agent = PDFProcessorAgent() if use_ai else None
        logger.info(f"PDFProcessor initialized (AI: {use_ai}, PDF: {PDF_AVAILABLE})")
    
    def process_pdf(self, 
                   file_path: Union[str, Path],
                   password: Optional[str] = None,
                   extract_images: bool = False,
                   extract_tables: bool = True,
                   ai_extraction_template: Optional[Dict[str, str]] = None) -> ProcessingResult:
        """Process a PDF file with comprehensive extraction."""
        file_path = Path(file_path)
        start_time = datetime.now()
        
        result = ProcessingResult(
            processor_name="PDFProcessor",
            start_time=start_time
        )
        
        try:
            if not file_path.exists():
                raise FileProcessingError(f"PDF file not found: {file_path}")
            
            if file_path.suffix.lower() != '.pdf':
                raise FileProcessingError(f"Not a PDF file: {file_path}")
            
            if not PDF_AVAILABLE:
                raise FileProcessingError("pymupdf4llm not available - cannot process PDF")
            
            # Use pymupdf4llm for simplified extraction
            md_text = pymupdf4llm.to_markdown(str(file_path))
            
            # Create basic metadata
            metadata = self._extract_basic_metadata(file_path)
            result.extracted_data['metadata'] = metadata.to_dict()
            
            # Process extracted text
            text_result = self._process_extracted_text(md_text)
            result.extracted_data['text_extraction'] = text_result.to_dict()
            result.extracted_text = text_result.full_text
            
            # Basic table extraction from markdown
            if extract_tables:
                tables = self._extract_tables_from_markdown(md_text)
                result.extracted_data['tables'] = tables
            
            # AI processing if enabled
            if self.use_ai and ai_extraction_template:
                ai_result = self.ai_agent.process_pdf_text(md_text, ai_extraction_template)
                result.extracted_data['ai_extraction'] = ai_result
            
            result.status = ProcessingStatus.COMPLETED
            result.end_time = datetime.now()
            result.calculate_duration()
            
            logger.info(f"PDF processed successfully: {file_path.name}")
            
        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.calculate_duration()
            
            logger.error(f"PDF processing failed: {e}")
        
        return result
    
    def _extract_basic_metadata(self, file_path: Path) -> PDFMetadata:
        """Extract basic metadata from PDF file."""
        try:
            # Basic file metadata
            file_size = file_path.stat().st_size
            
            # Try to estimate page count from markdown
            try:
                # Simple estimation - not perfect but avoids fitz dependency
                pages = 1  # Default to 1 page
            except:
                pages = 0  # Unknown page count
            
            return PDFMetadata(
                title=file_path.stem,
                author="",
                subject="",
                creator="",
                producer="",
                creation_date="",
                modification_date="",
                pages=pages,
                encrypted=False,  # pymupdf4llm handles decryption internally
                has_forms=False,  # Not available with pymupdf4llm
                has_images=False,  # Not available with pymupdf4llm
                file_size=file_size
            )
            
        except Exception as e:
            logger.warning(f"Could not extract metadata: {e}")
            return PDFMetadata(
                title=file_path.stem,
                file_size=file_path.stat().st_size
            )
    
    def _process_extracted_text(self, md_text: str) -> TextExtractionResult:
        """Process text extracted by pymupdf4llm."""
        # Convert markdown to plain text for some analyses
        import re
        plain_text = re.sub(r'[#*_`\[\]]+', '', md_text)
        plain_text = re.sub(r'\n+', '\n', plain_text).strip()
        
        # Split by pages if possible (look for page markers)
        page_texts = []
        if '---' in md_text:  # Common page separator
            pages = md_text.split('---')
            page_texts = [page.strip() for page in pages if page.strip()]
        else:
            # Estimate pages by content length (rough approximation)
            text_length = len(md_text)
            estimated_pages = max(1, text_length // 2000)  # ~2000 chars per page
            page_size = len(md_text) // estimated_pages
            
            for i in range(estimated_pages):
                start = i * page_size
                end = start + page_size if i < estimated_pages - 1 else len(md_text)
                page_texts.append(md_text[start:end])
        
        word_count = len(plain_text.split())
        character_count = len(plain_text)
        
        return TextExtractionResult(
            full_text=md_text,  # Keep markdown format
            page_texts=page_texts,
            word_count=word_count,
            character_count=character_count,
            language_detected=self._detect_language(plain_text),
            confidence=0.9  # pymupdf4llm is generally reliable
        )
    
    def _extract_tables_from_markdown(self, md_text: str) -> List[Dict[str, Any]]:
        """Extract tables from markdown text."""
        tables = []
        
        # Look for markdown tables
        import re
        table_pattern = r'\|(.+)\|\n\|[:-\|\s]+\|\n((?:\|.+\|\n?)+)'
        
        matches = re.findall(table_pattern, md_text, re.MULTILINE)
        
        for i, (header_row, data_rows) in enumerate(matches):
            # Parse headers
            headers = [h.strip() for h in header_row.split('|') if h.strip()]
            
            # Parse data rows
            rows = []
            for row in data_rows.strip().split('\n'):
                if '|' in row:
                    cells = [c.strip() for c in row.split('|') if c.strip()]
                    if cells:
                        rows.append(cells)
            
            if headers and rows:
                tables.append({
                    'headers': headers,
                    'rows': rows,
                    'page_number': i + 1,  # Approximate
                    'row_count': len(rows),
                    'column_count': len(headers)
                })
        
        return tables
    
    def _extract_comprehensive_metadata(self, *args, **kwargs) -> PDFMetadata:
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_extract_comprehensive_metadata method not available with pymupdf4llm - use _extract_basic_metadata instead")
        return PDFMetadata()
    
    def _extract_text_comprehensive(self, *args, **kwargs) -> TextExtractionResult:
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_extract_text_comprehensive method not available with pymupdf4llm - use _process_extracted_text instead")
        return TextExtractionResult(
            full_text="",
            page_texts=[],
            word_count=0,
            character_count=0
        )
    
    def _extract_tables_advanced(self, *args, **kwargs) -> List[Any]:
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_extract_tables_advanced method not available with pymupdf4llm - use _extract_tables_from_markdown instead")
        return []
    
    def _detect_tables_on_page(self, *args, **kwargs) -> List[Any]:
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_detect_tables_on_page method not available with pymupdf4llm")
        return []
    
    def _find_table_structures(self, *args, **kwargs) -> List[Dict]:
        """Legacy method - not available with pymupdf4llm."""
        return []
    
    def _looks_like_table_row(self, text: str) -> bool:
        """Check if text looks like a table row - basic implementation."""
        if not text.strip():
            return False
        
        separators = ['\t', '|', '  ', ',']
        for sep in separators:
            if text.count(sep) >= 2:
                return True
        
        if re.search(r'\d+.*\d+.*\d+', text):
            return True
        
        return False
    
    def _parse_table_structure(self, *args, **kwargs) -> Optional[Dict]:
        """Legacy method - not available with pymupdf4llm."""
        return None
    
    def _extract_images(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_extract_images method not available with pymupdf4llm")
        return []
    
    def _extract_form_data(self, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_extract_form_data method not available with pymupdf4llm")
        return None
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text."""
        text = re.sub(r'\s+', ' ', text)
        
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        
        text = re.sub(r'(\n\s*){3,}', '\n\n', text)
        
        return text.strip()
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect language of extracted text."""
        try:
            from langdetect import detect
            if len(text) > 100:
                return detect(text[:1000])
        except:
            pass
        
        if re.search(r'[àáâãäåçèéêëìíîïñòóôõöùúûüý]', text.lower()):
            return 'pt'  
        elif re.search(r'[äöüß]', text.lower()):
            return 'de'  
        elif re.search(r'[àâçéèêëïîôùûüÿ]', text.lower()):
            return 'fr'  
        
        return 'en'  
    
    def extract_specific_sections(self, 
                                *args, 
                                **kwargs) -> Dict[str, str]:
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("extract_specific_sections method not available with pymupdf4llm")
        return {}
    
    def convert_to_searchable(self, file_path: Path, output_path: Path) -> bool:
        """Convert PDF to searchable format using OCR."""
        try:
            logger.warning("OCR functionality not implemented - requires additional dependencies")
            return False
        except Exception as e:
            logger.error(f"OCR conversion failed: {e}")
            return False