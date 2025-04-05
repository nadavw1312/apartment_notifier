import json
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.scraper.scraper_users_dal import (
    add_scraper_user, 
    update_session_data, 
    get_session_data_by_email_source,
    get_scraper_user_by_email_source,
    get_scraper_user_by_id,
    update_user_active_status,
    get_all_active_users,
    get_all_active_users_by_source,
    delete_scraper_user
)
from src.services.scraper.scraper_users_models import ScraperUser

# Facebook-specific constants
FACEBOOK_SOURCE = "facebook"

async def create_scraper_user(
    db: AsyncSession, 
    email: str, 
    source: str,
    password: Optional[str] = None,
    session_data: Optional[Dict[str, Any]] = None,
    is_active: bool = True
) -> ScraperUser:
    """Create a new scraper user or update if exists"""
    existing_user = await get_scraper_user_by_email_source(db, email, source)
    
    if existing_user:
        # Update existing user
        if password is not None:
            existing_user.password = password
        if session_data is not None:
            existing_user.session_data = json.dumps(session_data)
        existing_user.is_active = str(is_active).lower()
        await db.commit()
        await db.refresh(existing_user)
        return existing_user
    
    # Create new user
    return await add_scraper_user(db, email, source, password, session_data, is_active)

async def create_facebook_scraper_user(
    db: AsyncSession, 
    email: str, 
    password: Optional[str] = None,
    session_data: Optional[Dict[str, Any]] = None,
    is_active: bool = True
) -> ScraperUser:
    """Create a new Facebook scraper user"""
    return await create_scraper_user(db, email, FACEBOOK_SOURCE, password, session_data, is_active)

async def save_session_data(
    db: AsyncSession, 
    email: str,
    source: str,
    session_data: Dict[str, Any]
) -> ScraperUser:
    """Save session data for a user, creating the user if it doesn't exist"""
    existing_user = await get_scraper_user_by_email_source(db, email, source)
    
    if existing_user:
        return await update_session_data(db, email, source, session_data)
    
    # Create new user with session data
    return await add_scraper_user(db, email, source, session_data=session_data)

async def save_facebook_session_data(
    db: AsyncSession, 
    email: str,
    session_data: Dict[str, Any]
) -> ScraperUser:
    """Save Facebook session data for a user"""
    return await save_session_data(db, email, FACEBOOK_SOURCE, session_data)

async def get_session_data(
    db: AsyncSession, 
    email: str,
    source: str
) -> Optional[Dict[str, Any]]:
    """Get session data for a user"""
    return await get_session_data_by_email_source(db, email, source)

async def get_facebook_session_data(
    db: AsyncSession, 
    email: str
) -> Optional[Dict[str, Any]]:
    """Get Facebook session data for a user"""
    return await get_session_data(db, email, FACEBOOK_SOURCE)

async def set_user_active(
    db: AsyncSession, 
    email: str,
    source: str,
    is_active: bool
) -> Optional[ScraperUser]:
    """Set user active status"""
    return await update_user_active_status(db, email, source, is_active)

async def set_facebook_user_active(
    db: AsyncSession, 
    email: str,
    is_active: bool
) -> Optional[ScraperUser]:
    """Set Facebook user active status"""
    return await set_user_active(db, email, FACEBOOK_SOURCE, is_active)

async def get_active_users_by_source(
    db: AsyncSession, 
    source: str
) -> List[ScraperUser]:
    """Get all active users for a specific source"""
    return await get_all_active_users_by_source(db, source)

async def get_active_facebook_users(
    db: AsyncSession
) -> List[ScraperUser]:
    """Get all active Facebook users"""
    return await get_active_users_by_source(db, FACEBOOK_SOURCE)

async def get_all_active_scraper_users(
    db: AsyncSession
) -> List[ScraperUser]:
    """Get all active users from all sources"""
    return await get_all_active_users(db)

async def remove_scraper_user(
    db: AsyncSession, 
    email: str,
    source: str
) -> bool:
    """Remove a scraper user"""
    return await delete_scraper_user(db, email, source)

async def remove_facebook_scraper_user(
    db: AsyncSession, 
    email: str
) -> bool:
    """Remove a Facebook scraper user"""
    return await remove_scraper_user(db, email, FACEBOOK_SOURCE) 