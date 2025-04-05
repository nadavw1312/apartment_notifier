import json
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.db.sql_database import SQL_DB_MANAGER
from src.services.scraper.scraper_users_bl import (
    create_facebook_scraper_user,
    save_facebook_session_data,
    get_facebook_session_data,
    get_active_facebook_users,
    set_facebook_user_active,
    get_scraper_user_by_email_source
)
from dataclasses import dataclass
from src.workers.facebook.facebook_group_scraper import FacebookGroupScraper
from src.workers.facebook.shared_browser_manager import SharedBrowserManager
import logging

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ScraperGroupConfig:
    """Configuration for a single Facebook group to scrape"""
    group_id: str
    name: str
    config: Dict[str, Any]

@dataclass
class ScraperUserConfig:
    """Configuration for a Facebook user with groups to scrape"""
    email: str
    password: str
    active: bool
    groups: List[ScraperGroupConfig]

class FacebookScraperManager:
    """
    Manager class for Facebook group scrapers that handles multiple users
    and their group configurations. Implements SOLID principles for maintainability.
    """
    
    CONFIG_PATH = "src/workers/facebook/scraper_config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Facebook scraper manager
        
        Args:
            config_path: Optional path to config file. If not provided, uses default path.
        """
        self.config_path = config_path or self.CONFIG_PATH
        self.config = self._load_config()
        self.system_defaults = self.config.get("system_defaults", {})
        self.users = self._parse_user_configs()
        self.scrapers = {}
        self.browser_manager = SharedBrowserManager
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if not os.path.exists(self.config_path):
                print(f"⚠️ Config file not found at {self.config_path}")
                return {"users": [], "system_defaults": {}}
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading config: {e}")
            return {"users": [], "system_defaults": {}}
    
    def _parse_user_configs(self) -> List[ScraperUserConfig]:
        """Parse user configurations from loaded config"""
        users = []
        
        for user_data in self.config.get("users", []):
            # Parse group configurations
            groups = []
            for group_data in user_data.get("groups", []):
                # Merge group config with system defaults only
                group_config = self.system_defaults.copy()
                group_config.update(group_data.get("config", {}))
                
                groups.append(ScraperGroupConfig(
                    group_id=group_data.get("group_id", ""),
                    name=group_data.get("name", "Unknown Group"),
                    config=group_config
                ))
            
            # Create user config
            users.append(ScraperUserConfig(
                email=user_data.get("email", ""),
                password=user_data.get("password", ""),
                active=user_data.get("active", False),
                groups=groups
            ))
        
        return users
    
    def get_active_users(self) -> List[ScraperUserConfig]:
        """Get all active users from config"""
        return [user for user in self.users if user.active]
    
    async def ensure_user_session(self, user: ScraperUserConfig) -> bool:
        """
        Ensure the user has a valid Facebook session in the database
        
        Args:
            user: User configuration
            
        Returns:
            bool: True if session exists or was created, False otherwise
        """
        # Initialize database session
        async with SQL_DB_MANAGER.get_session_with_transaction() as db_session:
            # Check if user has a session in the database
            session_data = await get_facebook_session_data(db_session, user.email)
            
            if session_data:
                print(f"✅ [{user.email}] Found existing session in database")
                return True
            
            print(f"🔐 [{user.email}] Session not found. Creating new session...")
            
            try:
                # Create session with user credentials if available
                if user.email and user.password:
                    # Create or update user in database
                    await create_facebook_scraper_user(db_session, user.email, user.password)
                    
                    # Create Facebook session and get data directly as dictionary
                    session_data = await FacebookGroupScraper.create_facebook_session(
                        email=user.email,
                        password=user.password
                    )
                else:
                    # Create session without credentials
                    session_data = await FacebookGroupScraper.create_facebook_session()
                
                # Save session data to database
                await save_facebook_session_data(db_session, user.email, session_data)
                
                return True
            except Exception as e:
                print(f"⚠️ [{user.email}] Failed to create session: {e}")
                return False
    
    async def run_user_scrapers(self, user: ScraperUserConfig, max_cycles: Optional[int] = None):
        """
        Run scrapers for all groups for a specific user
        
        Args:
            user: User configuration
            max_cycles: Optional maximum number of cycles to run
        """
        # Initialize database
        await SQL_DB_MANAGER.init()
        
        # First, ensure user has a valid session
        if not await self.ensure_user_session(user):
            print(f"❌ [{user.email}] Cannot run scrapers without valid session")
            return
        
        # Get session data from database
        session_data = None
        async with SQL_DB_MANAGER.get_session_with_transaction() as db_session:
            # Get the session data from database
            session_data = await get_facebook_session_data(db_session, user.email)
            
            if not session_data:
                print(f"❌ [{user.email}] No session data found in database")
                return
        
        try:
            # Create scrapers for each group
            scrapers = []
            for group in user.groups:
                print(f"🔄 [{user.email}] Creating scraper for group: {group.name} ({group.group_id})")
                scraper = FacebookGroupScraper(group.group_id, group.config)
                scrapers.append(scraper)
            
            # Initialize all scrapers with session data
            print(f"🔄 Initializing scrapers with shared browser for user {user.email}...")
            for scraper in scrapers:
                await scraper.initialize_with_session_data(session_data, user.email)
            
            # Run all scrapers simultaneously
            await asyncio.gather(*[scraper.run(max_cycles) for scraper in scrapers])
            
        except Exception as e:
            print(f"⚠️ [{user.email}] Error running scrapers: {e}")
        
        finally:
            # Clean up all scrapers
            for scraper in scrapers:
                await scraper.cleanup()
            
            # Make sure shared browser is fully cleaned up for this user
            await self.browser_manager.cleanup_user(user.email)
            
            # Close the database
            await SQL_DB_MANAGER.close()
    
    async def run_all_active_users(self, max_cycles: Optional[int] = None):
        """
        Run scrapers for all active users from config
        
        Args:
            max_cycles: Optional maximum number of cycles to run
        """
        # Initialize database
        await SQL_DB_MANAGER.init()
        
        try:
            # Get active users
            active_users = self.get_active_users()
            
            if not active_users:
                print("⚠️ No active users found in config")
                return
            
            # Run scrapers for each user
            for user in active_users:
                await self.run_user_scrapers(user, max_cycles)
            
        except Exception as e:
            print(f"⚠️ Error running active users: {e}")
        
        finally:
            # Final cleanup of all shared browser resources
            await self.browser_manager.cleanup()
            # Close the database
            await SQL_DB_MANAGER.close()
    
    async def run_db_users(self, max_cycles: Optional[int] = None):
        """
        Run scrapers for all active users from database
        
        Args:
            max_cycles: Optional maximum number of cycles to run
        """
        # Initialize database
        await SQL_DB_MANAGER.init()
        
        try:
            # Get active users from database
            session_gen = SQL_DB_MANAGER.get_session()
            active_users = []
            
            # Use async for to properly consume the session generator
            async for session in session_gen:
                active_users = await get_active_facebook_users(session)
            
            if not active_users:
                print("⚠️ No active users found in database")
                return
            
            print(f"✅ Found {len(active_users)} active users in database")
            
            # Run scrapers for each user
            for user in active_users:
                try:
                    print(f"🔄 Running scrapers for user: {user.email}")
                    
                    # Convert database user to config user format
                    # This will let us reuse the run_user_scrapers method
                    user_config = ScraperUserConfig(
                        email=user.email,
                        # Ensure password is a string - use empty string if None
                        password=user.password or "",
                        active=True,
                        groups=[
                            # Apply system defaults to all groups
                            ScraperGroupConfig(
                                group_id=group_id,
                                name=f"Group {group_id}",
                                config=self.system_defaults.copy()
                            )
                            for group_id in self.system_defaults.get("group_ids", [])
                        ]
                    )
                    
                    # Run scrapers for this user
                    await self.run_user_scrapers(user_config, max_cycles)
                    
                except Exception as user_error:
                    print(f"⚠️ Error processing user {user.email}: {user_error}")
                    continue
        
        except Exception as e:
            print(f"⚠️ Error running database users: {e}")
        
        finally:
            # Final cleanup of all shared browser resources
            await self.browser_manager.cleanup()
            # Close the database
            await SQL_DB_MANAGER.close()
            
    async def sync_config_users_to_db(self):
        """
        Synchronize users from configuration file to database.
        
        This method:
        1. Creates users in the database if they don't exist in the scraper_config.json
        2. Updates existing users' active status
        3. Ensures all configuration users are properly represented in the database
        
        This should be run before starting the scrapers to ensure all users are properly
        initialized in the database.
        """
        # Initialize database
        await SQL_DB_MANAGER.init()
        
        try:
            # Process each user in the configuration
            for user_config in self.users:
                print(f"🔄 Syncing user: {user_config.email}")
                
                async with SQL_DB_MANAGER.get_session_with_transaction() as db_session:
                    # Check if user exists in database
                    user_exists = await get_scraper_user_by_email_source(db_session, user_config.email, "facebook")
                    
                    if user_exists:
                        print(f"✅ User {user_config.email} exists in database")
                        # User exists, update active status if needed
                        await set_facebook_user_active(db_session, user_config.email, user_config.active)
                    else:
                        print(f"➕ Creating new user: {user_config.email}")
                        # Create new user in database
                        await create_facebook_scraper_user(
                            db_session, 
                            user_config.email, 
                            user_config.password,
                            is_active=user_config.active
                        )
                        
                print(f"✅ Synced user: {user_config.email}")
                
            print("✅ All users synchronized successfully")
                
        except Exception as e:
            print(f"⚠️ Error synchronizing users: {e}")
        finally:
            # Close the database
            await SQL_DB_MANAGER.close()

    async def cleanup_user(self, user_email):
        """Clean up resources for a specific user"""
        # Any cleanup code that uses SharedBrowserManager directly
        await self.browser_manager.cleanup_user(user_email)
    
    async def cleanup(self):
        """Clean up all resources"""
        # Any cleanup code that uses SharedBrowserManager directly
        await self.browser_manager.cleanup()

async def main():
    """Main function to run the Facebook scraper manager"""
    manager = FacebookScraperManager()
    
    # First, synchronize configuration users with database
    print("🔄 Synchronizing configuration users with database...")
    await manager.sync_config_users_to_db()
    
    # Then run the scrapers
    print("🚀 Starting scrapers for all active users...")
    await manager.run_all_active_users()

async def init_config():
    """Initialize configuration users in the database without running scrapers"""
    manager = FacebookScraperManager()
    
    print("🔄 Initializing configuration users in database...")
    await manager.sync_config_users_to_db()
    print("✅ Configuration initialization complete")

if __name__ == "__main__":
    asyncio.run(main()) 