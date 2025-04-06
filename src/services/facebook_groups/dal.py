import json
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from src.services.facebook_groups.models import FacebookGroup

class FacebookGroupDAL:
    """Data Access Layer for managing Facebook groups"""
    
    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession, 
        group_id: str
    ) -> Optional[FacebookGroup]:
        """Get a Facebook group by its ID"""
        result = await db.execute(
            select(FacebookGroup).where(FacebookGroup.group_id == group_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_all(
        cls,
        db: AsyncSession
    ) -> List[FacebookGroup]:
        """Get all Facebook groups"""
        result = await db.execute(select(FacebookGroup))
        return list(result.scalars().all())

    @classmethod
    async def get_active(
        cls,
        db: AsyncSession
    ) -> List[FacebookGroup]:
        """Get all active Facebook groups"""
        result = await db.execute(
            select(FacebookGroup).where(FacebookGroup.is_active == True)
        )
        return list(result.scalars().all())

    @classmethod
    async def add(
        cls,
        db: AsyncSession, 
        group_id: str,
        name: str,
        description: Optional[str] = None,
        url: Optional[str] = None,
        member_count: Optional[int] = None,
        privacy: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
        scroll_times: Optional[int] = 2,
        fetch_interval: Optional[int] = 300
    ) -> FacebookGroup:
        """Add a new Facebook group to the database"""
        group = FacebookGroup(
            group_id=group_id,
            name=name,
            description=description,
            url=url,
            member_count=member_count,
            privacy=privacy,
            category=category,
            is_active=is_active,
            scroll_times=scroll_times,
            fetch_interval=fetch_interval
        )
        db.add(group)
        await db.commit()
        await db.refresh(group)
        return group

    @classmethod
    async def update(
        cls,
        db: AsyncSession, 
        group_id: str,
        **kwargs
    ) -> Optional[FacebookGroup]:
        """Update a Facebook group"""
        group = await cls.get_by_id(db, group_id)
        
        if not group:
            return None
        
        # Update only the provided fields
        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)
        
        await db.commit()
        await db.refresh(group)
        return group

    @classmethod
    async def update_active_status(
        cls,
        db: AsyncSession, 
        group_id: str,
        is_active: bool
    ) -> Optional[FacebookGroup]:
        """Update a group's active status"""
        return await cls.update(db, group_id, is_active=is_active)

    @classmethod
    async def delete(
        cls,
        db: AsyncSession, 
        group_id: str
    ) -> bool:
        """Delete a Facebook group"""
        result = await db.execute(
            delete(FacebookGroup).where(FacebookGroup.group_id == group_id)
        )
        await db.commit()
        return result.rowcount > 0

    @classmethod
    async def get_by_config(
        cls,
        db: AsyncSession,
        **config_params
    ) -> List[FacebookGroup]:
        """Get groups matching specific configuration parameters"""
        query = select(FacebookGroup)
        
        # Add filters for each config parameter
        for key, value in config_params.items():
            if hasattr(FacebookGroup, key):
                query = query.where(getattr(FacebookGroup, key) == value)
        
        result = await db.execute(query)
        return list(result.scalars().all()) 