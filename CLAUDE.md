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
```bash
python test_filename_extraction.py
```
Tests the filename extraction logic for Portal Saude MG PDFs.

Note: The main test file `test_all_scrapers.py` has been deleted but was previously used for comprehensive scraper testing.

### Environment Setup
- Copy `.env.example` to `.env` (if available) 
- Set `OPENAI_API_KEY` for AI features (optional - system works without it)
- Configure timeout and retry settings via environment variables

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
1. **Portal Saude MG** (`portal_saude_mg.py`) - PDF downloads from health department
2. **MDS Parcelas Pagas** (`mds_parcelas.py`) - Municipal payment data 
3. **MDS Saldo Detalhado** (`mds_saldo.py`) - Detailed account balance data

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
2. Command line arguments (through terminal interface)
3. Default values in `config/settings.py`

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
- **Portal Saude MG**: Direct HTTP access, no authentication required
- **MDS Sites**: Require authentication for full data access (currently does interface analysis only)
- All scrapers respect rate limiting and robots.txt guidelines

### PDF Processing
- PDFs are downloaded with intelligent filename extraction
- Resolution numbers are parsed from document titles
- Files organized by year/month structure automatically

### AI Integration (Optional)
- OpenAI integration available but not required for core functionality
- Used for enhanced content analysis when API key is provided
- System degrades gracefully without AI features

### Memory and Performance
- Uses streaming downloads for large files
- Implements retry logic with exponential backoff
- Monitors system resources during scraping operations

### Brazilian Government Site Compliance
- Designed specifically for Brazilian government transparency data
- Respects site terms of service and rate limits
- Only accesses publicly available information
- Implements proper delay between requests