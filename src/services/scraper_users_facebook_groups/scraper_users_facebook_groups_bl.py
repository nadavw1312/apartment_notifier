import json
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.scraper_users_facebook_groups.scraper_users_facebook_groups_dal import ScraperUserFacebookGroupDAL
from src.services.scraper_users_facebook_groups.scraper_users_facebook_groups_models import ScraperUserFacebookGroup
from src.services.scraper_users.scraper_users_bl import ScraperUserBL
from src.services.facebook_groups.facebook_groups_bl import FacebookGroupBL


class ScraperUserFacebookGroupBL:
    """Business Logic Layer for managing Facebook group associations with scraper users"""
    
    @classmethod
    async def assign_group_to_user(
        cls,
        db: AsyncSession, 
        user_id: int,
        group_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[ScraperUserFacebookGroup]:
        """
        Assign a Facebook group to a scraper user
        
        Args:
            db: Database session
            user_id: Scraper user ID
            group_id: Facebook group ID
            config: Optional configuration specific to this user-group assignment
            
        Returns:
            ScraperUserFacebookGroup if successful, None if user or group don't exist
        """
        # Verify user exists
        user = await ScraperUserBL.get_scraper_user(db, user_id)
        if not user:
            return None
        
        # Validate that group exists
        group = await FacebookGroupBL.get_group(db, group_id)
        if not group:
            return None
        
        # Create or get the association
        return await ScraperUserFacebookGroupDAL.add(db, user_id, group_id, config)
    

    @classmethod
    async def update_groups_from_config(
        cls,
        db: AsyncSession,
        user_id: int,
        group_configs: List[Dict[str, Any]],
        remove_unlisted: bool = False
    ) -> Dict[str, Any]:
        """
        Update a user's groups from configuration data
        
        Args:
            db: Database session
            user_id: Scraper user ID
            group_configs: List of group configurations
            remove_unlisted: If True, remove any groups not in the config
            
        Returns:
            Dictionary with added, updated, and removed counts
        """
        # Initialize counters
        result = {
            'added': 0,
            'updated': 0,
            'removed': 0
        }
        
        # Keep track of processed group IDs
        processed_ids = set()
        
        # Process each group in the config
        for group_config in group_configs:
            group_id = group_config.get('group_id')
            if not group_id:
                continue
            
            processed_ids.add(group_id)
            
            # Check if the assignment already exists
            existing = await ScraperUserFacebookGroupDAL.get_by_user_and_group(db, user_id, group_id)
            
            if existing:
                # Update existing assignment
                config = group_config.get('config')
                is_active = group_config.get('is_active', True)
                
                await ScraperUserFacebookGroupDAL.update(db, user_id, group_id, 
                                                       config=config, 
                                                       is_active=is_active)
                result['updated'] += 1
            else:
                # Create new assignment
                assignment = await cls.assign_group_to_user(
                    db, 
                    user_id, 
                    group_id, 
                    group_config.get('config')
                )
                if assignment:
                    result['added'] += 1
        
        # Remove groups not in the config if requested
        if remove_unlisted:
            existing_groups = await ScraperUserFacebookGroupDAL.get_groups_for_user(db, user_id)
            
            for group in existing_groups:
                if group.facebook_group_id not in processed_ids:
                    await ScraperUserFacebookGroupDAL.delete(db, user_id, group.facebook_group_id)
                    result['removed'] += 1
        
        return result 