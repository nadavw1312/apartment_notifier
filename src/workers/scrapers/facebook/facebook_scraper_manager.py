"""
Facebook-specific implementation of the BaseScraperManager class.
"""
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Type, cast
import json

from src.db.sql_database import SQL_DB_MANAGER
from src.services.scraper_users.scraper_users_bl import ScraperUserBL
from src.workers.scrapers.base.base_scraper_manager import BaseScraperManager, SourceConfig
from src.workers.scrapers.facebook.facebook_group_scraper import FacebookGroupScraper
from playwright.async_api import async_playwright, StorageState
from src.workers.scrapers.base.browser_manager import SharedBrowserManager

@dataclass
class FacebookGroupConfig(SourceConfig):
    """Configuration for a single Facebook group to scrape"""
    group_id: str
    name: str
    config: Dict[str, Any]

@dataclass
class FacebookUserConfig:
    """Configuration for a Facebook user with groups to scrape"""
    email: str
    password: str
    active: bool
    groups: List[FacebookGroupConfig]

class FacebookScraperManager(BaseScraperManager[FacebookGroupScraper, FacebookUserConfig, FacebookGroupConfig]):
    """
    Manager class for Facebook group scrapers that handles multiple users
    and their group configurations.
    """
    
    CONFIG_PATH = "config/scraper_config.json"
    
    def __init__(self):
        """Initialize the Facebook scraper manager"""
        super().__init__()
        self._browser_manager = SharedBrowserManager()
    
    def _parse_user_configs(self) -> List[FacebookUserConfig]:
        """Parse user configurations from loaded config"""
        users = []
        
        for user_data in self.config.get("users", []):
            # Parse group configurations
            groups = []
            for group_data in user_data.get("groups", []):
                # Merge group config with system defaults only
                group_config = self.system_defaults.copy()
                group_config.update(group_data.get("config", {}))
                
                # Create FacebookGroupConfig
                groups.append(FacebookGroupConfig(
                    source_id=group_data.get("group_id", ""),
                    group_id=group_data.get("group_id", ""),
                    name=group_data.get("name", ""),
                    config=group_config
                ))
            
            # Create user config
            users.append(FacebookUserConfig(
                email=user_data.get("email", ""),
                password=user_data.get("password", ""),
                active=user_data.get("active", False),
                groups=groups
            ))
        
        return users
    
    async def ensure_user_session(self, user: FacebookUserConfig) -> bool:
        """
        Ensure the user has a valid Facebook session in the database
        
        Args:
            user: User configuration
            
        Returns:
            bool: True if session exists or was created, False otherwise
        """
        # Use the async context manager correctly
        async with SQL_DB_MANAGER.get_session_with_transaction() as db_session:
            # Check if user has a session in the database
            session_data = await ScraperUserBL.get_facebook_session_data(db_session, user.email)
            
            if session_data:
                print(f"✅ [{user.email}] Found existing session in database")
                return True
            
            print(f"🔐 [{user.email}] Session not found. Creating new session...")
            
            try:
                # Create or update user in database - password can be None
                await ScraperUserBL.create_facebook_user(db_session, user.email, user.password)
                
                # Create session with user credentials if available
                if user.email and user.password:
                    # Create Facebook session and get data directly as dictionary
                    session_data = await FacebookGroupScraper.create_session(
                        email=user.email,
                        password=user.password
                    )
                else:
                    # Create session without credentials
                    session_data = await FacebookGroupScraper.create_session()
                
                # Save session data to database
                await ScraperUserBL.save_facebook_session_data(db_session, user.email, dict(session_data))
                
                return True
            except Exception as e:
                print(f"⚠️ [{user.email}] Failed to create session: {e}")
                return False
    
    def create_scraper_for_source(self, source: FacebookGroupConfig, user_config: FacebookUserConfig) -> FacebookGroupScraper:
        """
        Create a Facebook scraper for a specific group
        
        Args:
            source: Group configuration
            user_config: User configuration
            
        Returns:
            FacebookGroupScraper instance for the group
        """
        # Ensure group_id is set properly for the scraper
        group_id = source.group_id
        if not group_id:
            # Fallback to source_id if group_id is empty
            group_id = source.source_id
            
        print(f"Creating Facebook scraper for group ID: {group_id}")
        return FacebookGroupScraper(group_id, source.config, self._browser_manager)
    
    async def get_user_session_data(self, user: FacebookUserConfig) -> Dict[str, Any]:
        """
        Get Facebook session data for a user
        
        Args:
            user: User configuration
            
        Returns:
            Session data for the user
        """
        async with SQL_DB_MANAGER.get_session_with_transaction() as db_session:
            session_data = await ScraperUserBL.get_facebook_session_data(db_session, user.email)
            
            if not session_data:
                # Create new session data if none exists
                if user.email and user.password:
                    # Create Facebook session and get data directly as dictionary
                    session_data = await FacebookGroupScraper.create_session(
                        email=user.email,
                        password=user.password
                    )
                else:
                    # Create session without credentials
                    session_data = await FacebookGroupScraper.create_session()
                
                # Convert to dict if it's a StorageState
                session_dict = dict(session_data) if hasattr(session_data, 'get') else {
                    'cookies': getattr(session_data, 'cookies', []),
                    'origins': getattr(session_data, 'origins', [])
                }
                
                # Save session data to database
                await ScraperUserBL.create_or_update_session_data(
                    db_session,
                    email=user.email,
                    source='facebook',
                    session_data=session_dict
                )
                
                return session_dict
            
            return session_data
    
    def _get_user_id(self, user: FacebookUserConfig) -> str:
        """
        Get a unique identifier for a user
        
        Args:
            user: User configuration
            
        Returns:
            User email as identifier
        """
        return user.email
    
    def _get_user_sources(self, user: FacebookUserConfig) -> List[FacebookGroupConfig]:
        """
        Get all groups for a user
        
        Args:
            user: User configuration
            
        Returns:
            List of group configurations for the user
        """
        return user.groups
    
    def _get_source_name(self, source: FacebookGroupConfig) -> str:
        """
        Get the name of a group
        
        Args:
            source: Group configuration
            
        Returns:
            Name of the group
        """
        return f"{source.name} ({source.group_id})"
    
    async def run_scraper(self, scraper: FacebookGroupScraper, max_cycles: Optional[int] = None):
        """
        Run a single scraper instance
        
        Args:
            scraper: The scraper instance to run
            max_cycles: Optional maximum number of cycles to run
        """
        try:
            await scraper.run(max_cycles)
        except Exception as e:
            print(f"⚠️ Error running scraper: {e}")
        finally:
            await scraper.cleanup()
    
    async def run_user_scrapers(self, user: FacebookUserConfig, max_cycles: Optional[int] = None):
        """
        Run scrapers for a single user's groups
        
        Args:
            user: User configuration
            max_cycles: Optional maximum number of cycles to run
        """
        try:
            # Get session data for the user
            session_data = await self.get_user_session_data(user)
            if not session_data:
                print(f"⚠️ [{user.email}] No session data available")
                return
            
            # Load config file
            try:
                with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except FileNotFoundError:
                print(f"⚠️ Config file not found at {self.CONFIG_PATH}")
                return
            except json.JSONDecodeError as e:
                print(f"⚠️ Invalid JSON in config file: {e}")
                return
            except UnicodeDecodeError as e:
                print(f"⚠️ Encoding error in config file: {e}")
                return
            
            # Get headless setting from global config
            headless = config.get("global", {}).get("headless", False)
            
            # Get browser context with session data
            context = await self._browser_manager.get_context(
                user.email,
                session_data,
                headless
            )
            
            if not context:
                print(f"⚠️ [{user.email}] Failed to get browser context")
                return
            
            # Run scrapers for each group
            tasks = []
            for group in user.groups:
                scraper = self.create_scraper_for_source(group, user)
                # Initialize scraper with session data before running
                await scraper.initialize_with_session_data(session_data, user.email)
                task = asyncio.create_task(self.run_scraper(scraper, max_cycles))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
        except Exception as e:
            print(f"⚠️ Error running scrapers for user {user.email}: {e}")
        finally:
            # Release the browser context only after all scrapers are done
            if self._browser_manager:
                await self._browser_manager.release(user.email)
    
    async def run_db_users(self, max_cycles: Optional[int] = None):
        """
        Run scrapers for all active users in the database
        
        Args:
            max_cycles: Optional maximum number of cycles to run
        """
        # Initialize database
        await SQL_DB_MANAGER.init()
        
        try:
            # Get active users from the database
            db_users = []
            async for db_session in SQL_DB_MANAGER.get_session():
                db_users = await ScraperUserBL.get_active_facebook_users(db_session)
                break  # Just need one session to get the users
            
            if not db_users:
                print("ℹ️ No active users found in database")
                return
            
            print(f"Found {len(db_users)} active users in database")
            
            # Load config file
            try:
                with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except FileNotFoundError:
                print(f"⚠️ Config file not found at {self.CONFIG_PATH}")
                return
            except json.JSONDecodeError as e:
                print(f"⚠️ Invalid JSON in config file: {e}")
                return
            except UnicodeDecodeError as e:
                print(f"⚠️ Encoding error in config file: {e}")
                return
            
            facebook_config = config.get("facebook", {})
            if not facebook_config.get("enabled", True):
                print("Facebook scraper is not enabled in configuration")
                return
                
            # Get Facebook users from config
            config_users = facebook_config.get("users", [])
            if not config_users:
                print("⚠️ No Facebook users found in configuration")
                return
            
            # Convert database users to user configs and merge with config data
            users_to_run = []
            for db_user in db_users:
                # Find matching user in config
                config_user = next(
                    (user for user in config_users if user.get("email") == db_user.email),
                    None
                )
                
                if config_user:
                    # Parse group configurations
                    groups = []
                    for group_data in config_user.get("groups", []):
                        # Merge group config with system defaults
                        group_config = self.system_defaults.copy()
                        group_config.update(group_data.get("config", {}))
                        
                        # Create FacebookGroupConfig
                        groups.append(FacebookGroupConfig(
                            source_id=group_data.get("group_id", ""),
                            group_id=group_data.get("group_id", ""),
                            name=group_data.get("name", ""),
                            config=group_config
                        ))
                    
                    # Create user config
                    user_config = FacebookUserConfig(
                        email=db_user.email,
                        password=db_user.password or config_user.get("password", ""),  # Prefer database password
                        active=db_user.is_active,
                        groups=groups
                    )
                    
                    # Skip if no groups
                    if not user_config.groups:
                        print(f"⚠️ No groups configured for user {user_config.email}, skipping")
                        continue
                    
                    users_to_run.append(user_config)
            
            if not users_to_run:
                print("⚠️ No users with valid configurations found")
                return
            
            print(f"Running scrapers for {len(users_to_run)} users")
            
            # Run scrapers for each user in parallel
            tasks = []
            for user in users_to_run:
                task = asyncio.create_task(self.run_user_scrapers(user, max_cycles))
                tasks.append(task)
                
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
        except Exception as e:
            print(f"⚠️ Error running database users: {e}")
        
    async def sync_config_users_to_db(self):
        """Sync users from config file to database"""
        # Initialize database
        await SQL_DB_MANAGER.init()
        
        try:
            async with SQL_DB_MANAGER.get_session_with_transaction() as db_session:
                for user in self.users:
                    # Check if user exists in database
                    existing_user = await ScraperUserBL.get_scraper_user_by_email_source(
                        db_session, user.email, "facebook"
                    )
                    
                    if existing_user:
                        # Update existing user
                        existing_user.password = user.password
                        existing_user.is_active = user.active       
                        print(f"✅ Updated user {user.email} in database")
                    else:
                        # Create new user - passing active status as is
                        await ScraperUserBL.create_facebook_user(
                            db_session, user.email, user.password, is_active=user.active
                        )
                        print(f"✅ Created user {user.email} in database")
                
                print("✅ User sync complete")
                
        except Exception as e:
            print(f"⚠️ Error syncing users to database: {e}")

async def main():
    """Run the Facebook scraper manager"""
    manager = FacebookScraperManager()
    await manager.run_db_users()
    await manager.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
