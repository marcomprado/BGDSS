"""
Validators - Centralized validation patterns and methods for Brazilian government data.

This module provides pre-compiled regex patterns and validation methods
to eliminate code duplication across the codebase and improve performance.
"""

import re
from typing import Pattern, Optional
from datetime import datetime


class BrazilianGovernmentValidators:
    """Centralized validation patterns and methods for Brazilian government documents."""
    
    # Pre-compiled regex patterns for optimal performance
    RESOLUTION_NUMBER: Pattern[str] = re.compile(r'^\d{1,5}/20\d{2}$')
    BRAZILIAN_DATE: Pattern[str] = re.compile(r'^\d{2}/\d{2}/\d{4}$')
    BUDGET_CODES: Pattern[str] = re.compile(r'\b(301|302|303|304|305|306|122|242)\b')
    CURRENCY: Pattern[str] = re.compile(r'R\$\s*[\d.,]+')
    
    # Budget allocation to category mapping
    BUDGET_CATEGORIES = {
        '301': 'Atenção Primária',
        '302': 'MAC',
        '303': 'Assistência Farmacêutica',
        '304': 'Vigilância Sanitária',
        '305': 'Vigilância Epidemiológica',
        '306': 'Alimentação e Nutrição',
        '122': 'ADM',
        '242': 'Assist. ao Portador de Deficiência'
    }
    
    @classmethod
    def validate_resolution_number(cls, number: str) -> bool:
        """
        Validate resolution number format (xxxxx/20XX).
        
        Args:
            number: Resolution number string
            
        Returns:
            True if valid format, False otherwise
        """
        if not number or not isinstance(number, str):
            return False
        return bool(cls.RESOLUTION_NUMBER.match(number.strip()))
    
    @classmethod
    def validate_brazilian_date(cls, date_str: str) -> bool:
        """
        Validate Brazilian date format (DD/MM/YYYY) and date validity.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid date format and date, False otherwise
        """
        if not date_str or not isinstance(date_str, str):
            return False
        
        date_str = date_str.strip()
        
        # Check format first
        if not cls.BRAZILIAN_DATE.match(date_str):
            return False
        
        # Validate actual date
        try:
            day, month, year = map(int, date_str.split('/'))
            datetime(year, month, day)
            return True
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def extract_budget_codes(cls, text: str) -> list[str]:
        """
        Extract budget allocation codes from text.
        
        Args:
            text: Text to search for budget codes
            
        Returns:
            List of found budget codes
        """
        if not text or not isinstance(text, str):
            return []
        return cls.BUDGET_CODES.findall(text)
    
    @classmethod
    def categorize_by_budget_code(cls, budget_code: str) -> str:
        """
        Get category name for a budget code.
        
        Args:
            budget_code: Budget allocation code
            
        Returns:
            Category name or 'NÃO CLASSIFICADO' if not found
        """
        if not budget_code or not isinstance(budget_code, str):
            return "NÃO CLASSIFICADO"
        
        return cls.BUDGET_CATEGORIES.get(budget_code.strip(), "NÃO CLASSIFICADO")
    
    @classmethod
    def categorize_by_budget_allocation(cls, dotacao_orcamentaria: str) -> str:
        """
        Categorize resolution based on budget allocation number.
        
        Args:
            dotacao_orcamentaria: Budget allocation number string
            
        Returns:
            Category abbreviation based on mapping table
        """
        if not dotacao_orcamentaria or dotacao_orcamentaria == "NÃO INFORMADO":
            return "NÃO CLASSIFICADO"
        
        # Extract budget codes from allocation string
        codes = cls.extract_budget_codes(dotacao_orcamentaria)
        
        if codes:
            # Return category for the first matching code found
            return cls.categorize_by_budget_code(codes[0])
        
        return "NÃO CLASSIFICADO"
    
    @classmethod
    def extract_currency_values(cls, text: str) -> list[str]:
        """
        Extract Brazilian currency values from text.
        
        Args:
            text: Text to search for currency values
            
        Returns:
            List of found currency strings
        """
        if not text or not isinstance(text, str):
            return []
        return cls.CURRENCY.findall(text)
    
    @classmethod
    def validate_data_completeness(cls, data: dict) -> dict:
        """
        Validate completeness of extracted data.
        
        Args:
            data: Dictionary with extracted data
            
        Returns:
            Dictionary with validation results
        """
        required_fields = [
            'numero_resolucao', 'relacionada', 'objeto', 'data_inicial',
            'prazo_execucao', 'vedado_utilizacao', 'dotacao_orcamentaria',
            'link', 'abreviacao'
        ]
        
        validation_result = {
            'valid': True,
            'missing_fields': [],
            'invalid_formats': [],
            'warnings': []
        }
        
        # Check for missing fields
        for field in required_fields:
            if field not in data or not data[field]:
                validation_result['missing_fields'].append(field)
                validation_result['valid'] = False
        
        # Validate specific field formats
        if 'numero_resolucao' in data and data['numero_resolucao'] != "NÃO INFORMADO":
            if not cls.validate_resolution_number(data['numero_resolucao']):
                validation_result['invalid_formats'].append('numero_resolucao')
                validation_result['warnings'].append(
                    f"Invalid resolution number format: {data['numero_resolucao']}"
                )
        
        # Validate date fields
        date_fields = ['data_inicial', 'prazo_execucao']
        for field in date_fields:
            if field in data and data[field] != "NÃO INFORMADO":
                if not cls.validate_brazilian_date(data[field]):
                    validation_result['invalid_formats'].append(field)
                    validation_result['warnings'].append(
                        f"Invalid date format in {field}: {data[field]}"
                    )
        
        return validation_result


# Create a singleton instance for easy access
validators = BrazilianGovernmentValidators()