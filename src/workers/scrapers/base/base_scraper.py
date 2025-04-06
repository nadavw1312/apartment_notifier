"""
Base scraper class that defines common interfaces and functionality for all scrapers.
"""
import asyncio
import random
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Union, Tuple
from playwright.async_api import Page, BrowserContext, Browser
from src.workers.scrapers.base.browser_manager import SharedBrowserManager
from src.workers.scrapers.base.text_processor import process_text_batch, get_apartment_system_prompt

class BaseScraper(ABC):
    """
    Base abstract class for web scrapers.
    Provides common functionality and defines required interfaces.
    """
    
    # Default configuration that can be overridden by specific implementations
    DEFAULT_CONFIG = {
        "fetch_interval": 600,  # 10 minutes between cycles
        "scroll_times": 5,      # Number of times to scroll
        "headless": True,       # Run browser in headless mode
        "scroll_delay": 1.5,    # Delay between scrolls in seconds
        "cycle_duration": 590,   # Duration of scrolling in seconds
        "batch_size": 10,       # Number of items to process in a batch
        "max_items_per_cycle": 50,  # Maximum items to process per cycle
        "new_items_only": True  # Only process new items
    }
    
    def __init__(self, source_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base scraper
        
        Args:
            source_id: Identifier for what's being scraped (e.g., group ID, page URL)
            config: Optional configuration overrides
        """
        self.source_id = source_id
        self.source_url = self._get_source_url()
        
        # Apply configuration (default + overrides)
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
        
        # Browser components
        self.browser = None
        self.context = None
        self.page = None
        
        # State tracking
        self.running = False
        self._owns_browser = False
        self._user_id = None
        self._session = None
        self.processed_item_ids = set()
        
        # Batch processing state
        self.batch_items = []
        self.batch_texts = []
        
    @abstractmethod
    def _get_source_url(self) -> str:
        """
        Get the URL for the source being scraped.
        Must be implemented by specific scrapers.
        
        Returns:
            URL for the source being scraped
        """
        raise NotImplementedError("Subclasses must implement _get_source_url")
    
    async def initialize_with_session_data(self, session_data: Dict[str, Any], user_id: str):
        """
        Initialize the scraper with existing session data
        
        Args:
            session_data: Browser session data (cookies, storage, etc.)
            user_id: User identifier for browser management
        """
        self._user_id = user_id
        self._session = session_data
        
        # Get context from shared browser manager
        self.context = await SharedBrowserManager.get_context(
            user_id=user_id,
            session_data=session_data,
            headless=self.config.get("headless", False)
        )
        
        # Create a new page in this context
        self.page = await self.context.new_page()
        
        # Additional setup after page creation
        await self._setup_page()
        
        # Navigate to the source URL
        await self.page.goto(self.source_url)
        
        print(f"🚀 Initialized scraper for {self.source_id} (shared browser for user {user_id})")
    
    async def initialize(self, session_file: Optional[str] = None):
        """
        Initialize the scraper with a local session file
        
        Args:
            session_file: Optional path to session file
        """
        # Implementation depends on specific scraper
        pass
    
    async def _setup_page(self):
        """Set up the page with needed settings and event handlers"""
        if self.page:
            # Set timeout for navigation
            self.page.set_default_timeout(30000)
            
            # Add any common event handlers here
            pass
    
    async def scroll_page(self, distance=None, random_range=None, use_viewport_height=False, multiplier=1, delay=None):
        """
        Scroll the page by the specified parameters
        
        Args:
            distance: Exact pixel distance to scroll
            random_range: Tuple of (min, max) values to randomly choose a scroll distance
            use_viewport_height: Whether to use viewport height as the base for scrolling
            multiplier: Multiplier for viewport height
            delay: Time to wait after scrolling
            
        Returns:
            The actual scroll distance used
        """
        if self.page is None:
            print(f"⚠️ [{self.source_id}] Cannot scroll - page is not initialized")
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
            scroll_js = f"window.scrollBy(0, {scroll_distance or 300})"
            
        # Execute the scroll
        await self.page.evaluate(scroll_js)
        
        # Apply delay after scrolling
        actual_delay = delay if delay is not None else self.config["scroll_delay"]
        if actual_delay > 0:
            await asyncio.sleep(actual_delay)
            
        return scroll_distance
    
    async def check_for_new_items(self):
        """
        Check for new items on the page by continuously scrolling for cycle_duration
        The base implementation is generic - specific scrapers should override this
        if needed.
        """
        try:
            print(f"🔄 [{self.source_id}] Starting new items cycle with continuous scrolling...")
            
            # Make sure page exists before trying to use it
            if self.page is None:
                print(f"⚠️ [{self.source_id}] Page is not initialized")
                return
                
            # Refresh the page to get the latest items
            await self.page.reload()
            
            # Wait for items to load - this selector should be overridden in subclasses
            item_selector = await self._get_item_selector()
            await self.page.wait_for_selector(item_selector, timeout=10000)
            
            # Track start time
            start_time = asyncio.get_event_loop().time()
            end_time = start_time + self.config["cycle_duration"]
            
            # Get initial items
            item_elements = await self.page.query_selector_all(item_selector)
            print(f"👀 [{self.source_id}] Found {len(item_elements)} visible items initially")
            
            # Process the initial visible items
            await self.process_visible_items(item_elements, new_only=self.config.get("new_items_only", True))
            
            # Continue scrolling and processing until time runs out
            scroll_count = 0
            while asyncio.get_event_loop().time() < end_time:
                # Calculate remaining time
                remaining_time = end_time - asyncio.get_event_loop().time()
                print(f"⏱️ [{self.source_id}] Continuing to scroll for {remaining_time:.1f} more seconds (scroll #{scroll_count+1})")
                
                # Use the centralized scroll method with random distance
                scroll_distance = await self.scroll_page(random_range=(400, 800))
                
                # Get items after scrolling
                item_elements = await self.page.query_selector_all(item_selector)
                print(f"👀 [{self.source_id}] Found {len(item_elements)} visible items after scrolling")
                
                # Process the newly visible items
                await self.process_visible_items(item_elements, new_only=self.config.get("new_items_only", True))
                
                scroll_count += 1
                
                # Stop if we've reached max scroll times
                if scroll_count >= self.config["scroll_times"]:
                    print(f"🛑 [{self.source_id}] Reached max scroll times ({self.config['scroll_times']})")
                    break
                
            print(f"✅ [{self.source_id}] Completed continuous scrolling cycle with {scroll_count} scrolls over {self.config['cycle_duration']} seconds")
            
        except Exception as e:
            print(f"⚠️ [{self.source_id}] Error during continuous scrolling cycle: {e}")
    
    async def _get_item_selector(self) -> str:
        """
        Get the CSS selector for items on the page
        Should be overridden by specific scrapers
        
        Returns:
            CSS selector for items
        """
        return "div[data-item]"  # Default selector, should be overridden
        
    async def process_visible_items(self, item_elements, new_only=False):
        """
        Process visible items on the page
        
        Args:
            item_elements: List of page elements representing items
            new_only: Only process items that haven't been processed before
        """
        try:
            self.batch_items = []
            self.batch_texts = []
            
            # Limit the number of items to process
            max_items = min(len(item_elements), self.config.get("max_items_per_cycle", 30))
            processed_count = 0
            skipped_count = 0
            
            for idx in range(max_items):
                try:
                    item = item_elements[idx]
                    
                    # Extract item ID - this could be HTML or any other format
                    # depending on the scraper implementation
                    item_id = await self.extract_item_id(item)
                    
                    # Skip already processed items if new_only is True
                    if new_only and item_id and item_id in self.processed_item_ids:
                        skipped_count += 1
                        continue
                    
                    # Expand item content if needed (e.g., click "See more" buttons)
                    await self._expand_item_content(item)
                    
                    # Extract item data
                    data = await self.extract_item_data(item)
                    
                    # Skip invalid items based on implementation-specific criteria
                    if not await self._is_valid_item(data):
                        skipped_count += 1
                        continue
                    
                    # Add ID to data if not already present
                    if item_id and "id" not in data:
                        data["id"] = item_id
                    
                    # Log the item
                    print(f"📊 [{self.source_id}] Item data: ID={item_id}, {self._format_item_log(data)}")
                    
                    # Add to batch
                    self.batch_items.append(data)
                    
                    # Add text content if available for batch processing
                    if "text" in data:
                        self.batch_texts.append(data["text"])
                    
                    # Mark as processed
                    if item_id:
                        self.processed_item_ids.add(item_id)
                    
                    processed_count += 1
                    
                    # Process batch when it reaches size
                    if len(self.batch_items) >= self.config.get("batch_size", 10):
                        await self.process_batch()
                
                except Exception as e:
                    print(f"⚠️ [{self.source_id}] Error processing item at index {idx}: {e}")
            
            # Process any remaining items
            if self.batch_items:
                await self.process_batch()
            
            print(f"✅ [{self.source_id}] Processed {processed_count} items, skipped {skipped_count} items")
        
        except Exception as e:
            print(f"⚠️ [{self.source_id}] Error processing visible items: {e}")
    
    async def _expand_item_content(self, item):
        """
        Expand truncated content in an item (e.g., click "See more" buttons)
        Should be overridden by specific scrapers if needed
        
        Args:
            item: The item element to expand
        """
        # Default implementation does nothing
        pass
    
    async def _is_valid_item(self, data: Dict[str, Any]) -> bool:
        """
        Check if an item is valid based on its data
        Should be overridden by specific scrapers if needed
        
        Args:
            data: The extracted item data
            
        Returns:
            True if the item is valid, False otherwise
        """
        # Default implementation considers all items valid
        return True
    
    def _format_item_log(self, data: Dict[str, Any]) -> str:
        """
        Format item data for logging
        Should be overridden by specific scrapers if needed
        
        Args:
            data: The extracted item data
            
        Returns:
            Formatted string for logging
        """
        # Default implementation just returns ID
        return f"ID={data.get('id', 'Unknown')}"
    
    async def process_items(self, items):
        """
        Process scraped items (parse, transform, save)
        
        Args:
            items: List of items to process
        """
        if not items:
            return
        
        # Clear any existing batch
        self.batch_items = []
        self.batch_texts = []
        
        # Add items to batch
        for item in items:
            self.batch_items.append(item)
            if isinstance(item, dict) and "text" in item:
                self.batch_texts.append(item["text"])
            elif isinstance(item, str):
                self.batch_texts.append(item)
                self.batch_items[-1] = {"text": item}  # Convert string to dict
        
        # Process the batch
        if self.batch_items:
            await self.process_batch()
    
    async def process_batch(self):
        """Process the current batch of items"""
        if not self.batch_items:
            return
        
        saved_count = 0  # Initialize outside the try block
        
        try:
            print(f"🧠 [{self.source_id}] Processing batch of {len(self.batch_items)} items")
            
            # Process the batch with specific implementation
            batch_results = await self._process_batch_data(self.batch_items, self.batch_texts)
            
            # Process results and save to database
            saved_count = await self.process_batch_results(batch_results)
            
            # Log results based on saved count
            if saved_count > 0:
                print(f"🔄 [{self.source_id}] Batch processing complete. Successfully saved {saved_count} items.")
            else:
                print(f"ℹ️ [{self.source_id}] Batch processing complete. No valid items were saved.")
            
        except Exception as e:
            print(f"⚠️ [{self.source_id}] Error processing batch: {e}")
            
        finally:
            # Clear batch regardless of success or failure
            self.batch_items = []
            self.batch_texts = []
            
        return saved_count  # Return the result for potential use by caller
    
    async def _process_batch_data(self, items: List[Dict[str, Any]], texts: List[str]) -> List[Dict[str, Any]]:
        """
        Process batch data using the text processor
        
        Args:
            items: List of item data dictionaries
            texts: List of text content extracted from items
            
        Returns:
            List of processed results
        """
        try:
            # Process the batch with the text processor
            print(f"🧠 [{self.source_id}] Processing batch of {len(texts)} items with LLM")
            
            # Use the apartment system prompt by default
            # Subclasses can override this method if they need different prompts
            batch_results = await process_text_batch(texts, get_apartment_system_prompt())
            
            # Merge results with original items to preserve metadata
            for i, result in enumerate(batch_results):
                if i < len(items):
                    # Add any missing fields from original items
                    for key, value in items[i].items():
                        if key not in result or result[key] is None or result[key] == "":
                            result[key] = value
            
            return batch_results
        except Exception as e:
            print(f"⚠️ [{self.source_id}] Error in _process_batch_data: {e}")
            return []
    
    async def process_batch_results(self, batch_results: List[Dict[str, Any]]) -> int:
        """
        Process batch results and save to database
        
        Args:
            batch_results: List of processed results
            
        Returns:
            Number of successfully saved items
        """
        saved_count = 0
        
        for i, result in enumerate(batch_results):
            try:
                # Skip invalid results
                if not await self._is_valid_result(result):
                    continue
                
                # Prepare data for saving
                save_data = await self._prepare_save_data(result, i)
                
                # Save to database
                try:
                    await self.save_item_data(save_data)
                    saved_count += 1
                except Exception as save_error:
                    print(f"⚠️ [{self.source_id}] Failed to save item: {save_error}")
                
            except Exception as e:
                print(f"⚠️ [{self.source_id}] Error processing result {i}: {e}")
        
        if saved_count > 0:
            print(f"✅ [{self.source_id}] Saved {saved_count} new items to database")
        
        return saved_count
    
    async def _is_valid_result(self, result: Dict[str, Any]) -> bool:
        """
        Check if a batch result is valid
        Should be overridden by specific scrapers if needed
        
        Args:
            result: The processed result
            
        Returns:
            True if the result is valid, False otherwise
        """
        # Default implementation considers all results valid
        return True
    
    async def _prepare_save_data(self, result: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Prepare data for saving to database
        
        Args:
            result: The processed result
            index: The index of the result in the batch
            
        Returns:
            Data dictionary ready for saving
        """
        try:
            # Basic data that should be common across all scrapers
            # Specific scrapers should override this to add source-specific fields
            prepared_data = {
                "text": result.get("text", ""),
                "user": result.get("user", "Unknown"),
                "timestamp": result.get("timestamp", "Unknown"),
                "image_urls": result.get("images", []),
                "post_link": result.get("post_link", ""),
                "price": result.get("price", None),
                "location": result.get("location", ""),
                "phone_numbers": result.get("phone_numbers", []),
                "mentions": result.get("mentions", []),
                "summary": result.get("summary", ""),
                "post_id": result.get("post_id", ""),
                "is_valid": result.get("is_valid", True),
                # source should be set by specific scraper implementations
                # source: "facebook", "telegram", etc.
            }
            
            # Return the prepared data
            return prepared_data
        except Exception as e:
            print(f"⚠️ [{self.source_id}] Error preparing save data: {e}")
            return result  # Return original result as fallback
    
    @abstractmethod
    async def extract_item_id(self, item) -> str:
        """
        Extract a unique identifier from an item
        Must be implemented by specific scrapers
        
        Args:
            item: The item to extract an ID from
            
        Returns:
            Unique identifier for the item
        """
        raise NotImplementedError("Subclasses must implement extract_item_id")
    
    @abstractmethod
    async def extract_item_data(self, item) -> Dict[str, Any]:
        """
        Extract relevant data from an item
        Must be implemented by specific scrapers
        
        Args:
            item: The item to extract data from
            
        Returns:
            Dictionary of extracted data
        """
        raise NotImplementedError("Subclasses must implement extract_item_data")
    
    async def _extract_item_data_base(self, element, page=None) -> Dict[str, Any]:
        """
        Base method for extracting data from an item element using Playwright
        Uses template pattern with abstract methods for specific extraction parts
        
        Args:
            element: The Playwright element handle for the item
            page: The Playwright page object (optional)
            
        Returns:
            Dictionary with extracted item data
        """
        # If page is not provided, use the scraper's page
        if page is None and hasattr(self, 'page'):
            page = self.page
        
        # Extract text content
        text = await element.inner_text()
        
        # Initialize data dictionary with defaults
        item_data = {
            "text": text,
            "link": "Unknown",
            "timestamp": "Unknown",
            "user": "Unknown",
            "user_link": "Unknown"
        }
        
        try:
            # Extract specific data using abstract methods
            item_data["link"] = await self._extract_item_link(element, page)
            item_data["timestamp"] = await self._extract_item_timestamp(element, page)
            item_data["user"] = await self._extract_item_user(element, page)
            item_data["user_link"] = await self._extract_item_user_link(element, page)
            
            # Extract any additional data
            additional_data = await self._extract_additional_item_data(element, page)
            if additional_data:
                item_data.update(additional_data)
                
        except Exception as e:
            print(f"⚠️ [{self.source_id}] Error extracting item data: {e}")
        
        return item_data
        
    @abstractmethod
    async def _extract_item_link(self, element, page) -> str:
        """
        Extract the link/permalink for an item
        Must be implemented by specific scrapers
        
        Args:
            element: The element to extract the link from
            page: The Playwright page object
            
        Returns:
            Item link as string
        """
        raise NotImplementedError("Subclasses must implement _extract_item_link")
        
    @abstractmethod
    async def _extract_item_timestamp(self, element, page) -> str:
        """
        Extract the timestamp/date for an item
        Must be implemented by specific scrapers
        
        Args:
            element: The element to extract the timestamp from
            page: The Playwright page object
            
        Returns:
            Timestamp as string
        """
        raise NotImplementedError("Subclasses must implement _extract_item_timestamp")
        
    @abstractmethod
    async def _extract_item_user(self, element, page) -> str:
        """
        Extract the user/author name for an item
        Must be implemented by specific scrapers
        
        Args:
            element: The element to extract the user from
            page: The Playwright page object
            
        Returns:
            User name as string
        """
        raise NotImplementedError("Subclasses must implement _extract_item_user")
        
    @abstractmethod
    async def _extract_item_user_link(self, element, page) -> str:
        """
        Extract the user profile link for an item
        Must be implemented by specific scrapers
        
        Args:
            element: The element to extract the user link from
            page: The Playwright page object
            
        Returns:
            User profile link as string
        """
        raise NotImplementedError("Subclasses must implement _extract_item_user_link")
        
    async def _extract_additional_item_data(self, element, page) -> Dict[str, Any]:
        """
        Extract any additional data specific to the scraper implementation
        Should be implemented by specific scrapers that need additional data
        
        Args:
            element: The element to extract data from
            page: The Playwright page object
            
        Returns:
            Dictionary with additional extracted data
        """
        return {}
    
    async def load_processed_item_ids(self):
        """Load already processed item IDs from storage"""
        # Implementation depends on specific scraper and storage mechanism
        pass
    
    async def save_item_data(self, data: Dict[str, Any]):
        """
        Save item data to storage
        
        Args:
            data: Data to save
        """
        # Implementation depends on specific scraper and storage mechanism
        pass
    
    async def run(self, max_cycles=None):
        """
        Run the scraper in a loop
        
        Args:
            max_cycles: Maximum number of cycles to run (None for indefinite)
        """
        self.running = True
        cycle_count = 0
        
        try:
            # Navigation and setup logic
            if self.page is None:
                await self.initialize()
                
            if self.page is None:
                print(f"❌ [{self.source_id}] Page initialization failed")
                return
                
            # Navigate to the source URL
            await self.page.goto(self.source_url)
            
            # Load processed item IDs
            await self.load_processed_item_ids()
            
            # Main scraping loop
            while self.running and (max_cycles is None or cycle_count < max_cycles):
                # Track cycle start time
                cycle_start_time = asyncio.get_event_loop().time()
                
                cycle_count += 1
                print(f"🔄 [{self.source_id}] Starting cycle #{cycle_count}")
                
                try:
                    # Check for new items
                    await self.check_for_new_items()
                    
                    # Calculate time spent in this cycle
                    cycle_elapsed = asyncio.get_event_loop().time() - cycle_start_time
                    wait_time = max(0, self.config["fetch_interval"] - cycle_elapsed)
                    
                    # Sleep for remaining time until next cycle
                    if wait_time > 0:
                        print(f"⏳ [{self.source_id}] Cycle completed in {cycle_elapsed:.1f}s, waiting {wait_time:.1f}s until next cycle...\n")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"⚠️ [{self.source_id}] Cycle took {cycle_elapsed:.1f}s, which exceeds the fetch interval. Starting next cycle immediately.\n")
                    
                except Exception as e:
                    print(f"⚠️ [{self.source_id}] Error in cycle #{cycle_count}: {e}")
                    await asyncio.sleep(10)  # Wait before retrying
                    
        except Exception as e:
            print(f"❌ [{self.source_id}] Fatal error: {e}")
        finally:
            await self.cleanup()
            
    async def cleanup(self) -> None:
        """Clean up resources when scraper is done"""
        self.running = False
        
        try:
            if self._user_id:
                # Using shared browser - just release our reference
                # This method returns None, so it's awaitable
                await SharedBrowserManager.release(self._user_id)
            elif self._owns_browser:
                # We own the browser - close directly
                if self.context:
                    try:
                        await self.context.close()
                    except Exception as context_error:
                        print(f"⚠️ [{self.source_id}] Error closing context: {context_error}")
                
                # For the browser, instead of awaiting, we'll use a safer approach
                if self.browser:
                    # Non-awaited close to handle potential type issues
                    try:
                        self.browser.close()  # Deliberately not awaited
                    except Exception as browser_error:
                        print(f"⚠️ [{self.source_id}] Error closing browser: {browser_error}")
                    self.browser = None
        except Exception as e:
            print(f"⚠️ [{self.source_id}] Error during cleanup: {e}")
            
        print(f"🧹 Cleaned up resources for {self.source_id}")
    
    def stop(self):
        """Stop the scraper"""
        self.running = False
        print(f"🛑 [{self.source_id}] Stopping scraper") 