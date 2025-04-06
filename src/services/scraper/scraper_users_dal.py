import json
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.sql import and_
from datetime import datetime
from src.services.scraper.scraper_users_models import ScraperUser

class ScraperUserDAL:
    """Data Access Layer for managing scraper users"""
    
    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession, 
        user_id: int
    ) -> Optional[ScraperUser]:
        """Get a scraper user by ID"""
        result = await db.execute(
            select(ScraperUser).where(ScraperUser.id == user_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_email_source(
        cls,
        db: AsyncSession, 
        email: str,
        source: str
    ) -> Optional[ScraperUser]:
        """Get a scraper user by email and source"""
        result = await db.execute(
            select(ScraperUser).where(
                and_(
                    ScraperUser.email == email,
                    ScraperUser.source == source
                )
            )
        )
        return result.scalars().first()

    @classmethod
    async def get_all(
        cls,
        db: AsyncSession
    ) -> List[ScraperUser]:
        """Get all scraper users"""
        result = await db.execute(select(ScraperUser))
        return list(result.scalars().all())

    @classmethod
    async def get_active(
        cls,
        db: AsyncSession
    ) -> List[ScraperUser]:
        """Get all active scraper users"""
        result = await db.execute(
            select(ScraperUser).where(ScraperUser.is_active == True)
        )
        return list(result.scalars().all())

    @classmethod
    async def add(
        cls,
        db: AsyncSession, 
        email: str,
        source: str,
        password: Optional[str] = None,
        is_active: bool = True,
        config: Optional[Dict[str, Any]] = None,
        session_data: Optional[Dict[str, Any]] = None
    ) -> ScraperUser:
        """Add a new scraper user"""
        user = ScraperUser(
            email=email,
            source=source,
            password=password,
            is_active=is_active,
            config=json.dumps(config) if config else None,
            session_data=json.dumps(session_data) if session_data else None,
            last_login=datetime.now().isoformat()
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def update(
        cls,
        db: AsyncSession, 
        user_id: int,
        **kwargs
    ) -> Optional[ScraperUser]:
        """Update a scraper user"""
        user = await cls.get_by_id(db, user_id)
        
        if not user:
            return None
        
        # Special handling for config and session_data which need to be JSON serialized
        if 'config' in kwargs and isinstance(kwargs['config'], dict):
            kwargs['config'] = json.dumps(kwargs['config'])
        if 'session_data' in kwargs and isinstance(kwargs['session_data'], dict):
            kwargs['session_data'] = json.dumps(kwargs['session_data'])
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def update_active_status(
        cls,
        db: AsyncSession, 
        user_id: int,
        is_active: bool
    ) -> Optional[ScraperUser]:
        """Update a user's active status"""
        return await cls.update(db, user_id, is_active=is_active)

    @classmethod
    async def delete(
        cls,
        db: AsyncSession, 
        user_id: int
    ) -> bool:
        """Delete a scraper user"""
        result = await db.execute(
            delete(ScraperUser).where(ScraperUser.id == user_id)
        )
        await db.commit()
        return result.rowcount > 0

    @classmethod
    async def save_session_data(
        cls,
        db: AsyncSession,
        user_id: int,
        session_data: Dict[str, Any]
    ) -> Optional[ScraperUser]:
        """Save session data for a scraper user"""
        return await cls.update(db, user_id, session_data=json.dumps(session_data))

    @classmethod
    async def get_session_data(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get session data for a scraper user"""
        user = await cls.get_by_id(db, user_id)
        if not user or not user.session_data:
            return None
        return json.loads(user.session_data)

    @classmethod
    async def get_active_by_source(
        cls,
        db: AsyncSession,
        source: str
    ) -> List[ScraperUser]:
        """Get all active scraper users for a specific source"""
        result = await db.execute(
            select(ScraperUser).where(
                and_(
                    ScraperUser.is_active == True,
                    ScraperUser.source == source
                )
            )
        )
        return list(result.scalars().all())

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
        is_active=is_active
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
    user = await ScraperUserDAL.get_by_email_source(db, email, source)
    
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
    user = await ScraperUserDAL.get_by_email_source(db, email, source)
    
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
    user = await ScraperUserDAL.get_by_email_source(db, email, source)
    
    if not user:
        return None
    
    user.is_active = is_active
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
            (ScraperUser.is_active == True) &
            (ScraperUser.source == source)
        )
    )
    return list(result.scalars().all())

async def get_all_active_users(db: AsyncSession) -> List[ScraperUser]:
    """Get all active scraper users"""
    result = await db.execute(select(ScraperUser).where(ScraperUser.is_active == True))
    return list(result.scalars().all())

async def delete_scraper_user(
    db: AsyncSession, 
    email: str,
    source: str
) -> bool:
    """Delete a scraper user"""
    user = await ScraperUserDAL.get_by_email_source(db, email, source)
    
    if not user:
        return False
    
    await db.delete(user)
    await db.commit()
    return True 