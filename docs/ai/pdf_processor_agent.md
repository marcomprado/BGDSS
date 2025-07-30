# PDFProcessorAgent - Processamento Inteligente de PDFs

## Visão Geral

O `PDFProcessorAgent` combina extração de texto de PDFs com análise de IA para compreensão semântica, extração de dados estruturados e geração automática de resumos e insights.

**Localização**: `src/ai/pdf_processor_agent.py`

## Funcionalidade Principal

### **Responsabilidades**
- 📄 **Extração de Texto**: Conversão de PDF para texto estruturado
- 🧠 **Análise Semântica**: Compreensão do conteúdo usando IA
- 📊 **Extração de Dados**: Identificação automática de informações estruturadas
- 📋 **Geração de Resumos**: Sínteses automáticas de documentos longos
- 🔍 **Busca Inteligente**: Localização de informações específicas

## Arquitetura da Classe

```python
class PDFProcessorAgent:
    """
    Agente especializado em processamento inteligente de arquivos PDF
    usando extração de texto e análise de IA.
    """
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.processing_history: List[PDFProcessingRecord] = []
        self.extraction_cache: Dict[str, Any] = {}
```

## Métodos Principais

### **1. Extração e Processamento Básico**

#### `process_pdf_file(file_path: str, analysis_type: str = "comprehensive") -> PDFProcessingResult`
**Propósito**: Processa arquivo PDF completo com análise de IA.

```python
def process_pdf_file(self, file_path: str, analysis_type: str = "comprehensive") -> PDFProcessingResult:
    try:
        start_time = time.time()
        
        # Extract text from PDF
        extracted_text = self._extract_text_from_pdf(file_path)
        
        if not extracted_text.strip():
            raise PDFProcessingError("No text could be extracted from PDF")
        
        # Get file metadata
        metadata = self._get_pdf_metadata(file_path)
        
        # Perform AI analysis
        ai_analysis = self._analyze_pdf_content(extracted_text, analysis_type)
        
        # Create processing result
        result = PDFProcessingResult(
            file_path=file_path,
            extracted_text=extracted_text,
            metadata=metadata,
            ai_analysis=ai_analysis,
            processing_time=time.time() - start_time,
            analysis_type=analysis_type
        )
        
        # Cache result
        self._cache_processing_result(file_path, result)
        
        # Record processing
        self._record_processing(result)
        
        logger.info(f"PDF processed successfully: {file_path}")
        return result
        
    except Exception as e:
        logger.error(f"PDF processing failed for {file_path}: {e}")
        raise PDFProcessingError(f"Failed to process PDF: {e}")
```

#### `extract_structured_data(file_path: str, target_fields: List[str]) -> Dict[str, Any]`
**Propósito**: Extrai campos específicos de dados estruturados.

```python
def extract_structured_data(self, file_path: str, target_fields: List[str]) -> Dict[str, Any]:
    try:
        # Get or extract text
        if file_path in self.extraction_cache:
            extracted_text = self.extraction_cache[file_path]['text']
        else:
            extracted_text = self._extract_text_from_pdf(file_path)
        
        # Create extraction prompt
        extraction_prompt = f\"\"\"
        Extract the following specific information from this PDF content:
        
        Target Fields: {target_fields}
        
        PDF Content:
        {extracted_text[:4000]}  # Limit for token usage
        
        Provide response in JSON format with exact field names as keys.
        If a field is not found, use null as the value.
        Include confidence scores (0-1) for each extraction.
        
        Format:
        {{
            "extracted_data": {{
                "field1": "value1",
                "field2": "value2"
            }},
            "confidence_scores": {{
                "field1": 0.95,
                "field2": 0.87
            }},
            "extraction_notes": "Any relevant notes about the extraction"
        }}
        \"\"\"
        
        extraction_result = self.openai_client.generate_completion(
            extraction_prompt,
            max_tokens=1000,
            temperature=0.1  # Low temperature for accuracy
        )
        
        # Parse JSON response
        try:
            parsed_result = json.loads(extraction_result)
        except json.JSONDecodeError:
            # Fallback parsing
            parsed_result = self._fallback_parse_extraction(extraction_result, target_fields)
        
        parsed_result['file_path'] = file_path
        parsed_result['extraction_timestamp'] = datetime.now().isoformat()
        
        return parsed_result
        
    except Exception as e:
        logger.error(f"Structured data extraction failed: {e}")
        raise PDFProcessingError(f"Failed to extract structured data: {e}")
```

