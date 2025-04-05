"""Text filtering utilities for Facebook scraper."""

def is_apartment_post(text: str) -> bool:
    """
    Check if a post text contains apartment-related keywords
    
    Args:
        text: The post text to check
        
    Returns:
        Boolean indicating if this is likely an apartment post
    """
    keywords = ['דירה', 'להשכרה', 'חדר', 'סאבלט', 'שכירות']
    return any(keyword in text for keyword in keywords) 