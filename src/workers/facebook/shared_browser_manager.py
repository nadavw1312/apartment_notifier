"""
SharedBrowserManager for handling a single browser instance with multiple tabs.
This improves resource efficiency when running multiple scrapers simultaneously.
"""
import asyncio
from playwright.async_api import async_playwright
from typing import Dict, Any, Optional

class SharedBrowserManager:
    """
    Manages shared browser instances for multiple scrapers, one per user.
    Uses a single Chrome process with multiple tabs per user instead of multiple browser instances.
    """
    # Per-user browsers and contexts
    _browsers = {}  # key: user_id, value: browser
    _contexts = {}  # key: user_id, value: context
    _playwright_instances = {}  # key: user_id, value: playwright
    _refs = {}  # key: user_id, value: reference count
    _lock = asyncio.Lock()  # Lock for thread safety
    
    @classmethod
    async def get_browser(cls, user_id: str, headless: bool = False):
        """
        Get or create a shared browser instance for a specific user.
        
        Args:
            user_id: User identifier (email or other unique ID)
            headless: Whether to run in headless mode
            
        Returns:
            The browser instance for this user
        """
        async with cls._lock:
            if user_id not in cls._browsers or cls._browsers[user_id] is None:
                if user_id not in cls._playwright_instances or cls._playwright_instances[user_id] is None:
                    cls._playwright_instances[user_id] = await async_playwright().start()
                cls._browsers[user_id] = await cls._playwright_instances[user_id].chromium.launch(headless=headless)
                cls._refs[user_id] = 0
            
            cls._refs[user_id] += 1
            return cls._browsers[user_id]
    
    @classmethod
    async def get_context(cls, user_id: str, session_data: Optional[Dict[str, Any]] = None, headless: bool = False):
        """
        Get or create a shared browser context for a specific user.
        
        Args:
            user_id: User identifier (email or other unique ID)
            session_data: Optional session data for authentication
            headless: Whether to run in headless mode
            
        Returns:
            The browser context for this user
        """
        browser = await cls.get_browser(user_id, headless)
        
        async with cls._lock:
            if user_id not in cls._contexts or cls._contexts[user_id] is None:
                if session_data:
                    cls._contexts[user_id] = await browser.new_context(storage_state=session_data)
                else:
                    cls._contexts[user_id] = await browser.new_context()
            
            return cls._contexts[user_id]
    
    @classmethod
    async def release(cls, user_id: str):
        """
        Release a reference to a user's browser.
        Cleans up resources when no more references exist.
        
        Args:
            user_id: User identifier (email or other unique ID)
        """
        async with cls._lock:
            if user_id in cls._refs:
                cls._refs[user_id] -= 1
                if cls._refs[user_id] <= 0:
                    await cls.cleanup_user(user_id)
    
    @classmethod
    async def cleanup_user(cls, user_id: str):
        """
        Clean up browser resources for a specific user.
        
        Args:
            user_id: User identifier (email or other unique ID)
        """
        async with cls._lock:
            try:
                if user_id in cls._contexts and cls._contexts[user_id]:
                    await cls._contexts[user_id].close()
                    cls._contexts[user_id] = None
                
                if user_id in cls._browsers and cls._browsers[user_id]:
                    await cls._browsers[user_id].close()
                    cls._browsers[user_id] = None
                
                if user_id in cls._playwright_instances and cls._playwright_instances[user_id]:
                    await cls._playwright_instances[user_id].stop()
                    cls._playwright_instances[user_id] = None
                
                cls._refs[user_id] = 0
                print(f"🧹 Cleaned up shared browser resources for user: {user_id}")
            except Exception as e:
                print(f"⚠️ Error cleaning up resources for user {user_id}: {e}")
    
    @classmethod
    async def cleanup(cls):
        """
        Clean up all browser resources for all users.
        """
        async with cls._lock:
            user_ids = list(cls._browsers.keys())
            for user_id in user_ids:
                await cls.cleanup_user(user_id)
            
            # Clear dictionaries
            cls._browsers.clear()
            cls._contexts.clear()
            cls._playwright_instances.clear()
            cls._refs.clear()
            
            print("🧹 Cleaned up all shared browser resources") 