### **2. Análise e Compreensão**

#### `generate_summary(file_path: str, summary_type: str = "executive") -> Dict[str, Any]`
**Propósito**: Gera resumo automático do documento PDF.

```python
def generate_summary(self, file_path: str, summary_type: str = "executive") -> Dict[str, Any]:
    try:
        # Extract text
        extracted_text = self._extract_text_from_pdf(file_path)
        
        summary_prompts = {
            'executive': \"\"\"
            Create an executive summary of this document:
            - Main purpose and objective (1-2 sentences)
            - Key findings or conclusions (3-5 bullet points)
            - Important numbers, dates, or statistics
            - Recommended actions or next steps
            
            Document: {content}
            
            Provide response in JSON format.
            \"\"\",
            
            'detailed': \"\"\"
            Create a detailed summary of this document:
            - Document overview and structure
            - Main sections and their key points
            - Important details and supporting information
            - Conclusions and implications
            - References to important data or figures
            
            Document: {content}
            
            Provide response in JSON format.
            \"\"\",
            
            'technical': \"\"\"
            Create a technical summary focusing on:
            - Technical specifications or requirements
            - Methodologies or processes described
            - Data, measurements, or calculations
            - Technical conclusions or recommendations
            - Implementation details
            
            Document: {content}
            
            Provide response in JSON format.
            \"\"\"
        }
        
        prompt = summary_prompts.get(summary_type, summary_prompts['executive'])
        formatted_prompt = prompt.format(content=extracted_text[:6000])
        
        summary_response = self.openai_client.generate_completion(
            formatted_prompt,
            max_tokens=1500,
            temperature=0.3
        )
        
        # Parse and structure response
        try:
            summary_data = json.loads(summary_response)
        except json.JSONDecodeError:
            summary_data = {
                'summary_type': summary_type,
                'raw_summary': summary_response,
                'structured': False
            }
        
        summary_data.update({
            'file_path': file_path,
            'summary_type': summary_type,
            'generated_at': datetime.now().isoformat(),
            'document_length': len(extracted_text),
            'confidence': self._estimate_summary_confidence(summary_data)
        })
        
        return summary_data
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        raise PDFProcessingError(f"Failed to generate summary: {e}")
```

#### `analyze_document_sentiment(file_path: str) -> Dict[str, Any]`
**Propósito**: Analisa sentimento e tom do documento.

#### `identify_key_entities(file_path: str) -> Dict[str, Any]`
**Propósito**: Identifica entidades importantes (pessoas, organizações, datas).

### **3. Busca e Extração Inteligente**

#### `intelligent_search(file_path: str, query: str) -> Dict[str, Any]`
**Propósito**: Busca inteligente por informações específicas.

```python
def intelligent_search(self, file_path: str, query: str) -> Dict[str, Any]:
    try:
        # Extract text
        extracted_text = self._extract_text_from_pdf(file_path)
        
        # Perform intelligent search
        search_prompt = f\"\"\"
        Search for information related to: "{query}"
        
        In this document:
        {extracted_text[:5000]}
        
        Provide comprehensive search results in JSON:
        {{
            "query": "{query}",
            "found_information": [
                {{
                    "relevant_text": "exact text snippet",
                    "context": "surrounding context",
                    "relevance_score": 0.95,
                    "page_reference": "estimated page or section"
                }}
            ],
            "summary_answer": "direct answer to the query if found",
            "related_topics": ["list of related topics found"],
            "confidence": 0.87,
            "search_notes": "additional notes about the search"
        }}
        \"\"\"
        
        search_result = self.openai_client.generate_completion(
            search_prompt,
            max_tokens=1200,
            temperature=0.2
        )
        
        # Parse search results
        try:
            parsed_results = json.loads(search_result)
        except json.JSONDecodeError:
            parsed_results = {
                'query': query,
                'raw_response': search_result,
                'parsed': False
            }
        
        parsed_results.update({
            'file_path': file_path,
            'search_timestamp': datetime.now().isoformat(),
            'document_length': len(extracted_text)
        })
        
        return parsed_results
        
    except Exception as e:
        logger.error(f"Intelligent search failed: {e}")
        raise PDFProcessingError(f"Search operation failed: {e}")
```

