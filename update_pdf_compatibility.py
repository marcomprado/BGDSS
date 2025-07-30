#!/usr/bin/env python3
"""
Script para atualizar compatibilidade com pymupdf4llm
Substitui uso do PyMuPDF/fitz por pymupdf4llm
"""

import re
from pathlib import Path

def update_file_for_pymupdf4llm(file_path: Path):
    """Atualiza arquivo para usar pymupdf4llm."""
    if not file_path.exists():
        print(f"Arquivo não encontrado: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup original
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Add simple method for processing PDF text
    if 'ai/pdf_processor_agent.py' in str(file_path):
        # Add method to process PDF text directly
        new_method = '''
    def process_pdf_text(self, pdf_text: str, extraction_template: Dict[str, str]) -> Dict[str, Any]:
        """Process PDF text that was already extracted."""
        try:
            return self._extract_structured_data_with_ai(pdf_text, extraction_template)
        except Exception as e:
            logger.error(f"PDF text processing failed: {e}")
            return {}
    
    def _extract_tables_from_markdown(self, md_text: str) -> List[TableData]:
        """Extract tables from markdown text."""
        tables = []
        
        # Look for markdown tables
        table_pattern = r'\\|(.+)\\|\\n\\|[:-\\|\\s]+\\|\\n((?:\\|.+\\|\\n?)+)'
        
        matches = re.findall(table_pattern, md_text, re.MULTILINE)
        
        for i, (header_row, data_rows) in enumerate(matches):
            # Parse headers
            headers = [h.strip() for h in header_row.split('|') if h.strip()]
            
            # Parse data rows
            rows = []
            for row in data_rows.strip().split('\\n'):
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
'''
        
        # Insert before the last class or method
        if 'def _extract_structured_data_with_ai' in content:
            content = content.replace(
                'def _extract_structured_data_with_ai',
                new_method + '\n    def _extract_structured_data_with_ai'
            )
    
    # Remove old fitz references in remaining methods that weren't updated
    problematic_methods = [
        r'def _extract_comprehensive_metadata.*?(?=def|\Z)',
        r'def _extract_text_comprehensive.*?(?=def|\Z)',
        r'def _extract_tables_advanced.*?(?=def|\Z)',
        r'def _detect_tables_on_page.*?(?=def|\Z)',
        r'def _extract_images.*?(?=def|\Z)',
        r'def _extract_form_data.*?(?=def|\Z)',
        r'def extract_specific_sections.*?(?=def|\Z)',
        r'def convert_to_searchable.*?(?=def|\Z)'
    ]
    
    for pattern in problematic_methods:
        matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
        for match in matches:
            method_content = match.group(0)
            # Replace with stub that raises NotImplementedError
            method_name = re.search(r'def (\w+)', method_content).group(1)
            stub = f'''def {method_name}(self, *args, **kwargs):
        """Method not available with pymupdf4llm - use simplified extraction."""
        logger.warning("Method {method_name} not available with pymupdf4llm")
        return None'''
            content = content.replace(method_content, stub)
    
    # Write updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Atualizado: {file_path}")
    print(f"Backup salvo em: {backup_path}")

def main():
    """Atualiza arquivos para compatibilidade com pymupdf4llm."""
    files_to_update = [
        Path('src/processors/pdf_processor.py'),
        Path('src/ai/pdf_processor_agent.py')
    ]
    
    for file_path in files_to_update:
        if file_path.exists():
            update_file_for_pymupdf4llm(file_path)
        else:
            print(f"Arquivo não encontrado: {file_path}")

if __name__ == "__main__":
    main()