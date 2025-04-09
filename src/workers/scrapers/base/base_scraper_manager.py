"""
Base scraper manager for handling multiple scrapers of any type.
"""
import asyncio
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic

from src.workers.scrapers.base.base_scraper import BaseScraper

# Define generic types for the manager
T = TypeVar('T', bound=BaseScraper)
U = TypeVar('U')  # User config type
G = TypeVar('G')  # Group/source config type

@dataclass
class SourceConfig:
    """Configuration for a single source to scrape"""
    source_id: str
    name: str
    config: Dict[str, Any]

@dataclass
class UserConfig:
    """Configuration for a user with sources to scrape"""
    email: str
    password: str
    active: bool
    sources: List[SourceConfig]

class BaseScraperManager(Generic[T, U, G], ABC):
    """
    Base manager class for web scrapers that handles multiple users
    and their source configurations.
    """
    
    # Default config path that can be overridden by subclasses
    CONFIG_PATH = "config/scraper_config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the scraper manager
        
        Args:
            config_path: Optional path to config file. If not provided, uses default path.
        """
        self.config_path = config_path or self.CONFIG_PATH
        self.config = self._load_config()
        self.system_defaults = self.config.get("system_defaults", {})
        self.users = self._parse_user_configs()
        self.scrapers: Dict[str, List[T]] = {}  # key: user_id, value: list of scrapers
    
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
    
    @abstractmethod
    def _parse_user_configs(self) -> List[U]:
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
                groups.append(SourceConfig(
                    source_id=group_data.get("group_id", ""),
                    name=group_data.get("name", ""),
                    config=group_config
                ))
            
            # Create user config
            users.append(UserConfig(
                email=user_data.get("email", ""),
                password=user_data.get("password", ""),
                active=user_data.get("active", False),
                sources=groups
            ))
        
        return users  
      
    def get_active_users(self) -> List[U]:
        """Get all active users from config"""
        return [user for user in self.users if self._is_user_active(user)]
    
    def _is_user_active(self, user: U) -> bool:
        """Check if a user is active"""
        # Default implementation, can be overridden
        return getattr(user, "active", False)
    
    @abstractmethod
    async def ensure_user_session(self, user: U) -> bool:
        """
        Ensure the user has a valid session
        Must be implemented by specific managers
        
        Args:
            user: User configuration
            
        Returns:
            bool: True if session exists or was created, False otherwise
        """
        raise NotImplementedError("Subclasses must implement ensure_user_session")
    
    @abstractmethod
    def create_scraper_for_source(self, source: G, user_config: U) -> T:
        """
        Create a scraper for a specific source and user
        Must be implemented by specific managers
        
        Args:
            source: Source configuration
            user_config: User configuration
            
        Returns:
            Scraper instance for the source
        """
        raise NotImplementedError("Subclasses must implement create_scraper_for_source")
    
    @abstractmethod
    async def get_user_session_data(self, user: U) -> Dict[str, Any]:
        """
        Get session data for a user
        Must be implemented by specific managers
        
        Args:
            user: User configuration
            
        Returns:
            Session data for the user
        """
        raise NotImplementedError("Subclasses must implement get_user_session_data")
    
    async def run_user_scrapers(self, user: U, max_cycles: Optional[int] = None):
        """
        Run scrapers for all sources for a specific user
        
        Args:
            user: User configuration
            max_cycles: Optional maximum number of cycles to run
        """
        # First, ensure user has a valid session
        if not await self.ensure_user_session(user):
            print(f"❌ Cannot run scrapers without valid session")
            return
        
        # Get session data
        session_data = await self.get_user_session_data(user)
        if not session_data:
            print(f"❌ No session data found")
            return
        
        try:
            # Create scrapers for each source
            user_id = self._get_user_id(user)
            scrapers = []
            
            for source in self._get_user_sources(user):
                print(f"🔄 Creating scraper for source: {self._get_source_name(source)}")
                scraper = self.create_scraper_for_source(source, user)
                scrapers.append(scraper)
            
            # Add to scrapers dict for tracking
            self.scrapers[user_id] = scrapers
            
            # Initialize all scrapers with session data
            for scraper in scrapers:
                await scraper.initialize_with_session_data(session_data, user_id)
            
            # Run all scrapers simultaneously
            await asyncio.gather(*[scraper.run(max_cycles) for scraper in scrapers])
            
        except Exception as e:
            print(f"⚠️ Error running scrapers: {e}")
        
        finally:
            # Clean up all scrapers
            if user_id in self.scrapers:
                for scraper in self.scrapers[user_id]:
                    await scraper.cleanup()
                    
                # Remove from scrapers dict
                del self.scrapers[user_id]
    
    async def run_all_active_users(self, max_cycles: Optional[int] = None):
        """
        Run scrapers for all active users
        
        Args:
            max_cycles: Optional maximum number of cycles to run
        """
        # Get active users
        active_users = self.get_active_users()
        
        if not active_users:
            print("ℹ️ No active users found in configuration")
            return
        
        # Run scrapers for each active user in parallel
        tasks = []
        for user in active_users:
            task = asyncio.create_task(self.run_user_scrapers(user, max_cycles))
            tasks.append(task)
            
        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
    
    @abstractmethod
    def _get_user_id(self, user: U) -> str:
        """
        Get a unique identifier for a user
        Must be implemented by specific managers
        
        Args:
            user: User configuration
            
        Returns:
            Unique identifier for the user
        """
        raise NotImplementedError("Subclasses must implement _get_user_id")
    
    @abstractmethod
    def _get_user_sources(self, user: U) -> List[G]:
        """
        Get all sources for a user
        Must be implemented by specific managers
        
        Args:
            user: User configuration
            
        Returns:
            List of source configurations for the user
        """
        raise NotImplementedError("Subclasses must implement _get_user_sources")
    
    @abstractmethod
    def _get_source_name(self, source: G) -> str:
        """
        Get the name of a source
        Must be implemented by specific managers
        
        Args:
            source: Source configuration
            
        Returns:
            Name of the source
        """
        raise NotImplementedError("Subclasses must implement _get_source_name")
    
    async def cleanup_user(self, user_id: str):
        """
        Clean up resources for a specific user
        
        Args:
            user_id: User identifier
        """
        if user_id in self.scrapers:
            for scraper in self.scrapers[user_id]:
                await scraper.cleanup()
            
            # Remove from scrapers dict
            del self.scrapers[user_id]
    
    async def cleanup(self):
        """Clean up all resources for all users"""
        # Get all user IDs
        user_ids = list(self.scrapers.keys())
        
        # Clean up each user
        for user_id in user_ids:
            await self.cleanup_user(user_id)
        
        # Clear scrapers dict
        self.scrapers.clear()
        
        print("🧹 Cleaned up all scraper manager resources") 