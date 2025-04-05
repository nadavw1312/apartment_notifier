"""HTML parsing utilities for Facebook scraper."""

import re
from typing import Optional


def extract_post_id(html: str) -> Optional[str]:
    """
    Extract the post ID from the HTML
    
    Args:
        html: The HTML content of the post
        
    Returns:
        The post ID or None if not found
    """
    try:
        # Try to extract post ID from link
        post_link_match = re.search(r'\/posts\/(\d+)', html)
        if post_link_match:
            return post_link_match.group(1)
        
        # Alternative: try to find ID in data attributes
        data_id_match = re.search(r'data-ft="([^"]*)"', html)
        if data_id_match:
            data_ft = data_id_match.group(1)
            top_level_match = re.search(r'"top_level_post_id":"(\d+)"', data_ft)
            if top_level_match:
                return top_level_match.group(1)
        
        # Look for permalink patterns
        permalink_match = re.search(r'permalink\/(\d+)', html)
        if permalink_match:
            return permalink_match.group(1)
        
        return None
    except Exception:
        return None 