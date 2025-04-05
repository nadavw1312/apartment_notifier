import json
import random
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Union
from contextlib import asynccontextmanager

# External dependencies
from playwright.async_api import async_playwright, Page, BrowserContext
from bs4 import BeautifulSoup, Comment
from bs4.element import Tag
import htmlmin

# Internal imports - structured by module categories
# Database
from src.db.sql_database import SQL_DB_MANAGER

# Services
from src.services.apartment.apartment_bl import create_apartment, get_processed_post_ids

# LLM and workers
from src.llms.deepseek_api import DeepSeekApi
from src.workers.facebook.shared_browser_manager import SharedBrowserManager

# Components
from src.workers.facebook.components.html_parser import extract_post_id
from src.workers.facebook.components.text_filters import is_apartment_post
from src.workers.facebook.components.data_saver import save_apartment_data
from src.workers.facebook.components.post_extractor import expand_post_content, extract_post_data_playwright
from src.workers.facebook.components.post_processor import process_posts_batch

class FacebookGroupScraper:
    """Facebook group scraper class that can handle multiple Facebook groups in parallel."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "fetch_interval": 300,  # 5 minutes between cycles
        "scroll_times": 2,     # Reduced - we only need a few scrolls to see new posts
        "num_posts_to_fetch": 10,
        "batch_size": 10,
        "headless": False,
        "new_posts_only": True,  # New configuration flag to focus on new posts only
        "max_posts_per_cycle": 30,
        "scroll_delay": 1.5,    # Delay between scrolls in seconds
        "cycle_duration": 290   # Duration of scrolling in seconds (slightly less than fetch_interval)
    }
    
    # Shared session file path
    _session_file = "fb_session.json"
    
    @classmethod
    def get_session_file(cls):
        """Get the current session file path"""
        return cls._session_file
    
    @classmethod
    def set_session_file(cls, path):
        """Set the session file path"""
        cls._session_file = path
    
    def __init__(self, group_id: str, config: dict = {}, db_session_maker=None):
        """
        Initialize a Facebook group scraper for a specific group
        
        Args:
            group_id: The Facebook group ID to scrape
            config: Optional configuration overrides
            db_session_maker: Database session maker
        """
        self.group_id = group_id
        self.group_url = f"https://www.facebook.com/groups/{group_id}"
        
        # Apply configuration (default + overrides)
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # Internal state
        self.running = False
        self.browser = None
        self.context = None
        self.page = None
        self.last_processed_index = -1
        
        # Batch processing state
        self.batch_posts = []
        self.batch_texts = []
        self.batch_indices = []
        
        # Flag to track if we initialized our own browser (for backward compatibility)
        self._owns_browser = False
        self._user_id = None  # Store user ID for shared browser management
        self._session = None  # Session data for cookies
        
        # Browser arguments
        self.browser_context_args = {}  # Default empty dict for browser context args
        
        # Static class reference - now properly accessed from imported module
        self.shared_browser_manager = SharedBrowserManager
        
        # Store already processed post IDs to avoid duplicates
        self.processed_post_ids = set()
        
        # We'll use SQL_DB_MANAGER directly so no need for a separate db_manager
        
    @classmethod
    async def save_facebook_session(cls, email=None, password=None, session_file=None):
        """
        Open browser to login and automatically save session.
        
        Args:
            email: Optional email for auto-login
            password: Optional password for auto-login
            session_file: Optional session file path override
        """
        # Use provided session file or fall back to class variable
        session_path = session_file or cls._session_file
        
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

            await context.storage_state(path=session_path)
            await browser.close()
            print("✅ Session saved to", session_path)
    
    @classmethod
    async def create_facebook_session(cls, email=None, password=None):
        """
        Create a new Facebook session and return the session data without writing to file.
        
        Args:
            email: Optional email for auto-login
            password: Optional password for auto-login
            
        Returns:
            dict: The session data as a dictionary
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
            
            # Get session data directly instead of saving to file
            storage_state = await context.storage_state()
            # Convert to dictionary explicitly to ensure compatibility
            session_data = dict(storage_state)
            await browser.close()
            print("✅ Session data captured successfully")
            
            return session_data

    async def initialize_with_session_data(self, session_data, user_id):
        """
        Initialize the browser and page for scraping using session data directly
        
        Args:
            session_data: Session data dictionary containing cookies and storage
            user_id: User identifier (email) for browser management
        """
        # Use shared browser and context for this specific user
        self.context = await self.shared_browser_manager.get_context(user_id, session_data, self.config["headless"])
        self._user_id = user_id  # Store user_id for cleanup
        
        # Create a new page (tab) in the shared context
        self.page = await self.context.new_page()
        
        # Navigate to the group page
        await self.page.goto(self.group_url)
        await self.page.wait_for_selector("div[role='feed']")
        await asyncio.sleep(5)
        
        print(f"🚀 Initialized scraper for group {self.group_id} (shared browser for user {user_id})")
    
    async def initialize(self, session_file=None):
        """
        Initialize the browser and page for scraping
        
        Args:
            session_file: Optional session file path override
        """
        # Use provided session file or fall back to class variable
        session_path = session_file or self.__class__._session_file
        
        if not Path(session_path).exists():
            raise FileNotFoundError(f"Session file {session_path} not found. Please run save_facebook_session first.")
        
        # For backwards compatibility, we still support the old method
        # but mark that this instance owns its browser for cleanup
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(headless=self.config["headless"])
        self.context = await self.browser.new_context(storage_state=session_path)
        self.page = await self.context.new_page()
        self._owns_browser = True
        
        await self.page.goto(self.group_url)
        await self.page.wait_for_selector("div[role='feed']")
        await asyncio.sleep(5)
        
        print(f"🚀 Initialized scraper for group {self.group_id} (dedicated browser)")
    
    async def cleanup(self):
        """Clean up resources when scraper is done"""
        if self.page:
            await self.page.close()
            self.page = None
        
        # If we own the browser, close it directly
        if self._owns_browser:
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
        else:
            # Otherwise, release our reference to the shared browser for this user
            if self._user_id:
                await self.shared_browser_manager.release(self._user_id)
        
        self.running = False
        print(f"🧹 Cleaned up resources for group {self.group_id}")
    
    async def expand_post_content(self, post):
        """Click on 'ראה עוד' (See more) buttons to expand truncated content."""
        return await expand_post_content(post, self.group_id)
    
    async def load_processed_post_ids(self):
        """Load already processed post IDs from the database"""
        try:
            # Use the session as a read-only session
            session_gen = SQL_DB_MANAGER.get_session()
            async for session in session_gen:
                # Get post IDs
                post_ids = await get_processed_post_ids(session, self.group_id)
                
                # Convert to set for faster lookups
                self.processed_post_ids = set(post_ids)
                print(f"📋 [{self.group_id}] Loaded {len(self.processed_post_ids)} processed post IDs")
                # Session will be closed automatically after exiting the loop
                
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Failed to load processed post IDs: {e}")
            self.processed_post_ids = set()
            
    async def run(self, max_cycles=None):
        """Run the scraper in a loop
        
        Args:
            max_cycles: Maximum number of cycles to run (None for indefinite)
        """
        self.running = True
        cycle_count = 0
        
        try:
            # Try to initialize if page is not set up
            if self.page is None:
                try:
                    await self.initialize()
                except Exception as e:
                    print(f"❌ [{self.group_id}] Failed to initialize: {e}")
                    return
            
            # Safety check - if initialization failed, exit
            if self.page is None:
                print(f"❌ [{self.group_id}] Page is still None after initialization")
                return
                
            # Navigate to the group page if needed
            try:
                current_url = self.page.url  # This is a property, not a coroutine
                if current_url != self.group_url:
                    print(f"🌐 [{self.group_id}] Loading group: {self.group_url}")
                    await self.page.goto(self.group_url)
            except Exception as e:
                print(f"⚠️ [{self.group_id}] Error navigating to group: {e}")
                # Try to re-navigate
                await self.page.goto(self.group_url)
            
            # Load processed post IDs
            await self.load_processed_post_ids()
            
            # Main scraping loop
            while self.running and (max_cycles is None or cycle_count < max_cycles):
                # Track cycle start time
                cycle_start_time = asyncio.get_event_loop().time()
                
                cycle_count += 1
                print(f"🔄 [{self.group_id}] Starting cycle #{cycle_count}")
                
                try:
                    # Verify page is available
                    if not self.page:
                        print(f"⚠️ [{self.group_id}] Page is None, reinitializing...")
                        await self.initialize()
                        if not self.page:
                            print(f"⚠️ [{self.group_id}] Failed to initialize page, skipping cycle")
                            await asyncio.sleep(10)
                            continue
                    
                    # Handle either new posts only mode or full scroll mode
                    if self.config.get("new_posts_only", True):
                        # Get new posts from the top of the feed with continuous scrolling
                        await self.check_for_new_posts()
                    else:
                        # Scroll down to load more posts
                        for _ in range(self.config["scroll_times"]):
                            await self.scroll_page(use_viewport_height=True, multiplier=3)
                        
                        # Wait for posts to load
                        await self.page.wait_for_selector("div[role='article']", timeout=10000)
                        
                        # Collect and process posts
                        post_blocks = await self.page.query_selector_all("div[role='article']")
                        post_count = len(post_blocks)
                        print(f"👀 [{self.group_id}] Found {post_count} posts")
                        
                        # Collect and process all visible posts
                        await self.process_visible_posts(post_blocks)
                    
                    # Calculate time spent in this cycle
                    cycle_elapsed = asyncio.get_event_loop().time() - cycle_start_time
                    wait_time = max(0, self.config["fetch_interval"] - cycle_elapsed)
                    
                    # Sleep for remaining time until next cycle should start
                    if wait_time > 0:
                        print(f"⏳ [{self.group_id}] Cycle completed in {cycle_elapsed:.1f}s, waiting {wait_time:.1f}s until next cycle...\n")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"⚠️ [{self.group_id}] Cycle took {cycle_elapsed:.1f}s, which exceeds the fetch interval of {self.config['fetch_interval']}s. Starting next cycle immediately.\n")
                    
                except Exception as e:
                    print(f"⚠️ [{self.group_id}] Error in cycle #{cycle_count}: {e}")
                    await asyncio.sleep(10)  # Wait a bit before retrying
                    
        except Exception as e:
            print(f"❌ [{self.group_id}] Fatal error: {e}")
        finally:
            # Clean up
            if self.context:
                await self.context.close()
            if self.browser and self._owns_browser:
                await self.browser.close()
            
            self.running = False
            
    async def check_for_new_posts(self):
        """Check for new posts on the page by continuously scrolling for cycle_duration"""
        try:
            print(f"🔄 [{self.group_id}] Starting new posts cycle with continuous scrolling...")
            
            # Make sure page exists before trying to use it
            if self.page is None:
                print(f"⚠️ [{self.group_id}] Page is not initialized")
                return
                
            # Refresh the page to get the latest posts
            await self.page.reload()
            
            # Wait for posts to load
            await self.page.wait_for_selector("div[role='article']", timeout=10000)
            
            # Track start time
            start_time = asyncio.get_event_loop().time()
            end_time = start_time + self.config["cycle_duration"]
            
            # Get initial posts
            post_blocks = await self.page.query_selector_all("div[role='article']")
            print(f"👀 [{self.group_id}] Found {len(post_blocks)} visible posts initially")
            
            # Process the initial visible posts
            await self.process_visible_posts(post_blocks, new_only=True)
            
            # Continue scrolling and processing until time runs out
            scroll_count = 0
            while asyncio.get_event_loop().time() < end_time:
                # Calculate remaining time
                remaining_time = end_time - asyncio.get_event_loop().time()
                print(f"⏱️ [{self.group_id}] Continuing to scroll for {remaining_time:.1f} more seconds (scroll #{scroll_count+1})")
                
                # Use the centralized scroll method with random distance
                scroll_distance = await self.scroll_page(random_range=(400, 800))
                
                # Get posts after scrolling
                post_blocks = await self.page.query_selector_all("div[role='article']")
                print(f"👀 [{self.group_id}] Found {len(post_blocks)} visible posts after scrolling")
                
                # Process the newly visible posts
                await self.process_visible_posts(post_blocks, new_only=True)
                
                scroll_count += 1
                
            print(f"✅ [{self.group_id}] Completed continuous scrolling cycle with {scroll_count} scrolls over {self.config['cycle_duration']} seconds")
            
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error during continuous scrolling cycle: {e}")
    
    async def process_visible_posts(self, post_blocks, new_only=False):
        """
        Process visible posts on the page
        
        Args:
            post_blocks: List of post elements
            new_only: Only process posts that haven't been processed before
        """
        try:
            self.batch_posts = []
            self.batch_texts = []
            
            # Limit the number of posts to process
            max_posts = min(len(post_blocks), self.config["max_posts_per_cycle"])
            processed_count = 0
            skipped_count = 0
            
            for idx in range(max_posts):
                try:
                    post = post_blocks[idx]
                    
                    # Get post HTML
                    post_html = await post.inner_html()
                    
                    # Extract post ID
                    post_id = self.extract_post_id(post_html)
                    
                    # Skip already processed posts if new_only is True
                    if new_only and post_id and post_id in self.processed_post_ids:
                        continue
                    
                    # Skip posts that are too short (probably not real posts)
                    if len(post_html) < 200:
                        continue
                    
                    # First expand post content to make sure "See more" is clicked
                    await self.expand_post_content(post)
                    
                    # Extract post data with date/time information
                    data = await self.extract_post_data_playwright(post)
                    data["post_id"] = post_id
                    
                    # Skip posts without a valid username
                    if data["user_name"] == "Unknown":
                        print(f"⚠️ [{self.group_id}] Skipping post {post_id}: No valid username found")
                        skipped_count += 1
                        continue
                    
                    print(f"📊 [{self.group_id}] Post data: ID={post_id}, User={data['user_name']}, Date={data.get('post_date_time', 'Unknown')}")
                    
                    # Add to batch
                    self.batch_posts.append(data)
                    self.batch_texts.append(data["text"])
                    
                    # Mark as processed
                    if post_id:
                        self.processed_post_ids.add(post_id)
                    
                    processed_count += 1
                    
                    # Process batch when it reaches size
                    if len(self.batch_posts) >= self.config["batch_size"]:
                        await self.process_batch()
                
                except Exception as e:
                    print(f"⚠️ [{self.group_id}] Error processing post at index {idx}: {e}")
            
            # Process any remaining posts
            if self.batch_posts:
                await self.process_batch()
            
            print(f"✅ [{self.group_id}] Processed {processed_count} posts, skipped {skipped_count} posts")
        
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error processing visible posts: {e}")
    
    async def process_batch_results(self, batch_results):
        """Process batch results and save to database"""
        new_posts_count = 0
        
        for i, result in enumerate(batch_results):
            try:
                # Get original post HTML for reference if needed
                original_post_data = self.batch_posts[i]
                original_post_link = original_post_data.get("post_link", "Unknown") 
                post_id = original_post_data.get("post_id", "unknown")
                post_date_time = original_post_data.get("post_date_time", "Unknown")
                user_name = original_post_data.get("user_name", "Unknown")
                
                # Skip invalid posts
                if not result.get("is_valid", False):
                    print(f"⚠️ [{self.group_id}] Skipping invalid post: {post_id}")
                    continue
                
                # Prepare data for database
                data = {
                    "text": result["text"],
                    "user": user_name,  # Use our extracted user_name instead of the LLM result
                    "timestamp": post_date_time if post_date_time != "Unknown" else result["timestamp"],
                    "image_urls": result.get("images", []),
                    "post_link": original_post_link if original_post_link != "Unknown" else result["post_link"],
                    "price": result["price"],
                    "location": result["location"],
                    "phone_numbers": result["phone_numbers"],
                    "mentions": result["mentions"],
                    "summary": result["summary"],
                    "source": "facebook",
                    "group_id": self.group_id,
                    "is_valid": True,  # We already filtered for valid posts
                    "post_id": post_id  # Store the post ID for future reference
                }
                
                # Save to database immediately and wait for result
                try:
                    # Simply await the save operation
                    await self.save_apartment_data(data)
                    # Only increment counter if save was successful
                    new_posts_count += 1
                    print(f"📝 [{self.group_id}] Saved post: {data['post_link']} (User: {user_name})")
                except Exception as save_error:
                    print(f"⚠️ [{self.group_id}] Failed to save post {post_id}: {save_error}")
                
            except Exception as e:
                print(f"⚠️ [{self.group_id}] Error processing result {i}: {e}")
        
        if new_posts_count > 0:
            print(f"✅ [{self.group_id}] Saved {new_posts_count} new posts to database")
        
        return new_posts_count
    
    async def process_batch(self):
        """Process the current batch of posts"""
        if not self.batch_posts or not self.batch_texts:
            return
        
        saved_count = 0  # Initialize outside the try block
        
        try:
            print(f"🧠 [{self.group_id}] Processing batch of {len(self.batch_texts)} posts")
            
            # Process the batch with DeepSeek API
            batch_results = await process_posts_batch(self.batch_texts)
            
            # Add post IDs and links to results
            for i, result in enumerate(batch_results):
                if i < len(self.batch_posts):
                    result["post_id"] = self.batch_posts[i].get("post_id")
                    result["post_link"] = self.batch_posts[i].get("post_link")
            
            # Process results and save to database
            saved_count = await self.process_batch_results(batch_results)
            
            # Log results based on saved count
            if saved_count > 0:
                print(f"🔄 [{self.group_id}] Batch processing complete. Successfully saved {saved_count} posts.")
            else:
                print(f"ℹ️ [{self.group_id}] Batch processing complete. No valid posts were saved.")
            
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error processing batch: {e}")
            
        finally:
            # Clear batch regardless of success or failure
            self.batch_posts = []
            self.batch_texts = []
            
        return saved_count  # Return the result for potential use by caller
    
    async def save_apartment_data(self, data):
        """Save apartment data to database - this is a create operation"""
        return await save_apartment_data(data, self.group_id)

    async def scroll_page(self, distance=None, random_range=None, use_viewport_height=False, multiplier=1, delay=None):
        """
        Scroll the page by the specified parameters
        
        Args:
            distance: Exact pixel distance to scroll (if specified)
            random_range: Tuple of (min, max) values to randomly choose a scroll distance
            use_viewport_height: Whether to use viewport height as the base for scrolling
            multiplier: Multiplier for viewport height (if use_viewport_height is True)
            delay: Time to wait after scrolling (defaults to config scroll_delay)
            
        Returns:
            The actual scroll distance used
        """
        if self.page is None:
            print(f"⚠️ [{self.group_id}] Cannot scroll - page is not initialized")
            return 0
            
        # Determine scroll distance
        scroll_distance = distance
        
        if random_range is not None:
            scroll_distance = random.randint(random_range[0], random_range[1])
            
        if use_viewport_height:
            # Use viewport height as the base for scrolling
            scroll_js = f"window.scrollBy(0, window.innerHeight * {multiplier})"
        else:
            # Use pixel distance
            scroll_js = f"window.scrollBy(0, {scroll_distance})"
            
        # Execute the scroll
        await self.page.evaluate(scroll_js)
        
        # Apply delay after scrolling
        actual_delay = delay if delay is not None else self.config["scroll_delay"]
        if actual_delay > 0:
            await asyncio.sleep(actual_delay)
            
        return scroll_distance

    def stop(self):
        """Stop the scraper"""
        self.running = False
        print(f"🛑 [{self.group_id}] Stopping scraper")

    async def process_posts(self, posts_data):
        """
        Process a list of posts data
        
        Args:
            posts_data: List of posts data to process
        """
        try:
            if not posts_data:
                return
            
            # Extract just the text from each post for processing
            texts = [post["text"] for post in posts_data]
            
            # Process the batch of texts with DeepSeek API
            print(f"🧠 [{self.group_id}] Processing {len(texts)} posts with DeepSeek API")
            batch_results = await process_posts_batch(texts)
            
            # Add post IDs to results
            for i, result in enumerate(batch_results):
                if i < len(posts_data):
                    result["post_id"] = posts_data[i].get("post_id")
                    result["post_link"] = posts_data[i].get("post_link")
            
            # Save results to database
            await self.process_batch_results(batch_results)
            
            return batch_results
        except Exception as e:
            print(f"⚠️ [{self.group_id}] Error processing posts: {e}")
            return []

    def extract_post_id(self, html):
        """
        Extract the post ID from the HTML
        
        Args:
            html: The HTML content of the post
            
        Returns:
            The post ID or None if not found
        """
        return extract_post_id(html)

    async def extract_post_data_playwright(self, post):
        """
        Extract data from a post using Playwright
        
        Args:
            post: The Playwright element handle for the post
            
        Returns:
            Dictionary with extracted post data
        """
        return await extract_post_data_playwright(post, self.page, self.group_id)

