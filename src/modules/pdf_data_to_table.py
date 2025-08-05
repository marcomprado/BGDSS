"""
PDF Data to Table - Convert PDF data to a table format.

This module receives information from pdf_call.py and convert it to a table format.
It includes functionality for:
- Converting PDF data to a table format
- Formatting the table to be more readable
- Returning the table in a structured format to downloads/processed/name_of_the_file.xlsx
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import os

from src.ai.pdf_call import PDFProcessor
from src.utils.logger import logger


class PDFTableGenerator:
    """
    Generator of Excel tables from PDF processing results.
    Compiles data from multiple PDFs into structured Excel files.
    """
    
    def __init__(self):
        """Initialize the table generator."""
        self.processed_base_path = Path("downloads/processed")
        self.processed_base_path.mkdir(parents=True, exist_ok=True)
        
        # Column definitions for the output table
        self.columns = [
            'numero_resolucao',
            'relacionada', 
            'objeto',
            'data_inicial',
            'prazo_execucao',
            'vedado_utilizacao',
            'dotacao_orcamentaria'
        ]
        
        self.column_names_pt = {
            'numero_resolucao': 'Número da Resolução',
            'relacionada': 'Relacionada',
            'objeto': 'Objeto',
            'data_inicial': 'Data Inicial',
            'prazo_execucao': 'Prazo Execução',
            'vedado_utilizacao': 'Vedado a Utilização',
            'dotacao_orcamentaria': 'Dotação Orçamentária'
        }
    
    def process_pdf_directory_to_table(self, pdf_directory: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all PDFs in a directory and generate an Excel table.
        
        Args:
            pdf_directory: Directory containing PDF files
            api_key: OpenAI API key (optional)
            
        Returns:
            Dict with processing results and file paths
        """
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            error_msg = f"PDF directory not found: {pdf_directory}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        
        try:
            logger.info(f"Starting PDF to table processing for directory: {pdf_directory}")
            
            # Initialize PDF processor
            processor = PDFProcessor(api_key=api_key)
            
            # Process all PDFs in the directory
            processing_results = processor.process_pdf_batch(pdf_directory)
            
            if not processing_results:
                return {
                    'success': False,
                    'error': 'No PDF files found to process'
                }
            
            # Convert results to table
            table_result = self._create_table_from_results(processing_results, pdf_directory)
            
            # Add processing statistics
            table_result.update({
                'total_pdfs_found': len(processing_results),
                'successful_extractions': sum(1 for r in processing_results if r.get('success', False)),
                'processing_stats': processor.get_processing_stats()
            })
            
            logger.info(f"PDF to table processing completed. Success: {table_result.get('success', False)}")
            
            return table_result
            
        except Exception as e:
            error_msg = f"Error during PDF to table processing: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def process_extraction_results_to_table(self, processing_results: List[Dict[str, Any]], source_directory: str) -> Dict[str, Any]:
        """
        Convert existing processing results to table format.
        
        Args:
            processing_results: List of PDF processing results
            source_directory: Source directory name for file naming
            
        Returns:
            Dict with table generation results
        """
        try:
            logger.info(f"Converting {len(processing_results)} processing results to table")
            
            return self._create_table_from_results(processing_results, source_directory)
            
        except Exception as e:
            error_msg = f"Error converting results to table: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _create_table_from_results(self, processing_results: List[Dict[str, Any]], source_directory: str) -> Dict[str, Any]:
        """
        Create Excel table from processing results.
        
        Args:
            processing_results: List of PDF processing results
            source_directory: Source directory for naming
            
        Returns:
            Dict with table creation results
        """
        try:
            # Extract successful results
            successful_results = [r for r in processing_results if r.get('success', False)]
            
            if not successful_results:
                return {
                    'success': False,
                    'error': 'No successful PDF extractions found'
                }
            
            # Create table data
            table_data = []
            extraction_issues = []
            
            for result in successful_results:
                try:
                    row_data = self._extract_row_data(result)
                    table_data.append(row_data)
                except Exception as e:
                    extraction_issues.append(f"Failed to extract data from {result.get('file_name', 'unknown')}: {str(e)}")
                    continue
            
            if not table_data:
                return {
                    'success': False,
                    'error': 'No valid data rows could be extracted'
                }
            
            # Create DataFrame
            df = pd.DataFrame(table_data)
            
            # Rename columns to Portuguese
            df = df.rename(columns=self.column_names_pt)
            
            # Generate output filename
            output_file = self._generate_output_filename(source_directory)
            
            # Save to Excel with formatting
            self._save_to_excel(df, output_file)
            
            result = {
                'success': True,
                'output_file': str(output_file),
                'total_rows': len(table_data),
                'columns': list(self.column_names_pt.values()),
                'extraction_issues': extraction_issues,
                'file_size_mb': round(output_file.stat().st_size / (1024 * 1024), 2)
            }
            
            logger.info(f"Table created successfully: {output_file}")
            logger.info(f"Rows: {len(table_data)}, Issues: {len(extraction_issues)}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error creating table: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _extract_row_data(self, processing_result: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract a single row of data from processing result.
        
        Args:
            processing_result: Single PDF processing result
            
        Returns:
            Dict with row data for all columns
        """
        extracted_data = processing_result.get('extracted_data', {})
        
        # Initialize row with empty values
        row_data = {}
        
        # Extract each required field
        for column in self.columns:
            value = extracted_data.get(column, 'NÃO INFORMADO')
            
            # Clean up the value
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    value = 'NÃO INFORMADO'
            elif value is None:
                value = 'NÃO INFORMADO'
            else:
                value = str(value)
            
            row_data[column] = value
        
        return row_data
    
    def _generate_output_filename(self, source_directory: str) -> Path:
        """
        Generate output filename based on source directory and timestamp.
        
        Args:
            source_directory: Source directory name
            
        Returns:
            Path object for output file
        """
        # Clean up directory name for filename
        dir_name = Path(source_directory).name
        clean_dir_name = "".join(c for c in dir_name if c.isalnum() or c in ('_', '-')).lower()
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename
        filename = f"resolucoes_{clean_dir_name}_{timestamp}.xlsx"
        
        return self.processed_base_path / filename
    
    def _save_to_excel(self, df: pd.DataFrame, output_file: Path):
        """
        Save DataFrame to Excel with formatting.
        
        Args:
            df: DataFrame to save
            output_file: Output file path
        """
        try:
            # Create Excel writer with xlsxwriter engine for formatting
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Write the main data
                df.to_excel(writer, sheet_name='Resoluções', index=False)
                
                # Get the workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Resoluções']
                
                # Auto-adjust column widths
                for column_cells in worksheet.columns:
                    length = max(len(str(cell.value or '')) for cell in column_cells)
                    # Set reasonable limits for column width
                    length = min(max(length, 10), 100)
                    worksheet.column_dimensions[column_cells[0].column_letter].width = length
                
                # Create a summary sheet
                self._create_summary_sheet(writer, df)
            
            logger.info(f"Excel file saved successfully: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving Excel file: {e}")
            raise
    
    def _create_summary_sheet(self, writer, df: pd.DataFrame):
        """
        Create a summary sheet with processing statistics.
        
        Args:
            writer: Excel writer object
            df: Main data DataFrame
        """
        try:
            # Create summary data
            summary_data = {
                'Estatística': [
                    'Total de Resoluções',
                    'Resoluções com Data Inicial',
                    'Resoluções com Prazo Execução',
                    'Resoluções com Vedações',
                    'Resoluções com Dotação Orçamentária',
                    'Resoluções Relacionadas a Outras',
                    'Data de Processamento'
                ],
                'Valor': [
                    len(df),
                    len(df[df['Data Inicial'] != 'NÃO INFORMADO']),
                    len(df[df['Prazo Execução'] != 'NÃO INFORMADO']),
                    len(df[df['Vedado a Utilização'] != 'NÃO INFORMADO']),
                    len(df[df['Dotação Orçamentária'] != 'NÃO INFORMADO']),
                    len(df[df['Relacionada'] != 'NÃO INFORMADO']),
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Format summary sheet
            summary_sheet = writer.sheets['Resumo']
            summary_sheet.column_dimensions['A'].width = 30
            summary_sheet.column_dimensions['B'].width = 20
            
        except Exception as e:
            logger.warning(f"Could not create summary sheet: {e}")
    
    def validate_table_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate the generated table data.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validation results
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # Basic statistics
            validation_result['statistics'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'empty_cells': df.isnull().sum().sum(),
                'not_informed_count': (df == 'NÃO INFORMADO').sum().sum()
            }
            
            # Check for completely empty rows
            empty_rows = df.isnull().all(axis=1).sum()
            if empty_rows > 0:
                validation_result['issues'].append(f"Found {empty_rows} completely empty rows")
            
            # Check resolution number format
            if 'Número da Resolução' in df.columns:
                invalid_numbers = df[
                    (df['Número da Resolução'] != 'NÃO INFORMADO') & 
                    (~df['Número da Resolução'].str.match(r'^\d{1,5}/20\d{2}$', na=False))
                ]
                if not invalid_numbers.empty:
                    validation_result['warnings'].append(f"Found {len(invalid_numbers)} rows with invalid resolution number format")
            
            # Check date formats
            date_columns = ['Data Inicial', 'Prazo Execução']
            for col in date_columns:
                if col in df.columns:
                    invalid_dates = df[
                        (df[col] != 'NÃO INFORMADO') & 
                        (~df[col].str.match(r'^\d{2}/\d{2}/\d{4}$', na=False))
                    ]
                    if not invalid_dates.empty:
                        validation_result['warnings'].append(f"Found {len(invalid_dates)} rows with invalid date format in {col}")
            
            return validation_result
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def get_processing_summary(self, processing_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a processing summary from results.
        
        Args:
            processing_results: List of processing results
            
        Returns:
            Summary statistics
        """
        try:
            total_files = len(processing_results)
            successful = sum(1 for r in processing_results if r.get('success', False))
            failed = total_files - successful
            
            # Extract token usage if available
            total_tokens = 0
            for result in processing_results:
                if result.get('success') and 'extracted_data' in result:
                    ai_metadata = result['extracted_data'].get('_ai_metadata', {})
                    total_tokens += ai_metadata.get('tokens_used', 0)
            
            return {
                'total_files': total_files,
                'successful_extractions': successful,
                'failed_extractions': failed,
                'success_rate': (successful / total_files * 100) if total_files > 0 else 0,
                'total_tokens_used': total_tokens,
                'average_tokens_per_file': (total_tokens / successful) if successful > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error generating processing summary: {e}")
            return {'error': str(e)}