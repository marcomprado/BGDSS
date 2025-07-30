"""
CSV processor for validation, cleaning, and normalization of CSV data.
"""

import csv
import pandas as pd
import chardet
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from io import StringIO

from src.utils.logger import logger
from src.utils.exceptions import FileProcessingError
from src.models.download_result import ProcessingResult, ProcessingStatus


@dataclass
class CSVValidationResult:
    """Result of CSV validation process."""
    
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    row_count: int
    column_count: int
    encoding: str
    delimiter: str
    has_headers: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'issues': self.issues,
            'suggestions': self.suggestions,
            'row_count': self.row_count,
            'column_count': self.column_count,
            'encoding': self.encoding,
            'delimiter': self.delimiter,
            'has_headers': self.has_headers
        }


@dataclass
class CSVCleaningResult:
    """Result of CSV cleaning process."""
    
    original_rows: int
    cleaned_rows: int
    removed_rows: int
    fixed_issues: List[str]
    remaining_issues: List[str]
    cleaned_data: pd.DataFrame
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_rows': self.original_rows,
            'cleaned_rows': self.cleaned_rows,
            'removed_rows': self.removed_rows,
            'fixed_issues': self.fixed_issues,
            'remaining_issues': self.remaining_issues,
            'data_preview': self.cleaned_data.head().to_dict() if not self.cleaned_data.empty else {}
        }


