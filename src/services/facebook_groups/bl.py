from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.facebook_groups.dal import FacebookGroupDAL
from src.services.facebook_groups.models import FacebookGroup

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

    @classmethod
    async def get_all_groups(
        cls,
        db: AsyncSession
    ) -> List[FacebookGroup]:
        """Get all Facebook groups"""
        return await FacebookGroupDAL.get_all(db)

    @classmethod
    async def get_active_groups(
        cls,
        db: AsyncSession
    ) -> List[FacebookGroup]:
        """Get all active Facebook groups"""
        return await FacebookGroupDAL.get_active(db)

    @classmethod
    async def create_or_update_group(
        cls,
        db: AsyncSession, 
        group_id: str,
        name: str,
        **kwargs
    ) -> FacebookGroup:
        """Create a new Facebook group or update if it exists"""
        existing_group = await FacebookGroupDAL.get_by_id(db, group_id)
        
        if existing_group:
            # Update existing group
            kwargs['name'] = name  # Ensure name is updated
            return await FacebookGroupDAL.update(db, group_id, **kwargs)
        
        # Create new group
        return await FacebookGroupDAL.add(db, group_id, name, **kwargs)

    @classmethod
    async def set_group_active(
        cls,
        db: AsyncSession,
        group_id: str,
        is_active: bool
    ) -> Optional[FacebookGroup]:
        """Set a group's active status"""
        return await FacebookGroupDAL.update_active_status(db, group_id, is_active)

    @classmethod
    async def remove_group(
        cls,
        db: AsyncSession, 
        group_id: str
    ) -> bool:
        """Remove a Facebook group"""
        return await FacebookGroupDAL.delete(db, group_id)

    @classmethod
    async def update_group_metadata(
        cls,
        db: AsyncSession,
        group_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[FacebookGroup]:
        """Update a group's metadata (member count, privacy, etc.)"""
        valid_fields = ['name', 'description', 'url', 'member_count', 'privacy', 'category']
        
        # Filter metadata to include only valid fields
        update_data = {k: v for k, v in metadata.items() if k in valid_fields}
        
        return await FacebookGroupDAL.update(db, group_id, **update_data)

    @classmethod
    async def import_groups_from_config(
        cls,
        db: AsyncSession,
        groups_config: List[Dict[str, Any]]
    ) -> List[FacebookGroup]:
        """Import groups from configuration data"""
        imported_groups = []
        
        for group_data in groups_config:
            group_id = group_data.get('group_id')
            name = group_data.get('name', f'Group {group_id}')
            
            if not group_id:
                continue  # Skip groups without an ID
                
            # Extract configuration options
            config = group_data.get('config', {})
            group_kwargs = {
                'description': group_data.get('description'),
                'url': group_data.get('url', f"https://www.facebook.com/groups/{group_id}"),
                'is_active': group_data.get('is_active', True),
                'scroll_times': config.get('scroll_times'),
                'fetch_interval': config.get('fetch_interval')
            }
            
            # Create or update the group
            group = await cls.create_or_update_group(db, group_id, name, **group_kwargs)
            imported_groups.append(group)
            
        return imported_groups 