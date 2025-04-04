import json
import random
from playwright.async_api import async_playwright
import asyncio
from pathlib import Path
from src.db.sql_database import SQL_DB_MANAGER
import re
from bs4 import BeautifulSoup, Comment
from src.llms.deepseek_api import DeepSeekApi
from bs4.element import Tag
import htmlmin
from src.services.apartment.apartment_bl import create_apartment

# =================== 🔧 CONFIG ===================
FB_EMAIL = "dirot2411@gmail.com"
FB_PASSWORD = "dirotbot2025"
GROUP_ID = "333022240594651"
GROUP_URL = f"https://www.facebook.com/groups/{GROUP_ID}"
SESSION_FILE = "fb_session.json"
FETCH_INTERVAL = 10  # seconds
SCROLL_TIMES = 5
NUM_POSTS_TO_FETCH = 10
# ================================================

async def save_facebook_session():
    """Open browser to login manually and save session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.facebook.com/login")

        print("🔐 Please log in manually in the browser window.")
        print("👉 After login, press Enter here to save the session.")
        
        input("Press Enter to continue...")

        await context.storage_state(path=SESSION_FILE)
        await browser.close()
        print("✅ Session saved to", SESSION_FILE)

# Telegram dummy
async def send_telegram_message(message: str):
    print("📨 Sending to Telegram:", message)

# Keyword filter
def is_apartment_post(text: str) -> bool:
    keywords = ['דירה', 'להשכרה', 'חדר', 'סאבלט', 'שכירות']
    return any(keyword in text for keyword in keywords)

# Phone extractor
def extract_phone_numbers(text: str):
    return re.findall(r'05\d{8}', text)

# 🧠 Playwright extractor
async def extract_post_data_playwright(post):
    # Extract text content from the post
    text = await post.inner_text()
    
    # Extract post link
    post_link = "Unknown"
    link_element = await post.query_selector("a[href*='/posts/']")
    if link_element:
        href = await link_element.get_attribute("href")
        if href and not href.startswith("http"):
            href = f"https://www.facebook.com{href}"
        post_link = href
    
    return {
        "text": text,
        "post_link": post_link
    }

# 🧠 BeautifulSoup extractor
def extract_post_data_soup(html: str):
    soup = BeautifulSoup(html, "html.parser")
    
    # Extract text content with nice formatting
    text = soup.get_text(separator="\n").strip()
    
    # Extract post link
    post_link = "Unknown"
    post_link_tag = soup.select_one("a[href*='/posts/']")
    if post_link_tag:
        href = post_link_tag.get("href")
        if isinstance(href, list):  # Sometimes it's a list
            href = href[0]
        if href and isinstance(href, str) and not href.startswith("http"):
            href = f"https://www.facebook.com{href}"
        post_link = href
    
    return {
        "text": text,
        "post_link": post_link
    }

# Expand "See more" function
async def expand_post_content(post):
    """Click on 'ראה עוד' (See more) buttons to expand truncated content."""
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
            print("📖 Expanded 'See more' content")
                
    except Exception as e:
        print(f"⚠️ Error expanding post content: {e}")
    
    # Give a moment for any animations to complete
    await asyncio.sleep(0.3)

# 🔁 Main loop
async def fetch_group_posts_continuously():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=SESSION_FILE)
        page = await context.new_page()

        await page.goto(GROUP_URL)
        await page.wait_for_selector("div[role='feed']")
        await asyncio.sleep(5)

        # Track seen post links to avoid duplicates
        seen_links = set()
        # Track the highest index we've processed
        last_processed_index = -1
        
        # Initialize batch collection for posts
        batch_posts = []
        batch_texts = []
        batch_indices = []
        
        print("🚀 Started fetching loop...")

        while True:
            print("🔄 Fetching new posts...")

            for i in range(SCROLL_TIMES):
                scroll_distance = random.randint(400, 700)
                print(f"📜 Scrolling {i + 1}/{SCROLL_TIMES} by {scroll_distance}px")
                await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                await asyncio.sleep(random.uniform(1.5, 3.5))
                
                # Expand all visible posts after each scroll
                feed = await page.query_selector("div[role='feed']")
                if feed:
                    visible_posts = await feed.query_selector_all(":scope > div")
                    print(f"🔍 Found {len(visible_posts)} visible posts, expanding content...")
                    for post in visible_posts:
                        await expand_post_content(post)
                    print("✅ Expanded all visible posts")
                    await asyncio.sleep(1)  # Give time for expansion animations to complete

            feed = await page.query_selector("div[role='feed']")
            if feed is None:
                print("❌ No feed found")
                continue
            
            post_blocks = await feed.query_selector_all(":scope > div")
            post_count = len(post_blocks)
            print(f"✅ Found {post_count} post(s)")
            
            # Count new posts processed in this cycle
            new_posts_count = 0
            
            # Start processing from the next unprocessed index
            start_index = last_processed_index + 1
            
            # Check if we need to reset (feed possibly reloaded/changed)
            if start_index > post_count:
                print("🔄 Feed structure has changed, resetting index")
                start_index = 0
                last_processed_index = -1

            # Process only new posts (starting from last processed index)
            for idx in range(start_index, post_count):
                try:
                    post = post_blocks[idx]
                    
                    html = await post.inner_html()
                    if len(html) < 800:
                        # Mark as processed but skip further processing
                        last_processed_index = idx
                        continue
                    
                    if "טעינה..." in html:
                        print("❌ Post is still loading, skipping")
                        last_processed_index = idx
                        await asyncio.sleep(random.uniform(0, 1))
                        continue
                    
                    # Add post to batch for processing
                    minified_html = minify_html(html)
                    data_soup_obj = extract_post_data_soup(minified_html)
                    data_playwright_obj = await extract_post_data_playwright(post)
                    
                    # Store both versions of the text and the entire HTML
                    batch_posts.append({
                        "html": minified_html,
                        "data_soup": data_soup_obj,
                        "data_playwright": data_playwright_obj
                    })
                    batch_texts.append(data_soup_obj["text"])  # Use soup text for LLM
                    batch_indices.append(idx)
                    
                    # Process batch when it reaches size 10 or we're at the end
                    if len(batch_posts) >= 10 or idx == post_count - 1:
                        if batch_posts:
                            print(f"🔄 Processing batch of {len(batch_posts)} posts")
                            
                            try:
                                # Process all posts in the batch at once
                                batch_results = process_posts_batch(batch_texts)
                                
                                # Save the results to database
                                for i, result in enumerate(batch_results):
                                    # Get original post HTML for reference if needed
                                    original_post_data = batch_posts[i]
                                    original_post_link = original_post_data["data_soup"]["post_link"]
                                    
                                    # Prepare data for database
                                    data = {
                                        "text": result["text"],
                                        "user": result["user"],
                                        "timestamp": result["timestamp"],
                                        "image_urls": result.get("images", []),  # Use get with default for safety
                                        "post_link": original_post_link if original_post_link != "Unknown" else result["post_link"],
                                        "price": result["price"],
                                        "location": result["location"],
                                        "phone_numbers": result["phone_numbers"],
                                        "mentions": result["mentions"],
                                        "summary": result["summary"],
                                        "source": "facebook",
                                        "group_id": GROUP_ID,
                                        "is_valid": result["is_valid"]
                                    }
                                    
                                    # Save to database if it's an apartment post
                                    if is_apartment_post(data["text"]) or data["user"] != "":
                                        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
                                            await create_apartment(session, **data)
                                            new_posts_count += 1
                                            print(f"📝 Processed new post {new_posts_count}: {data['post_link']}")
                                    
                                    # Update the processed index
                                    last_processed_index = batch_indices[i]
                                
                            except Exception as e:
                                print(f"⚠️ Error processing batch: {e}")
                                # Mark all posts in batch as processed even if there was an error
                                if batch_indices:
                                    last_processed_index = batch_indices[-1]
                            
                            # Clear the batches
                            batch_posts = []
                            batch_texts = []
                            batch_indices = []
                
                except Exception as e:
                    print(f"⚠️ Error parsing post at index {idx}:", e)
                    # Still mark as processed even if there was an error
                    last_processed_index = idx

            print(f"✅ Processed {new_posts_count} new posts this cycle")
            print(f"📊 Current position: {last_processed_index + 1}/{post_count}")
            print(f"⏳ Waiting {FETCH_INTERVAL}s until next check...\n")
            await asyncio.sleep(FETCH_INTERVAL)
            
            # Check if we've processed all visible posts and need more scrolling
            if last_processed_index >= post_count - 3:
                print("🔄 Almost reached end of visible posts, will scroll more")

def clean_html_for_llm(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove irrelevant tags
    for tag in soup(["script", "style", "meta", "svg", "noscript", "iframe"]):
        tag.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    return soup.get_text(separator="\n", strip=True)

def minify_html(html: str) :
    minified_html = htmlmin.minify(html, remove_comments=True, remove_empty_space=True)
    return minified_html


def extract_full_post_data_from_html(html: str) -> dict:
    system_prompt = (
        "You are an intelligent HTML parser that extracts key data from a Facebook post's HTML source. "
        "Your job is to return a structured JSON object containing the following fields:\n\n"
        "1. user: The full name of the user who posted.\n"
        "2. timestamp: The date and time the post was uploaded.\n"
        "3. post_link: A direct permalink to the post if available.\n"
        "4. text: The full human-readable content of the post shuold be same content more orgnaized (ignore layout, comments, ads, etc.).\n"
        "5. price: The rent price or total cost if mentioned (in NIS).\n"
        "6. location: The location of the apartment if mentioned.\n"
        "7. phone_numbers: An array of phone numbers in the post (e.g. 05XXXXXXXX).\n"
        "8. images: An array of image URLs that are part of the post content (exclude icons and irrelevant assets).\n"
        "9. mentions: List of specific words or keywords like 'סאבלט', 'שכירות', etc.\n"
        "10. summary: A brief natural language summary(in Hebrew) of the post intent or offer.\n"
        "Return only a valid JSON object and nothing else. If any field cannot be found, set it to null or empty.\n"
    )
    response = DeepSeekApi.chat(html, system_prompt=system_prompt)
    if response is None:
        raise RuntimeError("DeepSeek API returned None")
    return json.loads(response)

def process_posts_batch(posts_data: list) -> list:
    """Process a batch of post texts and extract apartment data for each"""
    system_prompt = (
        "You are an intelligent text analyzer and HTML parser that extracts key data from Facebook posts. "
        "I will provide you with an array of Facebook post texts from apartment rental groups. "
        "Your job is to analyze each text and return an array of structured JSON objects IN THE SAME ORDER as the input array. "
        "The length of your output array must match the length of the input array. "
        "For each post text in the input array, extract the following information as a JSON object:\n\n"
        "1. user: The full name of the user who posted.\n"
        "2. timestamp: The date and time the post was uploaded.\n"
        "3. post_link: A direct permalink to the post if available.\n"
        "4. text: The full human-readable content of the post shuold be same content more orgnaized (ignore layout, comments, ads, etc.).\n"
        "6. price: The rent price or total cost if mentioned (in NIS).\n"
        "7. location: The location of the apartment if mentioned.\n"
        "8. phone_numbers: An array of phone numbers in the post (e.g. 05XXXXXXXX).\n"
        "9. images: An array of image URLs that are part of the post content (exclude icons and irrelevant assets).\n"
        "10. mentions: List of specific words or keywords like 'סאבלט', 'שכירות', etc.\n"
        "11. summary: A brief natural language summary(in Hebrew) of the post intent or offer.\n"
        "12. is_valid: A boolean value indicating if the post is a valid apartment post which meant that the user is offering an apartment (true) or not (false).\n"
        "Return ONLY a valid JSON array containing one object for each input text, in the same order. "
        "If any field cannot be found, set it to null or empty string/array.\n"
        "IMPORTANT: The output MUST be a JSON array with the same number of objects as the input array, in the same order.\n"
    )
    
    # Convert list of post texts to JSON string
    posts_json = json.dumps(posts_data, ensure_ascii=False)
    
    response = DeepSeekApi.chat(posts_json, system_prompt=system_prompt)
    if response is None:
        raise RuntimeError("DeepSeek API returned None")
    
    return json.loads(response)['output']

async def main():
    # Initialize the database
    await SQL_DB_MANAGER.init()

    if not Path(SESSION_FILE).exists():
        print("🔐 Facebook session not found. Launching manual login...")
        
        await save_facebook_session()
    else:
        print("📡 Using saved session to fetch group posts...")
        
        await fetch_group_posts_continuously()

    # Close the database
    await SQL_DB_MANAGER.close()

if __name__ == "__main__":
    asyncio.run(main())
