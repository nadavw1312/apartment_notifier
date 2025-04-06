"""Post extraction utilities for Facebook scraper."""

import asyncio
from playwright.async_api import ElementHandle


async def expand_post_content(post, group_id):
    """
    Click on 'ראה עוד' (See more) buttons to expand truncated content.
    
    Args:
        post: The Playwright element handle for the post
        group_id: Group ID for logging purposes
        
    Returns:
        True if any content was expanded, False otherwise
    """
    try:
        see_more_buttons = await post.query_selector_all("//div[@role='button'][contains(text(), 'ראה עוד') or contains(text(), 'See more')]")
        clicked = False
            
        for button in see_more_buttons:
            if await button.is_visible():
                await button.click(force=True)
                clicked = True
                # Wait for content to expand
                await asyncio.sleep(0.8)
            
        if clicked:
            print(f"📖 [{group_id}] Expanded 'See more' content")
            return True
                
    except Exception as e:
        print(f"⚠️ [{group_id}] Error expanding post content: {e}")
    
    # Give a moment for any animations to complete
    await asyncio.sleep(0.3)
    return False
