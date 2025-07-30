"""
Interactive mode interface for Web Scraper AI.
"""

import time
from typing import Dict, Any, Optional

from src.core.application import WebScraperApplication
from src.models.site_config import SiteConfig, SelectorConfig, DataExtractionRule
from src.models.scraping_task import TaskPriority
from src.utils.logger import logger


class InteractiveMode:
    """Interactive command interface."""
    
    def __init__(self, app: WebScraperApplication):
        self.app = app
        self.commands = {
            '1': self.show_status,
            'status': self.show_status,
            '2': self.show_health,
            'health': self.show_health,
            '3': self.show_metrics,
            'metrics': self.show_metrics,
            '4': self.create_task,
            'create-task': self.create_task,
            '5': self.list_tasks,
            'list-tasks': self.list_tasks,
            '6': self.cleanup,
            'cleanup': self.cleanup,
            '7': self.backup,
            'backup': self.backup,
            '8': self.exit_app,
            'exit': self.exit_app,
            'quit': self.exit_app,
            'help': self.show_help,
            '?': self.show_help
        }
        self.running = True
    
    def run(self) -> int:
        """Run interactive mode."""
        try:
            self._show_welcome()
            
            while self.running:
                self._show_menu()
                choice = input("\n🔧 Enter command: ").strip().lower()
                
                if not choice:
                    continue
                
                try:
                    if choice in self.commands:
                        result = self.commands[choice]()
                        if result is not None:
                            return result
                    else:
                        print("❌ Invalid command. Type 'help' or '?' for available commands.")
                
                except Exception as e:
                    print(f"❌ Error: {e}")
                    logger.error(f"Interactive command error: {e}")
                
                time.sleep(0.5)
            
            return 0
            
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user")
            return 130
        except Exception as e:
            print(f"❌ Interactive mode error: {e}")
            logger.error(f"Interactive mode error: {e}")
            return 1
    
    def _show_welcome(self) -> None:
        """Show welcome message."""
        print("\n🤖 Web Scraper AI - Interactive Mode")
        print("=" * 50)
        print("Welcome to the interactive command interface!")
        print("Type 'help' or '?' for available commands.")
        print("=" * 50)
    
    def _show_menu(self) -> None:
        """Show command menu."""
        print("\n📋 Available Commands:")
        print("━" * 30)
        print("1. status     - Show application status")
        print("2. health     - Show health check")
        print("3. metrics    - Show performance metrics")
        print("4. create-task - Create a scraping task")
        print("5. list-tasks - List all tasks")
        print("6. cleanup    - Run maintenance cleanup")
        print("7. backup     - Create system backup")
        print("8. exit       - Exit application")
        print("━" * 30)
        print("💡 Tip: You can use numbers or command names")
    
    def show_help(self) -> None:
        """Show detailed help."""
        print("\n📖 Detailed Help:")
        print("━" * 40)
        print("🔍 status     - Display current application status,")
        print("                engine state, and active tasks")
        print("🏥 health     - Perform health check on all components")
        print("📊 metrics    - Show performance metrics and statistics")
        print("🚀 create-task - Create and submit a new scraping task")
        print("📋 list-tasks - Display active and completed tasks")
        print("🧹 cleanup    - Run maintenance cleanup operations")
        print("💾 backup     - Create backup of system data")
        print("🚪 exit       - Gracefully shutdown and exit")
        print("━" * 40)
        print("📝 You can also use shortcuts like 'q' for quit")
    
    def show_status(self) -> None:
        """Show application status."""
        try:
            status = self.app.get_application_status()
            
            print("\n📊 Application Status:")
            print("━" * 35)
            print(f"🔧 Initialized: {'✅ Yes' if status['initialized'] else '❌ No'}")
            print(f"▶️  Running: {'✅ Yes' if status['running'] else '❌ No'}")
            print(f"🌐 Site Configs: {status['site_configs_loaded']}")
            
            if status['engine_status']:
                engine = status['engine_status']
                print(f"⚙️  Engine Status: {engine['status'].upper()}")
                print(f"🔄 Active Tasks: {engine['active_tasks']}")
                print(f"📦 Queue Size: {engine['queue_size']}")
                print(f"✅ Completed Tasks: {engine['completed_tasks']}")
            
            # Component status
            components = status.get('components', {})
            print("\n🔧 Components:")
            for component, available in components.items():
                icon = "✅" if available else "❌"
                print(f"  {icon} {component.replace('_', ' ').title()}")
                
        except Exception as e:
            print(f"❌ Failed to get status: {e}")
    
    def show_health(self) -> None:
        """Show health check results."""
        try:
            health = self.app.health_check()
            
            print("\n🏥 Health Check Results:")
            print("━" * 35)
            
            overall_icon = "✅" if health['status'] == 'healthy' else "❌"
            print(f"{overall_icon} Overall Status: {health['status'].upper()}")
            print(f"🕐 Checked at: {health['timestamp']}")
            
            if 'components' in health:
                print("\n🔧 Component Health:")
                for component, info in health['components'].items():
                    status_icon = "✅" if info.get('healthy', True) else "❌"
                    component_name = component.replace('_', ' ').title()
                    status_text = info.get('status', 'unknown')
                    print(f"  {status_icon} {component_name}: {status_text}")
            
        except Exception as e:
            print(f"❌ Failed to get health status: {e}")
    
    def show_metrics(self) -> None:
        """Show performance metrics."""
        try:
            metrics = self.app.get_metrics()
            
            print("\n📈 Performance Metrics:")
            print("━" * 35)
            
            if 'engine' in metrics:
                engine = metrics['engine']
                print(f"✅ Tasks Completed: {engine.get('tasks_completed', 0)}")
                print(f"❌ Tasks Failed: {engine.get('tasks_failed', 0)}")
                print(f"📊 Success Rate: {engine.get('success_rate', 0):.2%}")
                print(f"⏱️  Average Time: {engine.get('average_task_time', 0):.2f}s")
                print(f"🕐 Uptime: {engine.get('uptime_seconds', 0):.0f}s")
            
            if 'storage' in metrics:
                storage = metrics['storage']
                total_files = storage.get('total_files', 0)
                total_size_mb = storage.get('total_size', 0) / (1024 * 1024)
                print(f"\n💾 Storage:")
                print(f"📁 Total Files: {total_files}")
                print(f"💿 Total Size: {total_size_mb:.2f} MB")
            
        except Exception as e:
            print(f"❌ Failed to get metrics: {e}")
    
    def create_task(self) -> None:
        """Create a new scraping task."""
        try:
            print("\n🚀 Creating Example Scraping Task...")
            print("━" * 40)
            
            # Create example site config
            example_config = self._create_example_site_config()
            self.app.add_site_config(example_config)
            
            # Create task
            task = self.app.create_scraping_task(
                site_name='example_site',
                priority=TaskPriority.NORMAL
            )
            
            print(f"✅ Task Created Successfully!")
            print(f"🆔 Task ID: {task.task_id}")
            print(f"🌐 Site: {task.site_config_name}")
            print(f"📅 Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⚡ Priority: {task.priority.name}")
            
        except Exception as e:
            print(f"❌ Failed to create task: {e}")
    
    def list_tasks(self) -> None:
        """List all tasks."""
        try:
            if not self.app.engine:
                print("❌ Engine not available")
                return
            
            active_tasks = self.app.engine.get_active_tasks()
            completed_tasks = self.app.engine.get_completed_tasks()
            
            print("\n📋 Task List:")
            print("━" * 35)
            print(f"🔄 Active Tasks: {len(active_tasks)}")
            print(f"✅ Completed Tasks: {len(completed_tasks)}")
            
            if active_tasks:
                print("\n🔄 Active Tasks:")
                for task_id, task in list(active_tasks.items())[:5]:
                    status_icon = "🔄" if task.status.name == "IN_PROGRESS" else "⏸️"
                    print(f"  {status_icon} {task_id[:8]}... - {task.status.value}")
            
            if completed_tasks:
                print("\n✅ Recent Completed Tasks:")
                for task_id, task in list(completed_tasks.items())[:5]:
                    status_icon = "✅" if task.status.name == "COMPLETED" else "❌"
                    completion_time = task.updated_at.strftime('%H:%M:%S')
                    print(f"  {status_icon} {task_id[:8]}... - {task.status.value} ({completion_time})")
            
            if not active_tasks and not completed_tasks:
                print("📭 No tasks found")
                
        except Exception as e:
            print(f"❌ Failed to list tasks: {e}")
    
    def cleanup(self) -> None:
        """Run maintenance cleanup."""
        try:
            print("\n🧹 Running Maintenance Cleanup...")
            print("━" * 40)
            
            results = self.app.cleanup_old_data()
            
            print("✅ Cleanup Completed Successfully!")
            
            if 'temp_cleanup' in results:
                temp = results['temp_cleanup']
                print(f"🗑️  Temp Files: {temp.get('deleted_files', 0)} files deleted")
                print(f"💾 Space Freed: {temp.get('freed_bytes', 0) / (1024*1024):.2f} MB")
            
            if 'archive' in results:
                archive = results['archive']
                print(f"📦 Archived: {archive.get('archived_files', 0)} files")
            
            if 'old_tasks_removed' in results:
                print(f"🗂️  Old Tasks: {results['old_tasks_removed']} removed from memory")
                
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
    
    def backup(self) -> None:
        """Create system backup."""
        try:
            print("\n💾 Creating System Backup...")
            print("━" * 35)
            
            backup_info = self.app.create_backup("Interactive mode backup")
            
            print("✅ Backup Created Successfully!")
            print(f"🆔 Backup ID: {backup_info['backup_id']}")
            print(f"📁 Files: {backup_info['file_count']}")
            print(f"💿 Size: {backup_info['total_size'] / (1024*1024):.2f} MB")
            print(f"📅 Created: {backup_info['created_at']}")
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
    
    def exit_app(self) -> int:
        """Exit the application."""
        print("\n👋 Exiting Web Scraper AI...")
        print("Thank you for using our application!")
        self.running = False
        return 0
    
    def _create_example_site_config(self) -> SiteConfig:
        """Create an example site configuration."""
        # Create selectors
        title_selector = SelectorConfig(
            type='css',
            value='h1.title',
            wait_condition='presence'
        )
        
        description_selector = SelectorConfig(
            type='css',
            value='.description p',
            wait_condition='presence'
        )
        
        # Create extraction rules
        title_rule = DataExtractionRule(
            name='title',
            selector=title_selector,
            data_type='text',
            required=True
        )
        
        description_rule = DataExtractionRule(
            name='description',
            selector=description_selector,
            data_type='text',
            required=False,
            default_value='No description available'
        )
        
        # Create site configuration
        site_config = SiteConfig(
            name='example_site',
            base_url='https://example.com',
            description='Example site for demonstration',
            extraction_rules=[title_rule, description_rule],
            wait_time=5.0,
            timeout=30.0,
            retry_attempts=3
        )
        
        return site_config