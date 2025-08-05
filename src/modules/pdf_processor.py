"""
PDF Processor Module - AI-Powered PDF Analysis and Data Extraction

This module handles intelligent processing of PDF documents downloaded by the scrapers.
Uses OpenAI GPT models to extract structured data, metadata, and validate content quality.
Optimized for Brazilian government documents.
"""

import os
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

import pymupdf4llm
import pandas as pd
from src.ai.openai_client import OpenAIClient
from src.utils.logger import logger


class PDFProcessor:
    """
    AI-powered PDF processor for extracting structured data from government documents.
    Specializes in Brazilian administrative documents like resolutions, payment records, and balance sheets.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.ai_client = OpenAIClient(api_key=api_key)
        self.processed_files = []
        
    def process_pdf_file(self, pdf_path: Union[str, Path], document_type: str = "unknown") -> Dict[str, Any]:
        """
        Process a single PDF file and extract structured data.
        
        Args:
            pdf_path: Path to the PDF file
            document_type: Type of document (resolucao, parcelas, saldo, etc.)
            
        Returns:
            Dict containing extracted data, metadata, and processing results
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return {'error': f'PDF file not found: {pdf_path}'}
        
        try:
            logger.info(f"Processing PDF: {pdf_path.name}")
            
            # Extract text from PDF
            pdf_text = self._extract_text_from_pdf(pdf_path)
            
            if not pdf_text or len(pdf_text.strip()) < 50:
                return {
                    'error': 'Failed to extract meaningful text from PDF',
                    'file_path': str(pdf_path),
                    'text_length': len(pdf_text) if pdf_text else 0
                }
            
            # Determine document type if not specified
            if document_type == "unknown":
                document_type = self._detect_document_type(pdf_text, pdf_path.name)
            
            # Process with AI
            processing_results = {
                'file_path': str(pdf_path),
                'file_name': pdf_path.name,
                'file_size': pdf_path.stat().st_size,
                'document_type': document_type,
                'text_length': len(pdf_text),
                'processed_at': datetime.now().isoformat()
            }
            
            # Extract structured data using AI
            if self.ai_client.enabled:
                structured_data = self.ai_client.process_brazilian_government_pdf(pdf_text, document_type)
                processing_results['structured_data'] = structured_data
                
                # Extract metadata
                metadata = self.ai_client.extract_pdf_metadata(pdf_text)
                processing_results['metadata'] = metadata
                
                # Validate extraction quality
                validation_rules = self._get_validation_rules(document_type)
                validation_result = self.ai_client.validate_extraction_result(structured_data, validation_rules)
                processing_results['validation'] = validation_result
                
            else:
                # Basic processing without AI
                processing_results['structured_data'] = self._basic_text_extraction(pdf_text, document_type)
                processing_results['metadata'] = self._basic_metadata_extraction(pdf_text, pdf_path)
                processing_results['validation'] = {'note': 'AI validation not available'}
            
            # Save processing results
            self._save_processing_results(processing_results, pdf_path)
            
            self.processed_files.append(str(pdf_path))
            logger.info(f"Successfully processed PDF: {pdf_path.name}")
            
            return processing_results
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return {
                'error': str(e),
                'file_path': str(pdf_path),
                'processed_at': datetime.now().isoformat()
            }
    
    def process_pdf_batch(self, pdf_directory: Union[str, Path], document_type: str = "unknown") -> Dict[str, Any]:
        """
        Process all PDF files in a directory.
        
        Args:
            pdf_directory: Directory containing PDF files
            document_type: Type of documents in the directory
            
        Returns:
            Dict containing batch processing results
        """
        pdf_directory = Path(pdf_directory)
        
        if not pdf_directory.exists():
            return {'error': f'Directory not found: {pdf_directory}'}
        
        pdf_files = list(pdf_directory.glob("*.pdf"))
        
        if not pdf_files:
            return {'error': f'No PDF files found in: {pdf_directory}'}
        
        logger.info(f"Processing {len(pdf_files)} PDF files in batch from {pdf_directory}")
        
        batch_results = {
            'directory': str(pdf_directory),
            'total_files': len(pdf_files),
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'results': [],
            'started_at': datetime.now().isoformat()
        }
        
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_file.name}")
            
            result = self.process_pdf_file(pdf_file, document_type)
            batch_results['results'].append(result)
            batch_results['processed_files'] += 1
            
            if 'error' not in result:
                batch_results['successful_files'] += 1
            else:
                batch_results['failed_files'] += 1
        
        batch_results['completed_at'] = datetime.now().isoformat()
        
        # Generate batch summary
        self._generate_batch_summary(batch_results, pdf_directory)
        
        logger.info(f"Batch processing complete: {batch_results['successful_files']}/{batch_results['total_files']} successful")
        
        return batch_results
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF using pymupdf4llm"""
        try:
            # Use pymupdf4llm for better text extraction
            text = pymupdf4llm.to_markdown(str(pdf_path))
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return ""
    
    def _detect_document_type(self, pdf_text: str, filename: str) -> str:
        """Detect document type from text content and filename"""
        text_lower = pdf_text.lower()
        filename_lower = filename.lower()
        
        # Resolution/Deliberação detection
        if any(word in text_lower for word in ['resolução', 'deliberação', 'portaria', 'decreto']):
            return 'resolucao'
        
        # Payment detection
        if any(word in text_lower for word in ['parcela', 'pagamento', 'repasse', 'transferência']):
            return 'parcelas'
        
        # Balance detection
        if any(word in text_lower for word in ['saldo', 'balanço', 'balancete', 'conta']):
            return 'saldo'
        
        # Filename based detection
        if any(word in filename_lower for word in ['resolucao', 'deliberacao']):
            return 'resolucao'
        elif any(word in filename_lower for word in ['parcela', 'pagamento']):
            return 'parcelas'
        elif any(word in filename_lower for word in ['saldo', 'balanco']):
            return 'saldo'
        
        return 'documento_generico'
    
    def _get_validation_rules(self, document_type: str) -> Dict[str, str]:
        """Get validation rules based on document type"""
        rules = {
            'resolucao': {
                'numero_resolucao': 'Must be a valid resolution number',
                'data_publicacao': 'Must be a valid Brazilian date (DD/MM/YYYY)',
                'orgao_emissor': 'Must be a government organization name'
            },
            'parcelas': {
                'municipio': 'Must be a valid municipality name',
                'valor_parcela': 'Must be a valid Brazilian currency amount (R$)',
                'data_pagamento': 'Must be a valid Brazilian date (DD/MM/YYYY)'
            },
            'saldo': {
                'municipio': 'Must be a valid municipality name',
                'saldo_atual': 'Must be a valid Brazilian currency amount (R$)',
                'data_referencia': 'Must be a valid Brazilian date (DD/MM/YYYY)'
            }
        }
        
        return rules.get(document_type, {
            'documento': 'Must contain valid document information',
            'data': 'Must contain a valid date'
        })
    
    def _basic_text_extraction(self, pdf_text: str, document_type: str) -> Dict[str, Any]:
        """Basic text extraction without AI (fallback)"""
        import re
        
        basic_data = {
            'extraction_method': 'basic_regex',
            'document_type': document_type
        }
        
        # Extract dates (DD/MM/YYYY format)
        date_pattern = r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'
        dates = re.findall(date_pattern, pdf_text)
        if dates:
            basic_data['dates_found'] = [f"{d[0]}/{d[1]}/{d[2]}" for d in dates]
        
        # Extract currency amounts (R$ format)
        currency_pattern = r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        amounts = re.findall(currency_pattern, pdf_text)
        if amounts:
            basic_data['amounts_found'] = amounts
        
        # Extract potential municipality names (capitalized words)
        municipality_pattern = r'\b[A-Z][A-Z\s]+[A-Z]\b'
        municipalities = re.findall(municipality_pattern, pdf_text)
        if municipalities:
            basic_data['potential_municipalities'] = list(set(municipalities))
        
        return basic_data
    
    def _basic_metadata_extraction(self, pdf_text: str, pdf_path: Path) -> Dict[str, Any]:
        """Basic metadata extraction without AI"""
        return {
            'filename': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'text_length': len(pdf_text),
            'extraction_date': datetime.now().isoformat(),
            'language': 'pt-BR' if any(word in pdf_text.lower() for word in ['município', 'resolução', 'parcela']) else 'unknown'
        }
    
    def _save_processing_results(self, results: Dict[str, Any], pdf_path: Path):
        """Save processing results to JSON file"""
        try:
            results_dir = pdf_path.parent / "processed_results"
            results_dir.mkdir(exist_ok=True)
            
            results_file = results_dir / f"{pdf_path.stem}_results.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Saved processing results to: {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save processing results: {e}")
    
    def _generate_batch_summary(self, batch_results: Dict[str, Any], pdf_directory: Path):
        """Generate batch processing summary"""
        try:
            summary_file = pdf_directory / "batch_processing_summary.json"
            
            # Create summary data
            summary = {
                'directory': str(pdf_directory),
                'processing_date': datetime.now().isoformat(),
                'total_files': batch_results['total_files'],
                'successful_files': batch_results['successful_files'],
                'failed_files': batch_results['failed_files'],
                'success_rate': batch_results['successful_files'] / batch_results['total_files'] * 100,
                'document_types': {},
                'total_records_extracted': 0
            }
            
            # Analyze results
            for result in batch_results['results']:
                if 'document_type' in result:
                    doc_type = result['document_type']
                    summary['document_types'][doc_type] = summary['document_types'].get(doc_type, 0) + 1
                
                if 'structured_data' in result and isinstance(result['structured_data'], dict):
                    summary['total_records_extracted'] += 1
            
            # Save summary
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Generated batch summary: {summary_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate batch summary: {e}")
    
    def export_structured_data(self, results_directory: Union[str, Path], output_format: str = "excel") -> Dict[str, Any]:
        """
        Export all structured data from processed PDFs to a consolidated file.
        
        Args:
            results_directory: Directory containing processing results
            output_format: Output format ('excel', 'csv', 'json')
            
        Returns:
            Dict with export results
        """
        results_dir = Path(results_directory)
        
        if not results_dir.exists():
            return {'error': f'Results directory not found: {results_dir}'}
        
        # Find all result files
        result_files = list(results_dir.glob("**/processed_results/*_results.json"))
        
        if not result_files:
            return {'error': 'No processing result files found'}
        
        logger.info(f"Exporting structured data from {len(result_files)} result files")
        
        all_data = []
        export_stats = {
            'files_processed': 0,
            'records_exported': 0,
            'document_types': {}
        }
        
        for result_file in result_files:
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                if 'structured_data' in result and isinstance(result['structured_data'], dict):
                    # Flatten the structured data
                    record = {
                        'source_file': result.get('file_name', ''),
                        'document_type': result.get('document_type', ''),
                        'processed_at': result.get('processed_at', ''),
                        **result['structured_data']
                    }
                    
                    all_data.append(record)
                    export_stats['records_exported'] += 1
                    
                    doc_type = result.get('document_type', 'unknown')
                    export_stats['document_types'][doc_type] = export_stats['document_types'].get(doc_type, 0) + 1
                
                export_stats['files_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing result file {result_file}: {e}")
        
        if not all_data:
            return {'error': 'No structured data found to export'}
        
        # Export data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            if output_format.lower() == "excel":
                output_file = results_dir / f"consolidated_data_{timestamp}.xlsx"
                df = pd.DataFrame(all_data)
                df.to_excel(output_file, index=False, engine='openpyxl')
                
            elif output_format.lower() == "csv":
                output_file = results_dir / f"consolidated_data_{timestamp}.csv"
                df = pd.DataFrame(all_data)
                df.to_csv(output_file, index=False, encoding='utf-8')
                
            elif output_format.lower() == "json":
                output_file = results_dir / f"consolidated_data_{timestamp}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=2)
                    
            else:
                return {'error': f'Unsupported output format: {output_format}'}
            
            export_stats['output_file'] = str(output_file)
            export_stats['export_completed_at'] = datetime.now().isoformat()
            
            logger.info(f"Successfully exported {export_stats['records_exported']} records to {output_file}")
            
            return export_stats
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return {'error': f'Export failed: {str(e)}'}
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get summary of current processing session"""
        return {
            'processed_files_count': len(self.processed_files),
            'processed_files': self.processed_files,
            'ai_enabled': self.ai_client.enabled,
            'session_start': getattr(self, '_session_start', None)
        }