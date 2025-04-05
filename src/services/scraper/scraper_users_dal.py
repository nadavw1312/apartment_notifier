import json
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from src.services.scraper.scraper_users_models import ScraperUser

async def get_scraper_user_by_email_source(
    db: AsyncSession, 
    email: str, 
    source: str
) -> Optional[ScraperUser]:
    """Get a scraper user by email and source"""
    result = await db.execute(
        select(ScraperUser).where(
            (ScraperUser.email == email) & 
            (ScraperUser.source == source)
        )
    )
    return result.scalars().first()

async def get_scraper_user_by_id(
    db: AsyncSession, 
    user_id: int
) -> Optional[ScraperUser]:
    """Get a scraper user by ID"""
    result = await db.execute(select(ScraperUser).where(ScraperUser.id == user_id))
    return result.scalars().first()

async def add_scraper_user(
    db: AsyncSession, 
    email: str,
    source: str,
    password: Optional[str] = None,
    session_data: Optional[Dict[str, Any]] = None,
    is_active: bool = True
) -> ScraperUser:
    """Add a new scraper user to the database"""
    user = ScraperUser(
        email=email,
        source=source,
        password=password,
        session_data=json.dumps(session_data) if session_data else None,
        last_login=datetime.now().isoformat(),
        is_active=str(is_active).lower()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def update_session_data(
    db: AsyncSession, 
    email: str,
    source: str,
    session_data: Dict[str, Any]
) -> Optional[ScraperUser]:
    """Update session data for a user"""
    user = await get_scraper_user_by_email_source(db, email, source)
    
    if not user:
        return None
    
    user.session_data = json.dumps(session_data)
    user.last_login = datetime.now().isoformat()
    
    await db.commit()
    await db.refresh(user)
    return user

async def get_session_data_by_email_source(
    db: AsyncSession, 
    email: str,
    source: str
) -> Optional[Dict[str, Any]]:
    """Get session data for a user by email and source"""
    user = await get_scraper_user_by_email_source(db, email, source)
    
    if not user or not user.session_data:
        return None
    
    try:
        return json.loads(user.session_data)
    except json.JSONDecodeError:
        return None

async def update_user_active_status(
    db: AsyncSession, 
    email: str,
    source: str, 
    is_active: bool
) -> Optional[ScraperUser]:
    """Update user's active status"""
    user = await get_scraper_user_by_email_source(db, email, source)
    
    if not user:
        return None
    
    user.is_active = str(is_active).lower()
    await db.commit()
    await db.refresh(user)
    return user

async def get_all_active_users_by_source(
    db: AsyncSession,
    source: str
) -> List[ScraperUser]:
    """Get all active scraper users for a specific source"""
    result = await db.execute(
        select(ScraperUser).where(
            (ScraperUser.is_active == "true") &
            (ScraperUser.source == source)
        )
    )
    return list(result.scalars().all())

async def get_all_active_users(db: AsyncSession) -> List[ScraperUser]:
    """Get all active scraper users"""
    result = await db.execute(select(ScraperUser).where(ScraperUser.is_active == "true"))
    return list(result.scalars().all())

async def delete_scraper_user(
    db: AsyncSession, 
    email: str,
    source: str
) -> bool:
    """Delete a scraper user"""
    user = await get_scraper_user_by_email_source(db, email, source)
    
    if not user:
        return False
    
    await db.delete(user)
    await db.commit()
    return True 