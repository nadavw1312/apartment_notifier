import json
from typing import Dict, Any, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.scraper_users_facebook_groups.dal import ScraperUserFacebookGroupDAL
from src.services.scraper_users_facebook_groups.models import ScraperUserFacebookGroup
from src.services.scraper_users.scraper_users_bl import ScraperUserBL
from src.services.facebook_groups.bl import FacebookGroupBL


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
    async def get_user_groups(
        cls,
        db: AsyncSession, 
        user_id: int,
        active_only: bool = False
    ) -> List[ScraperUserFacebookGroup]:
        """
        Get all groups associated with a user
        
        Args:
            db: Database session
            user_id: Scraper user ID
            active_only: If True, return only active assignments
            
        Returns:
            List of ScraperUserFacebookGroup 
        """
        if active_only:
            return await ScraperUserFacebookGroupDAL.get_active_groups_for_user(db, user_id)
        else:
            return await ScraperUserFacebookGroupDAL.get_groups_for_user(db, user_id)

    @classmethod
    async def get_group_users(
        cls,
        db: AsyncSession, 
        group_id: str
    ) -> List[ScraperUserFacebookGroup]:
        """Get all users associated with a group"""
        return await ScraperUserFacebookGroupDAL.get_users_for_group(db, group_id)

    @classmethod
    async def update_group_config(
        cls,
        db: AsyncSession,
        user_id: int,
        group_id: str,
        config: Dict[str, Any]
    ) -> Optional[ScraperUserFacebookGroup]:
        """Update the configuration for a user-group association"""
        return await ScraperUserFacebookGroupDAL.update(db, user_id, group_id, config=config)

    @classmethod
    async def set_group_active(
        cls,
        db: AsyncSession,
        user_id: int,
        group_id: str,
        is_active: bool
    ) -> Optional[ScraperUserFacebookGroup]:
        """Set the active status for a user-group association"""
        return await ScraperUserFacebookGroupDAL.update_active_status(db, user_id, group_id, is_active)

    @classmethod
    async def update_last_scraped(
        cls,
        db: AsyncSession,
        user_id: int,
        group_id: str
    ) -> Optional[ScraperUserFacebookGroup]:
        """Update the last scraped timestamp for a user-group association"""
        return await ScraperUserFacebookGroupDAL.update_last_scraped(db, user_id, group_id)

    @classmethod
    async def remove_group_from_user(
        cls,
        db: AsyncSession,
        user_id: int,
        group_id: str
    ) -> bool:
        """Remove a group association from a user"""
        return await ScraperUserFacebookGroupDAL.delete(db, user_id, group_id)

    @classmethod
    async def remove_all_groups_from_user(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> int:
        """Remove all group associations from a user"""
        return await ScraperUserFacebookGroupDAL.delete_all_for_user(db, user_id)

    @classmethod
    async def get_user_group_assignment(
        cls,
        db: AsyncSession, 
        user_id: int,
        group_id: str
    ) -> Optional[ScraperUserFacebookGroup]:
        """Get a user-group assignment"""
        return await ScraperUserFacebookGroupDAL.get_by_user_and_group(db, user_id, group_id)

    @classmethod
    async def assign_groups_to_user(
        cls,
        db: AsyncSession, 
        user_id: int,
        group_configs: List[Dict[str, Any]]
    ) -> List[ScraperUserFacebookGroup]:
        """
        Assign multiple groups to a user at once
        
        Args:
            db: Database session
            user_id: Scraper user ID
            group_configs: List of group configurations, each with at least a 'group_id' field
            
        Returns:
            List of created/updated ScraperUserFacebookGroup objects
        """
        results = []
        
        for group_config in group_configs:
            group_id = group_config.get('group_id')
            if not group_id:
                continue
            
            # Extract configuration
            config = group_config.get('config')
            
            # Create assignment
            assignment = await cls.assign_group_to_user(db, user_id, group_id, config)
            if assignment:
                results.append(assignment)
            
        return results

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