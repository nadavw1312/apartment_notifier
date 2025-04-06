"""
Centralized runner for multiple web scrapers.
Loads configuration from a single file and runs all configured scrapers.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.db.sql_database import SQL_DB_MANAGER
from src.workers.scrapers.init_scrapers import init_from_central_config
# Import scraper managers
from src.workers.scrapers.facebook.facebook_scraper_manager import FacebookScraperManager
# Future imports for other platforms would go here
# from src.workers.scrappers.other_platform.other_platform_manager import OtherPlatformManager

# Default location for the configuration file
DEFAULT_CONFIG_PATH = Path("config/scraper_config.json")

class ScraperRunner:
    """Main runner class that manages all platform scraper managers."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the scraper runner with configuration
        
        Args:
            config_path: Path to the configuration file, uses default if None
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self.managers = []
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the configuration file
        
        Returns:
            Dictionary containing the configuration
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"✅ Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            print(f"⚠️ Error loading configuration: {e}")
            print("Using default configuration...")
            raise e
    
    
    async def initialize_managers(self):
        """Initialize all enabled platform managers from the configuration"""
        # Get global settings
        global_settings = self.config.get("global", {})
        
        # Initialize Facebook manager if enabled
        if self.config.get("facebook", {}).get("enabled", False):
            try:
                print("🔄 Initializing Facebook scraper manager")
                
                # Create Facebook manager instance
                facebook_manager = FacebookScraperManager()
                
                # Add to managers list
                self.managers.append(facebook_manager)
                print("✅ Added Facebook scraper manager")
            except Exception as e:
                print(f"⚠️ Error initializing Facebook scraper manager: {e}")
        
        print(f"✅ Initialized {len(self.managers)} platform managers")
    
    async def run_managers(self):
        """Run all initialized platform managers"""
        if not self.managers:
            print("⚠️ No platform managers initialized, nothing to run")
            return
        
        print(f"🚀 Starting {len(self.managers)} platform managers")
        tasks = []
        
        for manager in self.managers:
            # Start each manager by calling its run_db_users method
            task = asyncio.create_task(manager.run_db_users())
            tasks.append(task)
        
        # Wait for all managers to complete
        await asyncio.gather(*tasks)
    
    async def cleanup_managers(self):
        """Cleanup all platform managers properly"""
        for manager in self.managers:
            try:
                if hasattr(manager, 'cleanup') and callable(manager.cleanup):
                    await manager.cleanup()
            except Exception as e:
                print(f"⚠️ Error cleaning up manager: {e}")
        
        print("✅ All platform managers cleaned up")

async def main():
    """Main entry point to run all platform managers"""
    try:
        # Initialize database once
        await SQL_DB_MANAGER.init() 
        
        # Create runner with default configuration
        runner = ScraperRunner()
        
        # Initialize and run platform managers
        await init_from_central_config()
        await runner.initialize_managers()
        await runner.run_managers()
    except Exception as e:
        print(f"⚠️ Error running platform managers: {e}")
        await SQL_DB_MANAGER.close()

if __name__ == "__main__":
    asyncio.run(main()) 