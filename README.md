# BGDSS - Brazilian Government Data Scraping System

A Python application for automated data extraction from Brazilian government websites with AI-powered PDF processing.

## Overview

BGDSS (Brazilian Government Data Scraping System) extracts data from Brazilian government websites and processes PDF documents using AI to generate structured Excel files. The system includes a terminal-based interface for site selection and configuration.

## Requirements

- Python 3.8+
- OpenAI API key (optional, for AI PDF processing)
- Chrome/Chromium browser (for web scraping)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure OpenAI API key (optional):
   ```bash
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Supported Sites

The system currently supports 3 government sites, with different implementation status:

### 1. Portal Saude MG - Health Resolutions (WORKING)
- **URL**: https://portal-antigo.saude.mg.gov.br/deliberacoes
- **Status**: Fully implemented and functional
- **Data Type**: PDF resolutions and deliberations
- **Features**: Complete scraping, AI PDF processing, Excel generation

### 2. MDS Parcelas Pagas - Municipal Payments (NOT IMPLEMENTED)
- **Status**: Interface exists but scraping logic not implemented
- **Data Type**: Municipal payment installments
- **Note**: Requires development

### 3. MDS Saldo Detalhado - Account Balances (NOT IMPLEMENTED) 
- **Status**: Interface exists but scraping logic not implemented
- **Data Type**: Detailed account balance information
- **Note**: Requires development

## Features

### Web Scraping
- Automated PDF downloading from government sites
- Configurable filters (year, month)
- Error handling and retry logic
- Sequential file naming

### AI Processing (Optional)
- PDF text extraction using OpenAI API
- Structured data extraction from government resolutions
- Automatic categorization based on budget allocation codes
- Excel file generation with processed data

### Data Output
The system extracts the following information from PDF resolutions:
- Resolution number
- Related resolutions
- Resolution object/purpose
- Initial date
- Execution deadline
- Usage restrictions
- Budget allocation
- Direct link to source PDF
- Automatic category classification

## Usage

1. Run `python main.py`
2. Select a government site from the menu
3. Configure extraction parameters (year, month)
4. The system will:
   - Download PDFs from the selected site
   - Process PDFs with AI (if API key configured)
   - Generate Excel file with structured data

## Project Structure

```
src/
├── ai/                     # AI processing modules
├── modules/sites/          # Site-specific scrapers
├── ui/                     # Terminal interface
├── utils/                  # Utilities and logging
config/                     # Configuration files
downloads/                  # Downloaded and processed files
logs/                       # Application logs
```

## Configuration

The system uses environment variables for configuration:
- `OPENAI_API_KEY`: Required for AI PDF processing
- `LOG_LEVEL`: Logging level (default: INFO)
- Various timeout and retry settings

## Notes

- AI processing requires an OpenAI API key and will consume tokens
- The system respects robots.txt and implements rate limiting
- Only Portal Saude MG is currently fully functional
- Excel files include both original data and AI-processed categorizations

## License

MIT License - see LICENSE file for details.