# Non-class functions that don't need state and can be shared

async def run_scrapers(group_ids, config: dict = {}):
    """
    Run multiple scrapers in parallel
    
    Args:
        group_ids: List of Facebook group IDs to scrape
        config: Optional configuration to apply to all scrapers
    """
    # Initialize the database
    await SQL_DB_MANAGER.init()
    
    try:
        # Check if session file exists
        if not Path(FacebookGroupScraper.get_session_file()).exists():
            print("🔐 Facebook session not found. Launching manual login...")
            await FacebookGroupScraper.save_facebook_session()
        
        # Create scrapers for each group
        scrapers = [FacebookGroupScraper(group_id, config) for group_id in group_ids]
        
        # Initialize all scrapers first
        for scraper in scrapers:
            await scraper.initialize()
        
        # Run all scrapers simultaneously
        await asyncio.gather(*[scraper.run() for scraper in scrapers])
    
    except Exception as e:
        print(f"⚠️ Error running scrapers: {e}")
    
    finally:
        # Clean up all scrapers
        for scraper in scrapers:
            await scraper.cleanup()
        
        # Close the database
        await SQL_DB_MANAGER.close()

async def main():
    # Example group IDs to scrape (add your own)
    group_ids = [
        "333022240594651",  # Original group
        # Add more group IDs here
    ]
    
    # Run scrapers in parallel
    await run_scrapers(group_ids)

if __name__ == "__main__":
    asyncio.run(main())
