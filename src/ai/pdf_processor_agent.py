"""
AI Agent for processing PDF files and extracting structured data.
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
try:
    import pymupdf4llm
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    pymupdf4llm = None

import pandas as pd
import re
import json

from src.ai.openai_client import OpenAIClient
from src.utils.logger import logger
from src.utils.exceptions import FileProcessingError, AIError


@dataclass
class TableData:
    """Represents extracted table data."""
    
    headers: List[str]
    rows: List[List[str]]
    page_number: int
    confidence: float = 0.0
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame."""
        return pd.DataFrame(self.rows, columns=self.headers)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'headers': self.headers,
            'rows': self.rows,
            'page_number': self.page_number,
            'confidence': self.confidence
        }


@dataclass
class PDFExtractionResult:
    """Complete result of PDF extraction."""
    
    file_path: str
    total_pages: int
    extracted_text: str
    tables: List[TableData]
    metadata: Dict[str, Any]
    structured_data: Dict[str, Any]
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'total_pages': self.total_pages,
            'extracted_text': self.extracted_text[:1000],  
            'tables': [table.to_dict() for table in self.tables],
            'metadata': self.metadata,
            'structured_data': self.structured_data,
            'processing_time': self.processing_time
        }


class PDFProcessorAgent:
    """AI agent for processing PDF files."""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        self.ai_client = openai_client or OpenAIClient()
        if not PDF_AVAILABLE:
            logger.warning("pymupdf4llm not available - PDF processing will be limited")
        logger.info(f"PDFProcessorAgent initialized (PDF: {PDF_AVAILABLE})")
    
    def process_pdf_text(self, pdf_text: str, extraction_template: Dict[str, str]) -> Dict[str, Any]:
        """Process PDF text that was already extracted by pymupdf4llm."""
        try:
            return self._extract_structured_data_with_ai(pdf_text, extraction_template)
        except Exception as e:
            logger.error(f"PDF text processing failed: {e}")
            return {}
    
    def process_pdf(self, 
                   pdf_path: Union[str, Path],
                   extraction_template: Optional[Dict[str, str]] = None) -> PDFExtractionResult:
        """Process a PDF file and extract structured data using pymupdf4llm."""
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileProcessingError(f"PDF file not found: {pdf_path}")
        
        if pdf_path.suffix.lower() != '.pdf':
            raise FileProcessingError(f"Not a PDF file: {pdf_path}")
        
        if not PDF_AVAILABLE:
            raise FileProcessingError("pymupdf4llm not available - cannot process PDF")
        
        import time
        start_time = time.time()
        
        try:
            # Use pymupdf4llm for extraction
            md_text = pymupdf4llm.to_markdown(str(pdf_path))
            
            # Extract tables from markdown
            tables = self._extract_tables_from_markdown(md_text)
            
            # Basic metadata
            metadata = {
                'title': pdf_path.stem,
                'file_size': pdf_path.stat().st_size,
                'pages': md_text.count('---') if '---' in md_text else 1  # Estimate
            }
            
            structured_data = {}
            if extraction_template:
                structured_data = self._extract_structured_data(
                    md_text, extraction_template
                )
            
            processing_time = time.time() - start_time
            
            result = PDFExtractionResult(
                file_path=str(pdf_path),
                total_pages=metadata.get('pages', 1),
                extracted_text=md_text,
                tables=tables,
                metadata=metadata,
                structured_data=structured_data,
                processing_time=processing_time
            )
            
            logger.info(f"PDF processed successfully: {pdf_path.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            raise FileProcessingError(
                f"Failed to process PDF: {e}",
                file_path=str(pdf_path),
                file_type='pdf'
            )
    
    def _extract_tables_from_markdown(self, md_text: str) -> List[TableData]:
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
                tables.append(TableData(
                    headers=headers,
                    rows=rows,
                    page_number=i + 1,
                    confidence=0.8
                ))
        
        return tables
    
    def _extract_text(self, *args, **kwargs):
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_extract_text method not available with pymupdf4llm - use process_pdf instead")
        return ""
    
    def _extract_tables(self, *args, **kwargs):
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_extract_tables method not available with pymupdf4llm - use _extract_tables_from_markdown instead")
        return []
    
    def _detect_tables_on_page(self, *args, **kwargs):
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_detect_tables_on_page method not available with pymupdf4llm")
        return []
    
    def _extract_metadata(self, *args, **kwargs):
        """Legacy method - not available with pymupdf4llm."""
        logger.warning("_extract_metadata method not available with pymupdf4llm")
        return {}
    
    def _extract_structured_data(self,
                                text_content: str,
                                extraction_template: Dict[str, str]) -> Dict[str, Any]:
        """Use AI to extract structured data based on template."""
        try:
            result = self.ai_client.extract_structured_data(
                text_content=text_content[:8000],  
                extraction_template=extraction_template
            )
            
            logger.info("Structured data extracted successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {'error': str(e)}
    
    def extract_forms_data(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """Extract form-like data from PDF."""
        result = self.process_pdf(pdf_path)
        
        form_patterns = {
            'name': r'Name[:\s]+([^\n]+)',
            'date': r'Date[:\s]+([^\n]+)',
            'email': r'Email[:\s]+([^\n]+)',
            'phone': r'Phone[:\s]+([^\n]+)',
            'address': r'Address[:\s]+([^\n]+)',
            'id': r'ID[:\s]+([^\n]+)'
        }
        
        extracted_forms = {}
        
        for field, pattern in form_patterns.items():
            matches = re.findall(pattern, result.extracted_text, re.IGNORECASE)
            if matches:
                extracted_forms[field] = matches[0].strip()
        
        response = self.ai_client.chat_completion(
            messages=[{
                "role": "user",
                "content": f"""Extract form data from this text. Look for fields like name, 
                date, contact info, etc. Return as JSON.
                
                Text: {result.extracted_text[:3000]}"""
            }],
            response_format={"type": "json_object"}
        )
        
        try:
            ai_extracted = json.loads(response['content'])
            extracted_forms.update(ai_extracted)
        except:
            pass
        
        return extracted_forms
    
    def convert_tables_to_excel(self, 
                               pdf_result: PDFExtractionResult,
                               output_path: Union[str, Path]) -> Path:
        """Convert extracted tables to Excel file."""
        output_path = Path(output_path)
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for i, table in enumerate(pdf_result.tables):
                    df = table.to_dataframe()
                    sheet_name = f'Table_{i+1}_Page_{table.page_number}'
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                
                if pdf_result.structured_data:
                    struct_df = pd.DataFrame([pdf_result.structured_data])
                    struct_df.to_excel(writer, sheet_name='Structured_Data', index=False)
            
            logger.info(f"Tables exported to Excel: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise FileProcessingError(
                f"Failed to export to Excel: {e}",
                file_path=str(output_path),
                file_type='excel'
            )
    
    def validate_extraction(self,
                           extraction_result: PDFExtractionResult,
                           validation_rules: Dict[str, str]) -> Dict[str, Any]:
        """Validate extracted data against rules."""
        validation_result = self.ai_client.validate_extraction_result(
            extracted_data=extraction_result.structured_data,
            validation_rules=validation_rules
        )
        
        return validation_result