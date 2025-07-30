"""
Command Line Interface for Web Scraper AI application.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.core.application import app
from src.utils.logger import logger


class CLIInterface:
    """Command Line Interface handler."""
    
    def __init__(self):
        self.parser = self._create_parser()
        self.args = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser."""
        parser = argparse.ArgumentParser(
            description='Web Scraper AI Application',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py --mode interactive --workers 5
  python main.py --mode daemon --config /path/to/config.json
  python main.py --log-level DEBUG --workers 2
            """
        )
        
        # Mode selection
        parser.add_argument(
            '--mode', 
            choices=['interactive', 'advanced', 'daemon'], 
            default='advanced',
            help='Run mode: interactive (basic), advanced (rich UI), daemon (background) (default: advanced)'
        )
        
        # Configuration
        parser.add_argument(
            '--config', 
            type=str, 
            help='Configuration file path'
        )
        
        # Performance
        parser.add_argument(
            '--workers', 
            type=int, 
            default=3, 
            help='Number of worker threads (default: 3)'
        )
        
        # Logging
        parser.add_argument(
            '--log-level', 
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
            default='INFO',
            help='Log level (default: INFO)'
        )
        
        # Development options
        parser.add_argument(
            '--dev', 
            action='store_true',
            help='Enable development mode with additional logging'
        )
        
        parser.add_argument(
            '--no-ai', 
            action='store_true',
            help='Disable AI components for testing'
        )
        
        return parser
    
    def parse_arguments(self, args: Optional[list] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        self.args = self.parser.parse_args(args)
        return self.args
    
    def configure_application(self) -> None:
        """Configure the application based on parsed arguments."""
        if not self.args:
            raise ValueError("Arguments not parsed yet. Call parse_arguments() first.")
        
        # Configure engine workers
        if hasattr(app, 'application_config'):
            if 'engine' not in app.application_config:
                app.application_config['engine'] = {}
            app.application_config['engine']['max_workers'] = self.args.workers
        
        # Configure AI components
        if self.args.no_ai:
            if hasattr(app, 'application_config'):
                if 'ai' not in app.application_config:
                    app.application_config['ai'] = {}
                app.application_config['ai'].update({
                    'enable_openai': False,
                    'enable_navigator': False,
                    'enable_pdf_processor': False
                })
        
        # Configure development mode
        if self.args.dev:
            logger.info("Development mode enabled")
            # Additional dev configurations can be added here
        
        logger.info(f"Application configured - Workers: {self.args.workers}, Mode: {self.args.mode}")
    
    def initialize_application(self) -> None:
        """Initialize the application."""
        try:
            logger.info("Initializing Web Scraper AI Application...")
            
            app.initialize()
            app.start()
            
            logger.info("✅ Application started successfully!")
            
        except Exception as e:
            logger.error(f"Application initialization failed: {e}")
            raise
    
    def run(self, args: Optional[list] = None) -> int:
        """Main CLI run method."""
        try:
            # Parse arguments
            self.parse_arguments(args)
            
            # Show startup banner
            self._show_banner()
            
            # Configure application
            self.configure_application()
            
            # Initialize application
            self.initialize_application()
            
            # Run appropriate mode
            if self.args.mode == 'interactive':
                from src.ui.interactive_mode import InteractiveMode
                interactive = InteractiveMode(app)
                return interactive.run()
            
            elif self.args.mode == 'advanced':
                from src.ui.advanced_interactive import AdvancedInteractiveMode
                advanced = AdvancedInteractiveMode(app)
                return advanced.run()
            
            elif self.args.mode == 'daemon':
                from src.ui.daemon_mode import DaemonMode
                daemon = DaemonMode(app)
                return daemon.run()
            
            else:
                logger.error(f"Unknown mode: {self.args.mode}")
                return 1
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            return 130  # Standard exit code for Ctrl+C
            
        except Exception as e:
            logger.error(f"CLI error: {e}")
            return 1
            
        finally:
            self._cleanup()
    
    def _show_banner(self) -> None:
        """Show application startup banner."""
        print("🤖 Web Scraper AI Application")
        print("=" * 40)
        print(f"Mode: {self.args.mode}")
        print(f"Workers: {self.args.workers}")
        print(f"Log Level: {self.args.log_level}")
        if self.args.dev:
            print("Development Mode: Enabled")
        if self.args.no_ai:
            print("AI Components: Disabled")
        print("=" * 40)
    
    def _cleanup(self) -> None:
        """Cleanup resources."""
        try:
            if app.is_running:
                logger.info("Shutting down application...")
                app.stop()
                logger.info("✅ Application stopped")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global CLI interface instance
cli = CLIInterface()