import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_

from src.services.scraper_users_facebook_groups.models import ScraperUserFacebookGroup

class ScraperUserFacebookGroupDAL:
    """Data Access Layer for managing Facebook group associations with scraper users"""
    
    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession, 
        id: int
    ) -> Optional[ScraperUserFacebookGroup]:
        """Get a user-group association by its ID"""
        result = await db.execute(
            select(ScraperUserFacebookGroup).where(ScraperUserFacebookGroup.id == id)
        )
        return result.scalars().first()

    @classmethod
    async def get_by_user_and_group(
        cls,
        db: AsyncSession, 
        user_id: int,
        group_id: str
    ) -> Optional[ScraperUserFacebookGroup]:
        """Get a user-group association by user and group IDs"""
        result = await db.execute(
            select(ScraperUserFacebookGroup).where(
                and_(
                    ScraperUserFacebookGroup.scraper_user_id == user_id,
                    ScraperUserFacebookGroup.facebook_group_id == group_id
                )
            )
        )
        return result.scalars().first()

    @classmethod
    async def get_groups_for_user(
        cls,
        db: AsyncSession, 
        user_id: int
    ) -> List[ScraperUserFacebookGroup]:
        """Get all groups associated with a user"""
        result = await db.execute(
            select(ScraperUserFacebookGroup).where(
                ScraperUserFacebookGroup.scraper_user_id == user_id
            )
        )
        return list(result.scalars().all())

    @classmethod
    async def get_active_groups_for_user(
        cls,
        db: AsyncSession, 
        user_id: int
    ) -> List[ScraperUserFacebookGroup]:
        """Get active groups associated with a user"""
        result = await db.execute(
            select(ScraperUserFacebookGroup).where(
                and_(
                    ScraperUserFacebookGroup.scraper_user_id == user_id,
                    ScraperUserFacebookGroup.is_active == True
                )
            )
        )
        return list(result.scalars().all())

    @classmethod
    async def get_users_for_group(
        cls,
        db: AsyncSession, 
        group_id: str
    ) -> List[ScraperUserFacebookGroup]:
        """Get all users associated with a group"""
        result = await db.execute(
            select(ScraperUserFacebookGroup).where(
                ScraperUserFacebookGroup.facebook_group_id == group_id
            )
        )
        return list(result.scalars().all())

    @classmethod
    async def add(
        cls,
        db: AsyncSession, 
        user_id: int,
        group_id: str,
        config: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> ScraperUserFacebookGroup:
        """Associate a user with a Facebook group"""
        # Check if association already exists
        existing = await cls.get_by_user_and_group(db, user_id, group_id)
        if existing:
            return existing
            
        # Create new association
        user_group = ScraperUserFacebookGroup(
            scraper_user_id=user_id,
            facebook_group_id=group_id,
            config=json.dumps(config) if config else None,
            is_active=is_active
        )
        db.add(user_group)
        await db.commit()
        await db.refresh(user_group)
        return user_group

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        user_id: int,
        group_id: str,
        config: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[ScraperUserFacebookGroup]:
        """Update a user-group association"""
        user_group = await cls.get_by_user_and_group(db, user_id, group_id)
        if not user_group:
            return None
            
        if config is not None:
            user_group.config = json.dumps(config)
        if is_active is not None:
            user_group.is_active = is_active
            
        await db.commit()
        await db.refresh(user_group)
        return user_group

    @classmethod
    async def update_active_status(
        cls,
        db: AsyncSession,
        user_id: int,
        group_id: str,
        is_active: bool
    ) -> Optional[ScraperUserFacebookGroup]:
        """Update the active status of a user-group association"""
        return await cls.update(db, user_id, group_id, is_active=is_active)

    @classmethod
    async def update_last_scraped(
        cls,
        db: AsyncSession,
        user_id: int,
        group_id: str
    ) -> Optional[ScraperUserFacebookGroup]:
        """Update the last scraped timestamp for a user-group association"""
        user_group = await cls.get_by_user_and_group(db, user_id, group_id)
        if not user_group:
            return None
            
        user_group.last_scraped = datetime.utcnow()
        await db.commit()
        await db.refresh(user_group)
        return user_group

    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        user_id: int,
        group_id: str
    ) -> bool:
        """Delete a user-group association"""
        result = await db.execute(
            delete(ScraperUserFacebookGroup).where(
                and_(
                    ScraperUserFacebookGroup.scraper_user_id == user_id,
                    ScraperUserFacebookGroup.facebook_group_id == group_id
                )
            )
        )
        await db.commit()
        return result.rowcount > 0

    @classmethod
    async def delete_all_for_user(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> int:
        """Delete all group associations for a user"""
        result = await db.execute(
            delete(ScraperUserFacebookGroup).where(
                ScraperUserFacebookGroup.scraper_user_id == user_id
            )
        )
        await db.commit()
        return result.rowcount 