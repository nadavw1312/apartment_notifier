import json
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Union, cast

# External dependencies
from playwright.async_api import async_playwright, Page, ElementHandle, StorageState
from bs4 import BeautifulSoup

# Internal imports - structured by module categories
# Database
from src.db.sql_database import SQL_DB_MANAGER

# Services
from src.services.apartment.apartment_bl import ApartmentBL

# Base scraper
from src.workers.scrapers.base.base_scraper import BaseScraper

# Components
from src.workers.scrapers.facebook.components import (
    extract_post_id,
    save_apartment_data,
    expand_post_content,
)

class FacebookGroupScraper(BaseScraper):
    """Facebook group scraper class that handles Facebook groups using the base scraper framework."""
    
    # Facebook-specific configuration overrides
    DEFAULT_CONFIG = {
        **BaseScraper.DEFAULT_CONFIG,  # Inherit base config
        "fetch_interval": 300,  # 5 minutes between cycles
        "scroll_times": 2,      # Reduced - we only need a few scrolls to see new posts
        "batch_size": 10,
        "headless": False,
        "new_posts_only": True,  # Focus on new posts only
        "max_items_per_cycle": 30,
    }
    
    def __init__(self, group_id: str, config: Optional[Dict[str, Any]] = None, browser_manager=None):
        """
        Initialize a Facebook group scraper for a specific group
        
        Args:
            group_id: The Facebook group ID to scrape
            config: Optional configuration overrides
            browser_manager: Optional SharedBrowserManager instance
        """
        # Call parent constructor with source_id and config
        super().__init__(group_id, config)
        
        # Store Facebook-specific values
        self.group_id = group_id  # Store group_id for Facebook-specific operations
        self.source_id = group_id  # Ensure source_id is set for base class operations
        
        # Store browser manager
        self._browser_manager = browser_manager
        
        # Batch processing state specific to Facebook
        self.batch_posts = []
    
    async def process_batch(self):
        """Process the current batch of items and store reference to batch for Facebook-specific handling"""
        if not self.batch_items:
            return 0
        
        # Store batch_items for reference in _prepare_save_data
        self.batch_posts = self.batch_items.copy()
        
        # Call parent implementation
        return await super().process_batch()
    
    def _get_source_url(self) -> str:
        """
        Get the URL for the source being scraped.
        
        Returns:
            URL for the Facebook group
        """
        return f"https://www.facebook.com/groups/{self.source_id}"
    
    async def _get_item_selector(self) -> str:
        """
        Get the CSS selector for posts on the Facebook page
        
        Returns:
            CSS selector for posts
        """
        return "div[role='article']"
    
    @classmethod
    async def create_session(cls, email=None, password=None):
        """
        Create a Facebook session and return the session data.
        
        Args:
            email: Optional email for auto-login
            password: Optional password for auto-login
            
        Returns:
            dict: The session data as a dictionary (StorageState format)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto("https://www.facebook.com/login")

            if email and password:
                # Auto-login if credentials provided
                try:
                    await page.fill('input[name="email"]', email)
                    await page.fill('input[name="pass"]', password)
                    await page.click('button[name="login"]')
                    await page.wait_for_load_state("networkidle")
                    
                    # Wait for login to complete - check for logout button or feed
                    print("🔄 Waiting for login to complete...")
                    try:
                        # Try to find elements that confirm successful login
                        await page.wait_for_selector("div[role='feed'], a[aria-label*='profile'], a[href*='/me/'], div[aria-label*='Account'], div[aria-label*='account']", 
                                                   timeout=60000)
                        print("✅ Login successful")
                    except Exception as e:
                        print(f"⚠️ Could not detect successful login: {e}")
                        print("⏳ Continuing with current state anyway...")
                except Exception as e:
                    print(f"⚠️ Auto-login failed: {e}")
                    
                    # If auto-login fails, wait for manual login
                    print("🔐 Please log in manually in the browser window.")
                    try:
                        # Wait for navigation after manual login
                        await page.wait_for_selector("div[role='feed'], a[aria-label*='profile'], a[href*='/me/'], div[aria-label*='Account'], div[aria-label*='account']", 
                                                   timeout=120000)
                        print("✅ Manual login detected")
                    except Exception as login_err:
                        print(f"⚠️ Could not detect successful manual login: {login_err}")
                        print("⏳ Continuing with current state anyway...")
            else:
                # Manual login required
                print("🔐 Please log in manually in the browser window.")
                try:
                    # Wait for navigation after manual login
                    await page.wait_for_selector("div[role='feed'], a[aria-label*='profile'], a[href*='/me/'], div[aria-label*='Account'], div[aria-label*='account']", 
                                               timeout=120000)
                    print("✅ Manual login detected")
                except Exception as e:
                    print(f"⚠️ Could not detect successful manual login: {e}")
                    print("⏳ Continuing with current state anyway...")

            # Wait a bit more to ensure cookies are properly set
            await asyncio.sleep(3)

            # Get session data
            storage_state = await context.storage_state()
            
            await browser.close()
            print("✅ Session data captured successfully")
            
            return storage_state

    
    async def initialize_with_session_data(self, session_data: StorageState, user_id: str):
        """
        Initialize the browser and page with provided session data
        
        Args:
            session_data: The session data to use for authentication (StorageState format)
            user_id: User identifier for browser management
        """
        try:
            # Store user_id for tracking
            self._user_id = user_id
            self._session = session_data
            
            if not self._browser_manager:
                raise RuntimeError("Browser manager not initialized")
            
            # Get context from browser manager
            self._context = await self._browser_manager.get_context(
                user_id,
                session_data,
                self.DEFAULT_CONFIG["headless"]
            )
            
            if not self._context:
                raise RuntimeError("Failed to get browser context")
            
            # Create a new page in the context
            self.page = await self._context.new_page()
            
            if not self.page:
                raise RuntimeError("Failed to create new page")
            
            # Navigate to the group page
            await self.page.goto(self.source_url)
            await self.page.wait_for_selector("div[role='feed']", timeout=30000)  # 30 second timeout
            await asyncio.sleep(5)
            
            print(f"🚀 Initialized scraper for group {self.group_id} with provided session data (user {user_id})")
            
        except Exception as e:
            print(f"❌ [{self.group_id}] Page initialization failed: {e}")
            if self.page:
                await self.page.close()
            raise
    
    async def load_processed_item_ids(self):
        """Load already processed post IDs from the database"""
        try:
            # Use the session as a read-only session
            session_gen = SQL_DB_MANAGER.get_session()
            async for session in session_gen:
                # Get post IDs
                post_ids = await ApartmentBL.get_processed_post_ids(session, self.group_id)
                
                # Convert to set for faster lookups
                self.processed_item_ids = set(post_ids)
                print(f"📋 [{self.group_id}] Loaded {len(self.processed_item_ids)} processed post IDs")
                break  # Just need one session to get the IDs
                
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Failed to load processed post IDs: {e}")
            self.processed_item_ids = set()
    
    async def _expand_item_content(self, item):
        """
        Expand truncated content in a post by clicking "See more" buttons
        
        Args:
            item: The post element to expand
        """
        return await expand_post_content(item, self.group_id)
    
    async def _is_valid_item(self, data: Dict[str, Any]) -> bool:
        """
        Check if an item is valid based on its data
        
        Args:
            data: The extracted item data
            
        Returns:
            True if the item is valid, False otherwise
        """
        # Skip posts without a valid username
        if data.get("user") == "Unknown":
            return False
            
        # Additional logic can be added here
        return True
    
    def _format_item_log(self, data: Dict[str, Any]) -> str:
        """
        Format item data for logging
        
        Args:
            data: The extracted post data
            
        Returns:
            Formatted string for logging
        """
        user = data.get("user", "Unknown")
        date = data.get("timestamp", "Unknown")
        return f"User={user}, Date={date}"
    
    async def save_item_data(self, data: Dict[str, Any]):
        """
        Save post data to storage
        
        Args:
            data: Data to save
        """
        return await save_apartment_data(data, self.group_id)
    
    async def _is_valid_result(self, result: Dict[str, Any]) -> bool:
        """
        Check if a batch result is valid
        
        Args:
            result: The processed result
            
        Returns:
            True if the result is valid, False otherwise
        """
        return result.get("is_valid", False)
    
    async def _prepare_save_data(self, result: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Prepare data for saving to database with Facebook-specific fields
        
        Args:
            result: The processed result
            index: The index of the result in the batch
            
        Returns:
            Data dictionary ready for saving
        """
        try:
            # Get original post data for reference
            original_post_data = self.batch_posts[index] if index < len(self.batch_posts) else {}
            
            # Extract Facebook-specific data
            post_date_time = original_post_data.get("timestamp", "Unknown")
            user_name = original_post_data.get("user", "Unknown")
            original_post_link = original_post_data.get("link", "Unknown")
            
            # Get common prepared data from base class
            data = await super()._prepare_save_data(result, index)
            
            # Override with Facebook-specific fields
            data["source"] = "facebook"
            data["group_id"] = self.group_id
            
            # Use our extraction data for some fields if available
            if user_name != "Unknown":
                data["user"] = user_name
            
            if post_date_time != "Unknown":
                data["timestamp"] = post_date_time
                
            if original_post_link != "Unknown":
                data["post_link"] = original_post_link
                
            return data
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error preparing save data: {e}")
            return result  # Return original result as fallback

    def extract_post_id(self, html: str) -> str:
        """
        Extract the post ID from the HTML
        
        Args:
            html: The HTML content of the post
            
        Returns:
            The post ID or empty string if not found
        """
        result = extract_post_id(html)
        return result if result is not None else ""

    async def extract_item_id(self, item: Union[Dict[str, Any], ElementHandle]) -> str:
        """
        Extract a unique identifier from a post
        
        Args:
            item: The item to extract an ID from (post element or dict)
            
        Returns:
            Unique identifier for the item
        """
        try:
            # Handle dictionary type
            if isinstance(item, dict) and "post_id" in item:
                return item["post_id"]
            
            # Handle ElementHandle type
            elem = cast(ElementHandle, item)
            try:
                item_html = await elem.inner_html()
                return self.extract_post_id(item_html)
            except Exception:
                return ""
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error extracting item ID: {e}")
            return ""

    async def extract_item_data(self, item: Union[Dict[str, Any], ElementHandle]) -> Dict[str, Any]:
        """
        Extract relevant data from a post
        
        Args:
            item: The item to extract data from (post element or dict)
            
        Returns:
            Dictionary of extracted data
        """
        try:
            # Handle dictionary
            if isinstance(item, dict):
                return item
            
            # Handle ElementHandle by using the base extraction method
            elem = cast(ElementHandle, item)
            
            # Use the base extraction method
            data = await self._extract_item_data_base(elem, self.page)
            
            # Add post ID
            try:
                item_html = await elem.inner_html()
                post_id = self.extract_post_id(item_html)
                if post_id:
                    data["post_id"] = post_id
            except Exception:
                pass
                
            # Rename fields to match Facebook-specific field names (for backward compatibility)
            if "link" in data:
                data["post_link"] = data.pop("link")
            if "timestamp" in data:
                data["post_date_time"] = data.pop("timestamp")
            if "user" in data:
                data["user_name"] = data.pop("user")
                    
            return data
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error in extract_item_data: {e}")
            return {}
    
    # Facebook-specific extraction methods
    
    async def _extract_item_link(self, element, page) -> str:
        """
        Extract the permalink for a Facebook post
        
        Args:
            element: The post element
            page: The Playwright page object
            
        Returns:
            Post permalink as string
        """
        try:
            # Find the post permalink
            permalink_element = await element.query_selector("a[href*='/posts/']")
            if permalink_element:
                # Get the permalink
                href = await permalink_element.get_attribute("href")
                if href and not href.startswith("http"):
                    href = f"https://www.facebook.com{href}"
                return href
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error extracting post link: {e}")
        
        return "Unknown"
    
    async def _extract_item_timestamp(self, element, page) -> str:
        """
        Extract the timestamp/date for a Facebook post
        
        Args:
            element: The post element
            page: The Playwright page object
            
        Returns:
            Post timestamp as string
        """
        try:
            # First find the permalink element
            permalink_element = await element.query_selector("a[href*='/posts/']")
            
            if permalink_element and page and await permalink_element.is_visible():
                # Hover over the permalink link to trigger tooltip
                await permalink_element.hover()
                await asyncio.sleep(0.5)
                
                # Check if there's a tooltip
                tooltip = await page.query_selector("div[role='tooltip']")
                
                if tooltip:
                    tooltip_text = await tooltip.inner_text()
                    timestamp = tooltip_text.strip()
                    print(f"📅 [{self.group_id}] Found post date/time from tooltip: {timestamp}")
                    return timestamp
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error extracting post timestamp: {e}")
        
        return "Unknown"
    
    async def _extract_item_user(self, element, page) -> str:
        """
        Extract the user/author name for a Facebook post
        
        Args:
            element: The post element
            page: The Playwright page object
            
        Returns:
            Username as string
        """
        try:
            # Try various selectors to find the username
            username_element = await element.query_selector("a[role='link'] strong span")
            if not username_element:
                username_element = await element.query_selector("a[aria-label] span")
            
            # Try to get the username from the found element
            if username_element:
                user_name = await username_element.inner_text()
                if user_name and len(user_name.strip()) > 0:
                    user_name = user_name.strip()
                    print(f"👤 [{self.group_id}] Found user name: {user_name}")
                    return user_name
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error extracting username: {e}")
        
        return "Unknown"
    
    async def _extract_item_user_link(self, element, page) -> str:
        """
        Extract the user profile link for a Facebook post
        
        Args:
            element: The post element
            page: The Playwright page object
            
        Returns:
            User profile link as string
        """
        try:
            # Find the user profile link
            user_link_element = await element.query_selector("a[href*='/user/']")
            
            # If not found, try other common patterns
            if not user_link_element:
                user_link_element = await element.query_selector("a[href*='facebook.com/profile']")
            
            if user_link_element:
                # Extract user profile link
                user_href = await user_link_element.get_attribute("href")
                if user_href and len(user_href) > 0:
                    if not user_href.startswith("http"):
                        user_href = f"https://www.facebook.com{user_href}"
                    print(f"🔗 [{self.group_id}] Found user link: {user_href}")
                    return user_href
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error extracting user link: {e}")
        
        return "Unknown"

    async def cleanup(self):
        """Clean up resources"""
        if self.page:
            await self.page.close()
            self.page = None

    async def initialize(self, session_file: Optional[str] = None):
        """
        Initialize the scraper with a local session file
        
        Args:
            session_file: Optional path to session file
        """
        try:
            if session_file:
                # Load session data from file
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                except FileNotFoundError:
                    print(f"⚠️ Session file not found: {session_file}")
                    return
                except json.JSONDecodeError as e:
                    print(f"⚠️ Invalid JSON in session file: {e}")
                    return
                except UnicodeDecodeError as e:
                    print(f"⚠️ Encoding error in session file: {e}")
                    return
                
                # Initialize with session data
                await self.initialize_with_session_data(session_data, "local_user")
            else:
                # Initialize without session data
                if not self._browser_manager:
                    raise RuntimeError("Browser manager not initialized")
                
                # Get context from browser manager
                self._context = await self._browser_manager.get_context(
                    "local_user",
                    None,
                    self.DEFAULT_CONFIG["headless"]
                )
                
                if not self._context:
                    raise RuntimeError("Failed to get browser context")
                
                # Create a new page in the context
                self.page = await self._context.new_page()
                
                if not self.page:
                    raise RuntimeError("Failed to create new page")
                
                # Navigate to the group page
                await self.page.goto(self.source_url)
                await self.page.wait_for_selector("div[role='feed']", timeout=30000)
                await asyncio.sleep(5)
                
                print(f"🚀 Initialized scraper for group {self.group_id} without session data")
                
        except Exception as e:
            print(f"❌ [{self.group_id}] Initialization failed: {e}")
            if self.page:
                await self.page.close()
            raise
