"""
Initialize scrapers database from configuration file.
Reads central scraper_config.json and inserts/updates users and their groups.
"""
import asyncio
import json
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.sql_database import SQL_DB_MANAGER
from src.services.scraper.scraper_users_bl import ScraperUserBL
from src.services.scraper_users_facebook_groups.bl import ScraperUserFacebookGroupBL

# Central config path
CENTRAL_CONFIG_PATH = "config/scraper_config.json"

async def update_facebook_user_groups(db_session: AsyncSession, email: str, groups: List[Dict[str, Any]]):
    """Update Facebook groups for a user"""
    # Get user by email
    user = await ScraperUserBL.get_scraper_user_by_email_source(db_session, email, "facebook")
    if not user:
        return

    # Update groups
    await ScraperUserFacebookGroupBL.update_groups_from_config(
        db_session,
        user.id,
        groups,
        remove_unlisted=True
    )

async def init_facebook_users(db_session: AsyncSession, config: Dict[str, Any]):
    """Initialize Facebook users from config"""
    facebook_config = config.get("facebook", {})
    users = facebook_config.get("users", [])

    for user_config in users:
        email = user_config.get("email")
        password = user_config.get("password")
        groups = user_config.get("groups", [])
        
        if not email or not password:
            print(f"⚠️ Skipping user - missing email or password")
            continue
            
        # Check if user exists
        existing_user = await ScraperUserBL.get_scraper_user_by_email_source(
            db_session, email, "facebook"
        )
        
        if existing_user:
            print(f"✅ User {email} already exists")
            # Update groups
            await update_facebook_user_groups(db_session, email, groups)
        else:
            # Create new user
            print(f"🆕 Creating new user {email}")
            await ScraperUserBL.create_facebook_user(
                db_session, 
                email, 
                password,
                is_active=True,
                config={"groups": groups}
            )

async def init_from_central_config():
    """
    Initialize all platform users from the central config file
    """
    # Load the configuration file
    try:
        with open(CENTRAL_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"✅ Loaded central configuration from {CENTRAL_CONFIG_PATH}")
    except Exception as e:
        print(f"⚠️ Error loading central configuration: {e}")
        return
    
    try:
        # Use transaction session for all operations
        async with SQL_DB_MANAGER.get_session_with_transaction() as db_session:
            # Process Facebook users
            await init_facebook_users(db_session, config)
            
            # Process other platforms here as they are added
            # await init_other_platform_users(db_session, config)
            
            print("✅ All users from central configuration initialized successfully")
    
    except Exception as e:
        print(f"⚠️ Error initializing users from central configuration: {e}")

async def main():
    """Main entry point"""
    # Initialize database once
    await SQL_DB_MANAGER.init()
    
    # Run initialization
    await init_from_central_config()

if __name__ == "__main__":          
    asyncio.run(main())
