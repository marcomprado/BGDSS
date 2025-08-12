# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
python main.py
```
Main entry point that launches the terminal interface for Brazilian government sites scraping.

### Installing Dependencies
```bash
pip install -r requirements.txt
```
Install all required dependencies including Selenium, OpenAI, pandas, and web scraping libraries.

### Testing Individual Components
Currently no active test files in the repository (test files have been removed from working directory).

**Development Testing Approach**:
- Use `python main.py` and manually test specific site scrapers through the terminal interface
- Check logs in `logs/` directory for debugging
- Verify PDF processing with AI by checking `downloads/processed/` output

### Environment Setup
- Create `.env` file in project root (no example file exists)
- Set `OPENAI_API_KEY` for AI features (optional - system works without it)
- Configure timeout and retry settings via environment variables (see `config/settings.py` for all available options)

## Architecture Overview

### Core Architecture Pattern
This is a **modular scraping system** with site-specific scrapers that inherit common functionality:

- **Terminal Interface**: `src/ui/terminal.py` - Interactive CLI for site selection and configuration
- **Site Modules**: `src/modules/sites/` - Individual scrapers for each government site
- **Configuration**: Centralized settings management with environment variable support
- **Logging**: Comprehensive logging system with file rotation

### Key Components

**Main Application Flow**:
1. `main.py` → `src.ui.terminal.run_brazilian_sites_terminal()`
2. Terminal shows menu for 3 supported sites
3. User configures filters (year, month, municipality)
4. Appropriate scraper module is imported and executed
5. Results are processed and saved to organized directory structure

**Site Scraper Pattern**:
Each scraper in `src/modules/sites/` follows this pattern:
- `execute_scraping(config)` - Main entry point
- Site-specific HTTP requests and parsing logic
- Returns standardized result dictionary with success/failure status

**Supported Government Sites**:
1. **Portal Saude MG** (`portal_saude_mg.py`) - Health resolutions PDFs (fully implemented)
2. **MDS Parcelas Pagas** (`mds_parcelas.py`) - Municipal payment data (UI only)
3. **MDS Saldo Detalhado** (`mds_saldo.py`) - Detailed account balance data (UI only)

### Directory Structure and Data Flow

**Downloads Organization**:
```
downloads/
├── raw/                    # Raw downloaded files
├── processed/              # Processed/converted files  
├── temp/                   # Temporary files during processing
└── [site-specific]/        # Organized by site, year, month
```

**Configuration Hierarchy**:
1. Environment variables (.env file)
2. Site-specific configuration in `config/sites_config.json`
3. Command line arguments (through terminal interface)  
4. Default values in `config/settings.py`

### WebDriver Configuration
- Uses Selenium WebDriver with Chrome
- Configuration in `config/webdriver_config.py`
- Includes stealth options to avoid bot detection
- Automatic driver management via webdriver-manager

### Error Handling and Logging
- Custom exceptions in `src/utils/exceptions.py`
- Comprehensive logging in `src/utils/logger.py` 
- Logs saved to `logs/` directory with date-based rotation
- Graceful handling of site unavailability and authentication requirements

## Important Implementation Notes

### Site-Specific Behavior
- **Portal Saude MG**: Direct HTTP access, downloads PDFs, full AI processing to Excel
- **MDS Sites**: Require developing (currently does not exist)
- All scrapers respect rate limiting and robots.txt guidelines

### Implementation Status
- **Portal Saude MG**: Fully implemented with PDF processing and Excel export
- **MDS Sites**: UI components exist but scraping logic requires implementation
- **PDF Processing**: Complete AI-powered extraction pipeline implemented
- **Testing**: Manual testing through terminal interface (no automated test suite)

### PDF Processing
- **PDF to Excel Conversion**: Core feature using `src/modules/pdf_data_to_table.py`
- **AI-Powered Data Extraction**: Uses OpenAI API via `src/ai/pdf_call.py` and `src/ai/openai_client.py`
- **Intelligent Filename Parsing**: Resolution numbers extracted from document titles  
- **Excel Output**: Generated via `src/modules/pdf_data_to_table.py`
- **Organized Storage**: Files structured by site/year/month in `downloads/` directory

### AI Integration (Required for PDF Processing)
- **OpenAI API**: Essential for PDF data extraction to Excel format
- **Models Used**: gpt-4-turbo-preview by default (configurable via `OPENAI_MODEL` env var)
- **PDF Analysis**: Converts unstructured PDF content to structured Excel data
- **Graceful Degradation**: System works for basic scraping without AI, but PDF processing requires OpenAI API key

### Memory and Performance
- Uses streaming downloads for large files
- Implements retry logic with exponential backoff
- Monitors system resources during scraping operations

### Brazilian Government Site Compliance
- Designed specifically for Brazilian government transparency data
- Respects site terms of service and rate limits
- Only accesses publicly available information
- Implements proper delay between requests
- Name of the project is BGDSS - Brazilian Government Data Scraping System