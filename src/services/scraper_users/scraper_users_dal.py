import json
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.sql import and_
from datetime import datetime
from src.services.scraper_users.scraper_users_models import ScraperUser

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
    async def add(
        cls,
        db: AsyncSession, 
        email: str,
        source: str,
        password: Optional[str] = None,
        is_active: bool = True,
        session_data: Optional[Dict[str, Any]] = None
    ) -> ScraperUser:
        """Add a new scraper user"""
        user = ScraperUser(
            email=email,
            source=source,
            password=password,
            is_active=is_active,
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