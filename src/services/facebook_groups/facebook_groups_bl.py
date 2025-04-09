from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.facebook_groups.facebook_groups_dal import FacebookGroupDAL
from src.services.facebook_groups.facebook_groups_models import FacebookGroup

class FacebookGroupBL:
    """Business Logic Layer for managing Facebook groups"""
    
    @classmethod
    async def get_group(
            cls,
            db: AsyncSession, 
            group_id: str
        ) -> Optional[FacebookGroup]:
            """Get a Facebook group by its ID"""
            return await FacebookGroupDAL.get_by_id(db, group_id)