class CSVProcessor:
    """Processor for CSV files with validation, cleaning, and normalization."""
    
    def __init__(self):
        self.supported_encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        self.common_delimiters = [',', ';', '\t', '|']
        logger.info("CSVProcessor initialized")
    
    def process_csv(self, 
                   file_path: Union[str, Path],
                   auto_clean: bool = True,
                   validation_rules: Optional[Dict[str, Any]] = None) -> ProcessingResult:
        """Process a CSV file with validation and cleaning."""
        file_path = Path(file_path)
        start_time = datetime.now()
        
        result = ProcessingResult(
            processor_name="CSVProcessor",
            start_time=start_time
        )
        
        try:
            if not file_path.exists():
                raise FileProcessingError(f"CSV file not found: {file_path}")
            
            encoding = self.detect_encoding(file_path)
            delimiter = self.detect_delimiter(file_path, encoding)
            
            validation_result = self.validate_csv(file_path, encoding, delimiter)
            
            if auto_clean and not validation_result.is_valid:
                cleaning_result = self.clean_csv(file_path, encoding, delimiter)
                df = cleaning_result.cleaned_data
                
                result.extracted_data['cleaning_result'] = cleaning_result.to_dict()
            else:
                df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
            
            result.extracted_data['validation'] = validation_result.to_dict()
            result.extracted_data['dataframe_info'] = self._get_dataframe_info(df)
            result.extracted_data['sample_data'] = df.head(10).to_dict('records')
            
            result.status = ProcessingStatus.COMPLETED
            result.end_time = datetime.now()
            result.calculate_duration()
            
            logger.info(f"CSV processed successfully: {file_path.name}")
            
        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.now()
            result.calculate_duration()
            
            logger.error(f"CSV processing failed: {e}")
        
        return result
    
    def detect_encoding(self, file_path: Path) -> str:
        """Detect the encoding of a CSV file."""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  
            
            detected = chardet.detect(raw_data)
            encoding = detected['encoding']
            
            if encoding and detected['confidence'] > 0.7:
                if encoding.lower().startswith('utf-8'):
                    return 'utf-8'
                elif encoding.lower() in ['latin-1', 'iso-8859-1']:
                    return 'latin-1'
                elif encoding.lower() in ['cp1252', 'windows-1252']:
                    return 'cp1252'
            
            for enc in self.supported_encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        f.read(1000)
                    logger.info(f"Detected encoding: {enc}")
                    return enc
                except UnicodeDecodeError:
                    continue
            
            logger.warning("Could not detect encoding, defaulting to utf-8")
            return 'utf-8'
            
        except Exception as e:
            logger.error(f"Error detecting encoding: {e}")
            return 'utf-8'
    
    def detect_delimiter(self, file_path: Path, encoding: str) -> str:
        """Detect the delimiter used in a CSV file."""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                sample = f.read(2048)
            
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
            
            if delimiter in self.common_delimiters:
                logger.info(f"Detected delimiter: '{delimiter}'")
                return delimiter
            
            delimiter_counts = {}
            for delim in self.common_delimiters:
                delimiter_counts[delim] = sample.count(delim)
            
            most_common = max(delimiter_counts, key=delimiter_counts.get)
            
            if delimiter_counts[most_common] > 0:
                logger.info(f"Using most common delimiter: '{most_common}'")
                return most_common
            
            logger.warning("Could not detect delimiter, defaulting to comma")
            return ','
            
        except Exception as e:
            logger.error(f"Error detecting delimiter: {e}")
            return ','
    
    def validate_csv(self, 
                    file_path: Path, 
                    encoding: str, 
                    delimiter: str) -> CSVValidationResult:
        """Validate CSV file structure and content."""
        issues = []
        suggestions = []
        
        try:
            df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
            
            row_count = len(df)
            column_count = len(df.columns)
            
            has_headers = self._detect_headers(df)
            
            if row_count == 0:
                issues.append("CSV file is empty")
            
            if column_count == 0:
                issues.append("No columns detected")
            
            if df.columns.duplicated().any():
                issues.append("Duplicate column names found")
                suggestions.append("Rename duplicate columns")
            
            if df.isnull().sum().sum() > 0:
                null_percentage = (df.isnull().sum().sum() / (row_count * column_count)) * 100
                if null_percentage > 20:
                    issues.append(f"High percentage of missing values: {null_percentage:.1f}%")
                    suggestions.append("Consider data imputation or removal of sparse columns")
            
            empty_columns = df.columns[df.isnull().all()].tolist()
            if empty_columns:
                issues.append(f"Empty columns found: {empty_columns}")
                suggestions.append("Remove empty columns")
            
            constant_columns = []
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].nunique() == 1:
                    constant_columns.append(col)
            
            if constant_columns:
                issues.append(f"Columns with constant values: {constant_columns}")
                suggestions.append("Consider removing constant columns")
            
            encoding_issues = self._check_encoding_issues(df)
            if encoding_issues:
                issues.extend(encoding_issues)
                suggestions.append("Fix encoding issues before processing")
            
            is_valid = len(issues) == 0
            
            return CSVValidationResult(
                is_valid=is_valid,
                issues=issues,
                suggestions=suggestions,
                row_count=row_count,
                column_count=column_count,
                encoding=encoding,
                delimiter=delimiter,
                has_headers=has_headers
            )
            
        except Exception as e:
            logger.error(f"CSV validation failed: {e}")
            return CSVValidationResult(
                is_valid=False,
                issues=[f"Validation error: {str(e)}"],
                suggestions=["Check file format and encoding"],
                row_count=0,
                column_count=0,
                encoding=encoding,
                delimiter=delimiter,
                has_headers=False
            )
    
    def clean_csv(self, 
                 file_path: Path, 
                 encoding: str, 
                 delimiter: str) -> CSVCleaningResult:
        """Clean CSV data by fixing common issues."""
        try:
            df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
            original_rows = len(df)
            fixed_issues = []
            remaining_issues = []
            
            df_cleaned = df.copy()
            
            if df_cleaned.columns.duplicated().any():
                df_cleaned.columns = self._fix_duplicate_columns(df_cleaned.columns)
                fixed_issues.append("Fixed duplicate column names")
            
            empty_columns = df_cleaned.columns[df_cleaned.isnull().all()].tolist()
            if empty_columns:
                df_cleaned = df_cleaned.drop(columns=empty_columns)
                fixed_issues.append(f"Removed {len(empty_columns)} empty columns")
            
            constant_columns = []
            for col in df_cleaned.select_dtypes(include=['object']).columns:
                if df_cleaned[col].nunique() <= 1:
                    constant_columns.append(col)
            
            if constant_columns:
                df_cleaned = df_cleaned.drop(columns=constant_columns)
                fixed_issues.append(f"Removed {len(constant_columns)} constant columns")
            
            df_cleaned = df_cleaned.dropna(how='all')
            rows_after_empty_removal = len(df_cleaned)
            if rows_after_empty_removal < original_rows:
                fixed_issues.append(f"Removed {original_rows - rows_after_empty_removal} empty rows")
            
            for col in df_cleaned.select_dtypes(include=['object']).columns:
                df_cleaned[col] = df_cleaned[col].astype(str).str.strip()
                df_cleaned[col] = df_cleaned[col].replace('', pd.NA)
            
            for col in df_cleaned.select_dtypes(include=['object']).columns:
                try:
                    numeric_col = pd.to_numeric(df_cleaned[col], errors='coerce')
                    if not numeric_col.isna().all():
                        non_na_ratio = numeric_col.notna().sum() / len(numeric_col)
                        if non_na_ratio > 0.8:
                            df_cleaned[col] = numeric_col
                            fixed_issues.append(f"Converted column '{col}' to numeric")
                except:
                    pass
            
            df_cleaned = self._normalize_text_columns(df_cleaned)
            if len(df_cleaned.select_dtypes(include=['object']).columns) > 0:
                fixed_issues.append("Normalized text columns")
            
            null_percentage = (df_cleaned.isnull().sum().sum() / (len(df_cleaned) * len(df_cleaned.columns))) * 100
            if null_percentage > 10:
                remaining_issues.append(f"Still has {null_percentage:.1f}% missing values")
            
            cleaned_rows = len(df_cleaned)
            removed_rows = original_rows - cleaned_rows
            
            return CSVCleaningResult(
                original_rows=original_rows,
                cleaned_rows=cleaned_rows,
                removed_rows=removed_rows,
                fixed_issues=fixed_issues,
                remaining_issues=remaining_issues,
                cleaned_data=df_cleaned
            )
            
        except Exception as e:
            logger.error(f"CSV cleaning failed: {e}")
            raise FileProcessingError(f"Failed to clean CSV: {e}")
    
    def normalize_data(self, df: pd.DataFrame, normalization_rules: Dict[str, str]) -> pd.DataFrame:
        """Apply normalization rules to DataFrame."""
        df_normalized = df.copy()
        
        for column, rule in normalization_rules.items():
            if column not in df_normalized.columns:
                continue
            
            try:
                if rule == 'lowercase':
                    df_normalized[column] = df_normalized[column].astype(str).str.lower()
                
                elif rule == 'uppercase':
                    df_normalized[column] = df_normalized[column].astype(str).str.upper()
                
                elif rule == 'title_case':
                    df_normalized[column] = df_normalized[column].astype(str).str.title()
                
                elif rule == 'remove_spaces':
                    df_normalized[column] = df_normalized[column].astype(str).str.replace(' ', '')
                
                elif rule == 'phone_format':
                    df_normalized[column] = df_normalized[column].apply(self._format_phone)
                
                elif rule == 'email_lowercase':
                    df_normalized[column] = df_normalized[column].astype(str).str.lower().str.strip()
                
                elif rule == 'date_format':
                    df_normalized[column] = pd.to_datetime(df_normalized[column], errors='coerce')
                
                logger.debug(f"Applied normalization '{rule}' to column '{column}'")
                
            except Exception as e:
                logger.warning(f"Failed to apply normalization '{rule}' to column '{column}': {e}")
        
        return df_normalized
    
    def export_cleaned_csv(self, 
                          df: pd.DataFrame, 
                          output_path: Path,
                          encoding: str = 'utf-8') -> bool:
        """Export cleaned DataFrame to CSV."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False, encoding=encoding)
            logger.info(f"Cleaned CSV exported to: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return False
    
    def _detect_headers(self, df: pd.DataFrame) -> bool:
        """Detect if CSV has headers."""
        if df.empty:
            return False
        
        first_row = df.iloc[0] if len(df) > 0 else pd.Series()
        
        numeric_columns = df.select_dtypes(include=['number']).columns
        
        for col in numeric_columns:
            if col in first_row and pd.isna(first_row[col]):
                continue
            try:
                float(first_row[col])
                return False  
            except (ValueError, TypeError):
                pass
        
        return True
    
    def _check_encoding_issues(self, df: pd.DataFrame) -> List[str]:
        """Check for encoding-related issues."""
        issues = []
        
        for col in df.select_dtypes(include=['object']).columns:
            sample_values = df[col].dropna().astype(str).head(100)
            
            for value in sample_values:
                if any(ord(char) > 127 for char in value):
                    if '�' in value or '\ufffd' in value:
                        issues.append(f"Encoding issues detected in column '{col}'")
                        break
        
        return issues
    
    def _fix_duplicate_columns(self, columns: pd.Index) -> List[str]:
        """Fix duplicate column names."""
        seen = {}
        new_columns = []
        
        for col in columns:
            if col in seen:
                seen[col] += 1
                new_columns.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_columns.append(col)
        
        return new_columns
    
    def _normalize_text_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize text columns."""
        df_normalized = df.copy()
        
        for col in df_normalized.select_dtypes(include=['object']).columns:
            df_normalized[col] = (df_normalized[col]
                                .astype(str)
                                .str.strip()
                                .str.replace(r'\s+', ' ', regex=True)
                                .str.replace(r'[^\w\s\.\-@]', '', regex=True))
        
        return df_normalized
    
    def _format_phone(self, phone: str) -> str:
        """Format phone number."""
        if pd.isna(phone):
            return phone
        
        digits = re.sub(r'\D', '', str(phone))
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"1-({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return str(phone)
    
    def _get_dataframe_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary information about DataFrame."""
        return {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.to_dict(),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'null_counts': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum()
        }