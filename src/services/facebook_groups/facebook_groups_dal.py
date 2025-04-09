import json
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from src.services.facebook_groups.facebook_groups_models import FacebookGroup

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