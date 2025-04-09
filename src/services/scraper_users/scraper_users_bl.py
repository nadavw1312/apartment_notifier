import json
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.scraper_users.scraper_users_dal import ScraperUserDAL
from src.services.scraper_users.scraper_users_models import ScraperUser

# Facebook-specific constants
FACEBOOK_SOURCE = "facebook"

class ScraperUserBL:
    """Business Logic Layer for managing scraper users"""
    
    @classmethod
    async def get_scraper_user(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Optional[ScraperUser]:
        """Get a scraper user by ID"""
        return await ScraperUserDAL.get_by_id(db, user_id)

    @classmethod
    async def get_scraper_user_by_email_source(
        cls,
        db: AsyncSession,
        email: str,
        source: str
    ) -> Optional[ScraperUser]:
        """Get a scraper user by email and source"""
        return await ScraperUserDAL.get_by_email_source(db, email, source)

    @classmethod
    async def get_all_scraper_users(
        cls,
        db: AsyncSession
    ) -> List[ScraperUser]:
        """Get all scraper users"""
        return await ScraperUserDAL.get_all(db)

    @classmethod
    async def get_active_scraper_users(
        cls,
        db: AsyncSession
    ) -> List[ScraperUser]:
        """Get all active scraper users"""
        return await ScraperUserDAL.get_active(db)

    @classmethod
    async def create_scraper_user(
        cls,
        db: AsyncSession,
        email: str,
        source: str,
        password: Optional[str] = None,
        is_active: bool = True,
        session_data: Optional[Dict[str, Any]] = None
    ) -> ScraperUser:
        """Create a new scraper user"""
        return await ScraperUserDAL.add(
            db,
            email=email,
            source=source,
            password=password,
            is_active=is_active,
            session_data=session_data
        )

    @classmethod
    async def update_scraper_user(
        cls,
        db: AsyncSession,
        user_id: int,
        **kwargs
    ) -> Optional[ScraperUser]:
        """Update a scraper user"""
        return await ScraperUserDAL.update(db, user_id, **kwargs)

    @classmethod
    async def set_scraper_user_active(
        cls,
        db: AsyncSession,
        user_id: int,
        is_active: bool
    ) -> Optional[ScraperUser]:
        """Update a scraper user's active status"""
        return await ScraperUserDAL.update_active_status(db, user_id, is_active)

    @classmethod
    async def delete_scraper_user(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """Delete a scraper user"""
        return await ScraperUserDAL.delete(db, user_id)

    @classmethod
    async def save_user_session_data(
        cls,
        db: AsyncSession,
        user_id: int,
        session_data: Dict[str, Any]
    ) -> Optional[ScraperUser]:
        """Save session data for a scraper user"""
        return await ScraperUserDAL.save_session_data(db, user_id, session_data)

    @classmethod
    async def get_user_session_data(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get session data for a scraper user"""
        return await ScraperUserDAL.get_session_data(db, user_id)

    @classmethod
    async def get_active_scraper_users_by_source(
        cls,
        db: AsyncSession,
        source: str
    ) -> List[ScraperUser]:
        """Get all active scraper users for a specific source"""
        return await ScraperUserDAL.get_active_by_source(db, source)

    @classmethod
    async def create_facebook_user(
        cls,
        db: AsyncSession,
        email: str,
        password: str,
        is_active: bool = True
    ) -> ScraperUser:
        """Create a new Facebook scraper user"""
        return await cls.create_scraper_user(
            db,
            email=email,
            source='facebook',
            password=password,
            is_active=is_active
        )

    @classmethod
    async def get_facebook_session_data(
        cls,
        db: AsyncSession,
        email: str
    ) -> Optional[Dict[str, Any]]:
        """Get session data for a Facebook user"""
        user = await cls.get_scraper_user_by_email_source(db, email, 'facebook')
        if not user:
            return None
        return await cls.get_user_session_data(db, user.id)

    @classmethod
    async def save_facebook_session_data(
        cls,
        db: AsyncSession,
        email: str,
        session_data: Dict[str, Any]
    ) -> Optional[ScraperUser]:
        """Save session data for a Facebook user"""
        user = await cls.get_scraper_user_by_email_source(db, email, 'facebook')
        if not user:
            return None
        return await cls.save_user_session_data(db, user.id, session_data)

    @classmethod
    async def set_facebook_user_active(
        cls,
        db: AsyncSession,
        email: str,
        is_active: bool
    ) -> Optional[ScraperUser]:
        """Set active status for a Facebook user"""
        user = await cls.get_scraper_user_by_email_source(db, email, 'facebook')
        if not user:
            return None
        return await cls.set_scraper_user_active(db, user.id, is_active)

    @classmethod
    async def create_or_update_scraper_user(
        cls,
        db: AsyncSession,
        email: str,
        source: str,
        password: Optional[str] = None,
        is_active: bool = True
    ) -> ScraperUser:
        """Create a new scraper user or update if exists"""
        existing_user = await cls.get_scraper_user_by_email_source(db, email, source)
        
        if existing_user:
            # Update existing user
            return await cls.update_scraper_user(
                db,
                existing_user.id,
                password=password,
                is_active=is_active
            )
        
        # Create new user
        return await cls.create_scraper_user(
            db,
            email=email,
            source=source,
            password=password,
            is_active=is_active
        )

    @classmethod
    async def save_scraper_user_session_data(
        cls,
        db: AsyncSession,
        email: str,
        source: str,
        session_data: Dict[str, Any]
    ) -> ScraperUser:
        """Save session data for a user, creating the user if it doesn't exist"""
        existing_user = await cls.get_scraper_user_by_email_source(db, email, source)
        
        if existing_user:
            return await cls.save_user_session_data(db, existing_user.id, session_data)
        
        # Create new user with session data
        return await cls.create_scraper_user(
            db,
            email=email,
            source=source,
            session_data=session_data
        )

    @classmethod
    async def get_scraper_user_session_data(
        cls,
        db: AsyncSession,
        email: str,
        source: str
    ) -> Optional[Dict[str, Any]]:
        """Get session data for a user"""
        user = await cls.get_scraper_user_by_email_source(db, email, source)
        if not user:
            return None
        return await cls.get_user_session_data(db, user.id)

    @classmethod
    async def get_active_facebook_users(
        cls,
        db: AsyncSession
    ) -> List[ScraperUser]:
        """Get all active Facebook users"""
        return await cls.get_active_scraper_users_by_source(db, 'facebook')

    @classmethod
    async def create_or_update_session_data(
        cls,
        db: AsyncSession,
        email: str,
        source: str,
        session_data: Dict[str, Any]
    ) -> Optional[ScraperUser]:
        """Create or update session data for a scraper user.
        If user doesn't exist, creates a new user with the session data.
        If user exists, updates their session data.
        
        Args:
            db: Database session
            email: User's email
            source: Source platform (e.g., 'facebook')
            session_data: Session data to store
            
        Returns:
            Updated or created ScraperUser, or None if operation failed
        """
        # Try to get existing user
        user = await cls.get_scraper_user_by_email_source(db, email, source)
        
        if user:
            # Update existing user's session data
            return await cls.save_user_session_data(db, user.id, session_data)
        else:
            # Create new user with session data
            return await cls.create_scraper_user(
                db,
                email=email,
                source=source,
                session_data=session_data
            )
