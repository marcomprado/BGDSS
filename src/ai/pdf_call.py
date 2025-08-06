"""
PDF Call - AI-powered PDF processing and analysis for Brazilian government resolutions.

This module provides a high-level interface for processing and analyzing PDF documents using AI.
It includes functionality for:
- Analyzing PDF content using OpenAI API
- Extracting text from PDFs using pymupdf4llm
- Extracting structured data from Brazilian government resolutions
- Return the data in a structured format for table generation
"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import pymupdf4llm

from src.ai.openai_client import OpenAIClient
from src.utils.logger import logger
from src.utils.exceptions import AIError


class PDFProcessor:
    """
    AI-powered PDF processor specialized in Brazilian government resolutions.
    Extracts structured data using OpenAI API with specific prompts for resolution analysis.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the PDF processor with OpenAI client.
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        self.ai_client = OpenAIClient(api_key=api_key)
        self.processed_count = 0
        
        if not self.ai_client.enabled:
            raise AIError("OpenAI API key not configured - PDF processing requires AI functionality")
            
        logger.info("PDF Processor initialized with AI capabilities")
    
    def process_single_pdf(self, pdf_path: str, file_link: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a single PDF file and extract structured resolution data.
        
        Args:
            pdf_path: Path to the PDF file
            file_link: Optional direct link to the PDF from web scraper
            
        Returns:
            Dict containing extracted structured data or error information
        """
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': str(pdf_path)
            }
        
        try:
            logger.info(f"Processing PDF: {pdf_file.name}")
            
            # Extract text from PDF
            pdf_text = self._extract_text_from_pdf(pdf_file)
            
            if not pdf_text or len(pdf_text.strip()) < 100:
                error_msg = f"Failed to extract meaningful text from PDF: {pdf_file.name}"
                logger.warning(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'file_path': str(pdf_path),
                    'text_length': len(pdf_text) if pdf_text else 0
                }
            
            logger.info(f"Extracted {len(pdf_text)} characters from PDF")
            
            # Process with AI to extract structured data
            extracted_data = self._extract_resolution_data(pdf_text)
            
            if 'error' in extracted_data:
                return {
                    'success': False,
                    'error': extracted_data['error'],
                    'file_path': str(pdf_path),
                    'ai_response': extracted_data.get('raw_content', '')
                }
            
            # Add categorization based on budget allocation
            if 'dotacao_orcamentaria' in extracted_data:
                extracted_data['abreviacao'] = self._categorize_by_budget_allocation(extracted_data['dotacao_orcamentaria'])
            else:
                extracted_data['abreviacao'] = "NÃO CLASSIFICADO"
            
            # Add link information
            extracted_data['link'] = file_link or "NÃO INFORMADO"
            
            # Add metadata
            result = {
                'success': True,
                'file_path': str(pdf_path),
                'file_name': pdf_file.name,
                'file_link': file_link,
                'text_length': len(pdf_text),
                'extracted_data': extracted_data
            }
            
            self.processed_count += 1
            logger.info(f"Successfully processed PDF: {pdf_file.name}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing PDF {pdf_file.name}: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'file_path': str(pdf_path)
            }
    
    def process_pdf_batch(self, pdf_directory: str) -> List[Dict[str, Any]]:
        """
        Process all PDF files in a directory.
        
        Args:
            pdf_directory: Path to directory containing PDF files
            
        Returns:
            List of processing results for each PDF
        """
        pdf_dir = Path(pdf_directory)
        
        if not pdf_dir.exists():
            error_msg = f"PDF directory not found: {pdf_directory}"
            logger.error(error_msg)
            return [{'success': False, 'error': error_msg}]
        
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in directory: {pdf_directory}")
            return []
        
        # Try to load URL mapping if it exists
        url_mapping = self._load_url_mapping(pdf_dir)
        
        logger.info(f"Processing {len(pdf_files)} PDF files from {pdf_directory}")
        if url_mapping:
            logger.info(f"URL mapping loaded with {len(url_mapping)} entries")
        
        results = []
        successful_count = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_file.name}")
            
            # Get URL for this file if available
            file_url = None
            if url_mapping and pdf_file.name in url_mapping:
                file_url = url_mapping[pdf_file.name]['url']
                logger.debug(f"Found URL for {pdf_file.name}: {file_url}")
            
            result = self.process_single_pdf(str(pdf_file), file_link=file_url)
            results.append(result)
            
            if result.get('success', False):
                successful_count += 1
        
        logger.info(f"Batch processing complete: {successful_count}/{len(pdf_files)} files processed successfully")
        
        return results
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract text content from PDF using pymupdf4llm.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            logger.debug(f"Extracting text from: {pdf_path.name}")
            text = pymupdf4llm.to_markdown(str(pdf_path))
            
            if text:
                logger.debug(f"Successfully extracted {len(text)} characters")
                return text
            else:
                logger.warning(f"No text extracted from PDF: {pdf_path.name}")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path.name}: {e}")
            return ""
    
    def _extract_resolution_data(self, pdf_text: str) -> Dict[str, Any]:
        """
        Extract structured resolution data using AI with specific prompt.
        
        Args:
            pdf_text: Text content extracted from PDF
            
        Returns:
            Dict containing extracted structured data
        """
        try:
            # Create the specialized prompt for resolution extraction
            system_prompt = self._get_resolution_extraction_prompt()
            
            # Prepare user content with PDF text
            user_content = f"""Analise o seguinte texto extraído de um PDF de resolução e extraia os dados estruturados conforme solicitado:

TEXTO DO PDF:
{pdf_text[:20000]}  # Limit to ~20k characters to avoid token limits

Proceda com a análise e retorne os dados no formato JSON especificado."""

            # Create messages for API call
            messages = self.ai_client.create_prompt(system_prompt, user_content)
            
            # Call OpenAI API with JSON response format
            response = self.ai_client.chat_completion(
                messages,
                temperature=0.1,  # Low temperature for consistent extraction
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            extracted_data = json.loads(response['content'])
            
            # Add API usage info
            extracted_data['_ai_metadata'] = {
                'tokens_used': response['usage']['total_tokens'],
                'model': response['model']
            }
            
            logger.info(f"AI extraction successful. Tokens used: {response['usage']['total_tokens']}")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse AI response as JSON: {e}"
            logger.error(error_msg)
            return {
                'error': error_msg,
                'raw_content': response.get('content', '') if 'response' in locals() else ''
            }
            
        except Exception as e:
            error_msg = f"Error during AI extraction: {e}"
            logger.error(error_msg)
            return {'error': error_msg}
    
    def _get_resolution_extraction_prompt(self) -> str:
        """
        Get the specialized prompt for Brazilian government resolution extraction.
        
        Returns:
            System prompt for AI extraction
        """
        return """Você é um assistente especializado em análise de documentos legais. Sua tarefa é extrair informações específicas de um PDF de resolução e retornar os dados em formato estruturado para composição de uma tabela.

INSTRUÇÕES GERAIS:
• Analise cuidadosamente todo o conteúdo do PDF fornecido
• Extraia apenas as informações solicitadas
• Seja preciso e literal nas extrações
• Se alguma informação não estiver presente, retorne "NÃO INFORMADO"
• Mantenha a formatação original dos dados extraídos

DADOS A EXTRAIR:

1. NÚMERO DA RESOLUÇÃO
• Formato esperado: "xxxxx/20XX"
• Localização: Geralmente no cabeçalho ou início do documento
• Exemplo: "12345/2023"

2. RELACIONADA
• Descrição: Verificar se a resolução cita, modifica, altera ou revoga outra resolução
• Retornar: O número da resolução relacionada (mesmo formato xxxxx/20XX) ou "NÃO INFORMADO"
• Palavras-chave: "modifica", "altera", "revoga", "em substituição", "complementa"

3. OBJETO
• Descrição: Extrair integralmente o primeiro parágrafo da resolução
• Características: Geralmente começa após o número e data, descreve o propósito da resolução
• Retornar: Texto completo do primeiro parágrafo, sem alterações

4. DATA INICIAL
• Formato esperado: "DD/MM/AAAA"
• Localização: Data que aparece logo após o número da resolução
• Exemplo: "15/03/2023"

5. PRAZO EXECUÇÃO
• Descrição: Data estimada mencionada no texto para execução/vigência
• Cálculo: Se expresso em meses/anos a partir da data inicial:
  - Cada mês = 30 dias
  - Cada ano = 365 dias
• Formato de retorno: "DD/MM/AAAA"
• Se não especificado: "NÃO INFORMADO"

6. VEDADO A UTILIZAÇÃO
• Descrição: Parágrafo ou trecho que detalha restrições de uso de recursos/verbas
• Palavras-chave: "vedado", "proibido", "não poderá ser utilizado", "fica vedada"
• Retornar: Texto completo do parágrafo que contém as vedações

7. DOTAÇÃO ORÇAMENTÁRIA
• Descrição: Conjunto numérico que segue imediatamente após a expressão "dotação orçamentária"
• Formato: Sequência de números, pontos e traços (ex: "12.345.67.89.123")
• Atenção especial: Procurar pelos códigos 301, 302, 303, 304, 305, 306, 122, 242 dentro da dotação
• Retornar: Toda a sequência numérica da dotação orçamentária completa

FORMATO DE RESPOSTA:
Retorne os dados extraídos no seguinte formato JSON:
{
  "numero_resolucao": "",
  "relacionada": "",
  "objeto": "",
  "data_inicial": "",
  "prazo_execucao": "",
  "vedado_utilizacao": "",
  "dotacao_orcamentaria": ""
}

NOTA IMPORTANTE: Os campos "link" e "abreviacao" são adicionados automaticamente pelo sistema após a extração.

OBSERVAÇÕES IMPORTANTES:
• Mantenha fidelidade absoluta ao texto original
• Não interprete ou parafraseie as informações
• Em caso de dúvida sobre localização de dados, busque por padrões similares
• Datas devem estar sempre no formato DD/MM/AAAA
• Para campos não encontrados, use exatamente "NÃO INFORMADO"

Proceda com a análise do PDF fornecido e retorne os dados no formato especificado."""
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dict with processing statistics
        """
        return {
            'files_processed': self.processed_count,
            'ai_enabled': self.ai_client.enabled,
            'model_used': self.ai_client.default_model if self.ai_client.enabled else None
        }
    
    def validate_extraction_result(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the extracted data for completeness and format.
        
        Args:
            extracted_data: Data extracted from PDF
            
        Returns:
            Validation result with issues found
        """
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        required_fields = [
            'numero_resolucao', 'relacionada', 'objeto', 'data_inicial',
            'prazo_execucao', 'vedado_utilizacao', 'dotacao_orcamentaria',
            'link', 'abreviacao'
        ]
        
        # Check for missing fields
        for field in required_fields:
            if field not in extracted_data:
                validation_result['valid'] = False
                validation_result['issues'].append(f"Missing required field: {field}")
        
        # Validate number format (xxxxx/20XX)
        if 'numero_resolucao' in extracted_data:
            numero = extracted_data['numero_resolucao']
            if numero != "NÃO INFORMADO" and not self._validate_resolution_number_format(numero):
                validation_result['warnings'].append(f"Resolution number format may be incorrect: {numero}")
        
        # Validate date formats (DD/MM/AAAA)
        date_fields = ['data_inicial', 'prazo_execucao']
        for field in date_fields:
            if field in extracted_data:
                date_value = extracted_data[field]
                if date_value != "NÃO INFORMADO" and not self._validate_date_format(date_value):
                    validation_result['warnings'].append(f"Date format may be incorrect in {field}: {date_value}")
        
        return validation_result
    
    def _validate_resolution_number_format(self, number: str) -> bool:
        """Validate resolution number format (xxxxx/20XX)"""
        import re
        pattern = r'^\d{1,5}/20\d{2}$'
        return bool(re.match(pattern, number))
    
    def _validate_date_format(self, date_str: str) -> bool:
        """Validate Brazilian date format (DD/MM/AAAA)"""
        import re
        pattern = r'^\d{2}/\d{2}/\d{4}$'
        return bool(re.match(pattern, date_str))
    
    def _categorize_by_budget_allocation(self, dotacao_orcamentaria: str) -> str:
        """
        Categorize resolution based on budget allocation number.
        
        Args:
            dotacao_orcamentaria: Budget allocation number string
            
        Returns:
            Category abbreviation based on mapping table
        """
        # Budget allocation to category mapping
        category_mapping = {
            '301': 'Atenção Primária',
            '302': 'MAC',
            '303': 'Assistência Farmacêutica', 
            '304': 'Vigilância Sanitária',
            '305': 'Vigilância Epidemiológica',
            '306': 'Alimentação e Nutrição',
            '122': 'ADM',
            '242': 'Assist. ao Portador de Deficiência'
        }
        
        if not dotacao_orcamentaria or dotacao_orcamentaria == "NÃO INFORMADO":
            return "NÃO CLASSIFICADO"
        
        # Extract 3-digit codes from budget allocation number
        import re
        # Look for 3-digit patterns in the budget allocation
        matches = re.findall(r'\b(301|302|303|304|305|306|122|242)\b', dotacao_orcamentaria)
        
        if matches:
            # Return category for the first matching code found
            return category_mapping.get(matches[0], "NÃO CLASSIFICADO")
        
        return "NÃO CLASSIFICADO"
    
    def _load_url_mapping(self, pdf_directory: Path) -> Optional[Dict[str, Dict[str, str]]]:
        """
        Load URL mapping from JSON file if it exists.
        
        Args:
            pdf_directory: Path to directory containing PDFs
            
        Returns:
            URL mapping dictionary or None if not found
        """
        try:
            mapping_file = pdf_directory / 'url_mapping.json'
            if not mapping_file.exists():
                logger.debug(f"URL mapping file not found: {mapping_file}")
                return None
            
            import json
            with open(mapping_file, 'r', encoding='utf-8') as f:
                url_mapping = json.load(f)
            
            logger.info(f"URL mapping loaded successfully from: {mapping_file}")
            return url_mapping
            
        except Exception as e:
            logger.warning(f"Failed to load URL mapping: {e}")
            return None