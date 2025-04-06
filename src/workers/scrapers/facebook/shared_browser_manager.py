"""
This file is no longer needed as the browser management functionality 
has been moved to src/workers/scrappers/base/browser_manager.py.

This file is kept as a placeholder to maintain compatibility with 
existing imports, but will be removed in a future update.
"""

# Import the shared browser manager from the base module
from src.workers.scrapers.base.browser_manager import SharedBrowserManager

# Re-export the manager for backwards compatibility
__all__ = ['SharedBrowserManager'] 