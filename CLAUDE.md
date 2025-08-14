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
- **Required for AI features**: `OPENAI_API_KEY` and `OPENAI_MODEL` (no defaults)
- **AI Provider Options**: `AI_PROVIDER` (openai/openrouter), `AI_BASE_URL`, `AI_PROVIDER_CONFIG`
- **Optional Settings**: Timeout, retry, and performance settings (see `config/settings.py` for all options)

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
2. `BrazilianSitesTerminal` displays menu for 3 supported sites
3. User selection delegates to specific UI classes (`portal_saude_ui.py`, `mds_parcelas_ui.py`, `mds_saldo_ui.py`)
4. UI classes handle user configuration and execute appropriate scrapers
5. Results processed through AI pipeline and saved to organized directory structure

**Site Scraper Architecture**:
- **UI Layer**: Site-specific UI classes with real-time progress tracking via `InteractiveProgressDisplay`
- **Scraper Layer**: Site modules in `src/modules/sites/` implement `execute_scraping(ano, mes, progress_callback=None)` method
- **Processing Layer**: AI-powered PDF analysis and Excel generation via `src/ai/` and `src/utils/`
- **Configuration**: Centralized settings via singleton pattern in `config/settings.py`

**Real-Time UI System**:
- **InteractiveProgressDisplay**: Threaded real-time updates with ANSI cursor control
- **Progress Callbacks**: Scrapers report status changes via callback functions to update UI
- **Synchronization**: Timer and step progression synchronized between scraper and display
- **Animation System**: Loading animations (`.`, `..`, `...`) and PDF download counters

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

### PDF Processing Pipeline
- **PDF to Excel Conversion**: Core feature using `src/utils/pdf_data_to_table.py`
- **AI-Powered Data Extraction**: Uses OpenAI API via `src/ai/pdf_call.py` and `src/ai/openai_client.py`
- **Municipality Name Correction**: AI-powered correction via `src/ai/municipality_corrector.py`
- **Intelligent Filename Parsing**: Resolution numbers extracted from document titles  
- **Excel Output**: Generated via `src/utils/pdf_data_to_table.py`
- **Organized Storage**: Files structured by site/year/month in `downloads/` directory

### AI Integration (Required for PDF Processing)
- **Multiple AI Providers**: Supports OpenAI and OpenRouter via `AI_PROVIDER` environment variable
- **Flexible Configuration**: Base URLs and provider-specific configs via `AI_BASE_URL` and `AI_PROVIDER_CONFIG`
- **Model Configuration**: Configurable via `OPENAI_MODEL` environment variable (no default - must be set)
- **PDF Analysis**: Converts unstructured PDF content to structured Excel data with intelligent field extraction
- **Municipality Correction**: AI-powered correction of municipality names in extracted data
- **Cost Display**: Shows "consultar no API provider" instead of estimates for accurate billing transparency
- **Graceful Degradation**: System works for basic scraping without AI, but PDF processing requires API key

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

## UI Implementation Guidelines

### Interactive Progress System
The system uses a sophisticated real-time UI with threaded updates and progress callbacks:

**InteractiveProgressDisplay Pattern**:
- Thread-safe updates using `threading.Lock()`
- ANSI escape codes for precise cursor positioning (`\033[line;columnH`)
- Real-time timer with decimal minutes format (e.g., "1.5 minutos")
- Step-by-step progress tracking with completion checkmarks

**Progress Callback Integration**:
- Scrapers must support `progress_callback` parameter in `execute_scraping()` method
- Callback stages: `"loading_results"`, `"downloading_pdfs"` with optional current/total counters
- UI updates synchronized with actual scraper progress to prevent display lag

**Logger Silent Mode**:
- Use `logger.enable_silent_mode()` during UI operations to prevent console pollution
- File logging continues normally while console output is suppressed
- Always call `logger.disable_silent_mode()` after UI completion

### Site Scraper Implementation Pattern
When implementing new site scrapers, follow this callback-enabled pattern:

```python
def execute_scraping(self, ano: str, mes: str = None, progress_callback=None) -> Dict[str, Any]:
    # Report progress stages
    if progress_callback:
        progress_callback("loading_results", "Expanding document list")
    
    # Later in download loop
    if progress_callback:
        progress_callback("downloading_pdfs", "Downloading PDFs", current, total)
```

### Time Synchronization
- UI timer and final summary must use same time source via `InteractiveProgressDisplay.get_elapsed_time()`
- Capture elapsed time before calling `progress.stop()` to ensure accuracy
- Pass actual elapsed time to `show_success_screen()` for consistent reporting