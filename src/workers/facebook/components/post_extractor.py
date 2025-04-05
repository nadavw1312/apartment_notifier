"""Post extraction utilities for Facebook scraper."""

import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import ElementHandle, Page


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


async def extract_post_data_playwright(post, page, group_id):
    """
    Extract data from a post using Playwright
    
    Args:
        post: The Playwright element handle for the post
        page: The Playwright page object
        group_id: Group ID for logging purposes
        
    Returns:
        Dictionary with extracted post data
    """
    # Extract text content from the post
    text = await post.inner_text()
    
    # Extract post link, date/time, and user info
    post_link = "Unknown"
    post_date_time = "Unknown"
    user_name = "Unknown"
    user_link = "Unknown"
    
    # Use page directly to extract data
    try:
        # Ensure page exists
        if page is None:
            print(f"⚠️ [{group_id}] Page is None, cannot extract tooltip data")
            raise ValueError("Page is not initialized")
        
        # Find the post permalink
        permalink_element = await post.query_selector("a[href*='/posts/']")
        if permalink_element:
            # Save the permalink
            href = await permalink_element.get_attribute("href")
            if href and not href.startswith("http"):
                href = f"https://www.facebook.com{href}"
            post_link = href
            
            # Try to extract date/time from hover over permalink
            if await permalink_element.is_visible():
                # Hover over the permalink link to trigger tooltip
                await permalink_element.hover()
                await asyncio.sleep(0.5)
                
                # Check if there's a tooltip using page
                tooltip = await page.query_selector("div[role='tooltip']")
                
                if tooltip:
                    tooltip_text = await tooltip.inner_text()
                    post_date_time = tooltip_text.strip()
                    print(f"📅 [{group_id}] Found post date/time from permalink: {post_date_time}")
        
        # Try various selectors to find the username
        username_element = await post.query_selector("a[role='link'] strong span")
        if not username_element:
            username_element = await post.query_selector("a[aria-label] span")
        
        # Try to get the username from the found element
        if username_element:
            try:
                user_name = await username_element.inner_text()
                if user_name and len(user_name.strip()) > 0:
                    user_name = user_name.strip()
                    print(f"👤 [{group_id}] Found user name from span: {user_name}")
            except Exception as e:
                print(f"⚠️ [{group_id}] Error extracting username from span: {e}")
                
        # Find the user profile link
        user_link_element = await post.query_selector("a[href*='/user/']")

        # If we found a user link but still don't have a username, try to extract from the link
        if user_link_element:
            # Extract user profile link
            user_href = await user_link_element.get_attribute("href")
            if user_href and len(user_href) > 0:
                if not user_href.startswith("http"):
                    user_href = f"https://www.facebook.com{user_href}"
                user_link = user_href
                print(f"🔗 [{group_id}] Found user link: {user_link}")
                
    except Exception as e:
        print(f"⚠️ [{group_id}] Error extracting post data: {e}")
    
    return {
        "text": text,
        "post_link": post_link,
        "post_date_time": post_date_time,
        "user_name": user_name,
        "user_link": user_link
    }
