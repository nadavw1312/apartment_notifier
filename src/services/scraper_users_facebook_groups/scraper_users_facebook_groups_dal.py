import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_

from src.services.scraper_users_facebook_groups.scraper_users_facebook_groups_models import ScraperUserFacebookGroup

class ScraperUserFacebookGroupDAL:
    """Data Access Layer for managing Facebook group associations with scraper users"""
    

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