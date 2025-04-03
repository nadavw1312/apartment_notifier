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
FB_EMAIL = "nadavb1999@gmail.com"
FB_PASSWORD = "29852064ss"
GROUP_ID = "423017647874807"
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
    text = await post.inner_text()

    image_elements = await post.query_selector_all("img")
    image_urls = [
        await img.get_attribute("src")
        for img in image_elements
        if (await img.get_attribute("src")) and "scontent" in await img.get_attribute("src")
    ]

    user = "Unknown"
    user_element = await post.query_selector("h2 a, strong a")
    if user_element:
        user = await user_element.inner_text()

    timestamp = "Unknown"
    time_element = await post.query_selector("a[aria-label], abbr[title], time")
    if time_element:
        timestamp = await time_element.get_attribute("aria-label") or await time_element.get_attribute("title")

    post_link = "Unknown"
    link_element = await post.query_selector("a[href*='/posts/']")
    if link_element:
        href = await link_element.get_attribute("href")
        if href and not href.startswith("http"):
            href = f"https://www.facebook.com{href}"
        post_link = href

    return {
        "text": text,
        "user": user,
        "timestamp": timestamp,
        "image_urls": image_urls,
        "post_link": post_link,
    }

# 🧠 BeautifulSoup extractor
def extract_post_data_soup(html: str):
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(separator="\n").strip()

    user_tag = soup.select_one("h2 a, strong a")
    user = user_tag.get_text(strip=True) if user_tag else "Unknown"

    time_tag = soup.select_one("a[aria-label], abbr[title], time")
    timestamp = time_tag.get("aria-label") or time_tag.get("title") if time_tag else "Unknown"

    image_tags = soup.find_all("img")
    image_urls = []
    for img in image_tags:
        if isinstance(img, Tag):
            src = img.get("src")
            if src and "scontent" in src:
                image_urls.append(src)

    post_link_tag = soup.select_one("a[href*='/posts/']")
    post_link = post_link_tag.get("href") if post_link_tag else "Unknown"

    if isinstance(post_link, list):  # Sometimes it's a list
        post_link = post_link[0]

    if post_link and isinstance(post_link, str) and not post_link.startswith("http"):
        post_link = f"https://www.facebook.com{post_link}"

    return {
        "text": text,
        "user": user,
        "timestamp": timestamp,
        "image_urls": image_urls,
        "post_link": post_link,
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
                await asyncio.sleep(0.5)
            
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
        
        print("🚀 Started fetching loop...")

        while True:
            print("🔄 Fetching new posts...")

            for i in range(SCROLL_TIMES):
                scroll_distance = random.randint(500, 1500)
                print(f"📜 Scrolling {i + 1}/{SCROLL_TIMES} by {scroll_distance}px")
                await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                await asyncio.sleep(random.uniform(1.5, 3.5))

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
                    
                    # First check if there's enough content to process
                    # Expand post content by clicking "ראה עוד" (See more) buttons
                    await expand_post_content(post)
                    
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
                    
                    # Process with LLM 
                    minified_html = minify_html(html)
                    llm_data = extract_full_post_data_from_html(minified_html)
                    
                    # Combine data
                    data = {
                        "text": llm_data["text"],
                        "user": llm_data["user"],
                        "timestamp": llm_data["timestamp"],
                        "image_urls": llm_data["images"],
                        "post_link": llm_data["post_link"],
                        "price": llm_data["price"],
                        "location": llm_data["location"],
                        "phone_numbers": llm_data["phone_numbers"],
                        "mentions": llm_data["mentions"],
                        "summary": llm_data["summary"],
                        "source": "facebook",
                        "group_id": GROUP_ID,
                    }
                    
                    
                    # Save to database if it's an apartment post
                    if is_apartment_post(data["text"]) or data["user"] != "":
                        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
                            await create_apartment(session, **data)
                            new_posts_count += 1
                            print(f"📝 Processed new post {new_posts_count}: {data['post_link']}")
                    
                    # Update the last processed index
                    last_processed_index = idx

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
        "4. text: The full human-readable content of the post (ignore layout, comments, ads, etc.).\n"
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