### **4. Processamento em Lote**

#### `process_multiple_pdfs(file_paths: List[str], analysis_type: str = "basic") -> List[PDFProcessingResult]`
**Propósito**: Processa múltiplos PDFs em lote.

#### `compare_documents(file_path1: str, file_path2: str) -> Dict[str, Any]`
**Propósito**: Compara dois documentos PDF.

### **5. Utilitários de Extração**

#### `_extract_text_from_pdf(file_path: str) -> str`
**Propósito**: Extrai texto bruto do PDF.

```python
def _extract_text_from_pdf(self, file_path: str) -> str:
    try:
        text = ""
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\\n--- Page {page_num + 1} ---\\n"
                        text += page_text
                        text += "\\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
        
        if not text.strip():
            # Try alternative extraction method
            text = self._extract_text_alternative_method(file_path)
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise PDFProcessingError(f"Cannot extract text from PDF: {e}")
```

#### `_get_pdf_metadata(file_path: str) -> Dict[str, Any]`
**Propósito**: Extrai metadados do PDF.

#### `_analyze_pdf_content(text: str, analysis_type: str) -> Dict[str, Any]`
**Propósito**: Realiza análise de IA do conteúdo extraído.

## Classes de Apoio

### **PDFProcessingResult**
```python
@dataclass
class PDFProcessingResult:
    file_path: str
    extracted_text: str
    metadata: Dict[str, Any]
    ai_analysis: Dict[str, Any]
    processing_time: float
    analysis_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'file_path': self.file_path,
            'text_length': len(self.extracted_text),
            'metadata': self.metadata,
            'ai_analysis': self.ai_analysis,
            'processing_time': self.processing_time,
            'analysis_type': self.analysis_type,
            'timestamp': self.timestamp.isoformat()
        }
```

### **PDFProcessingRecord**
```python
@dataclass
class PDFProcessingRecord:
    file_path: str
    operation_type: str
    success: bool
    processing_time: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
```

## Tratamento de Erros

### **Exceções Customizadas**
```python
class PDFProcessingError(Exception):
    """Erro no processamento de PDF"""

class PDFExtractionError(PDFProcessingError):
    """Erro na extração de texto"""

class PDFAnalysisError(PDFProcessingError):
    """Erro na análise de IA"""
```

## Exemplos de Uso

### **Processamento Básico**
```python
from src.ai.pdf_processor_agent import PDFProcessorAgent
from src.ai.openai_client import OpenAIClient

# Initialize
client = OpenAIClient()
pdf_processor = PDFProcessorAgent(client)

# Process PDF
result = pdf_processor.process_pdf_file("document.pdf", "comprehensive")
print(f"Extracted {len(result.extracted_text)} characters")
print(f"AI Analysis: {result.ai_analysis}")
```

### **Extração de Dados Estruturados**
```python
# Extract specific fields
target_fields = ["company_name", "total_revenue", "report_date"]
extracted_data = pdf_processor.extract_structured_data("financial_report.pdf", target_fields)

print(f"Company: {extracted_data['extracted_data']['company_name']}")
print(f"Revenue: {extracted_data['extracted_data']['total_revenue']}")
```

### **Geração de Resumo**
```python
# Generate executive summary
summary = pdf_processor.generate_summary("document.pdf", "executive")
print(f"Summary: {summary}")
```

### **Busca Inteligente**
```python
# Search for specific information
search_results = pdf_processor.intelligent_search(
    "document.pdf", 
    "What are the main financial risks mentioned?"
)

for result in search_results['found_information']:
    print(f"Found: {result['relevant_text']}")
    print(f"Relevance: {result['relevance_score']}")
```

---

**O PDFProcessorAgent transforma documentos PDF em fontes de dados estruturados e insights inteligentes, combinando extração robusta com análise de IA avançada.**