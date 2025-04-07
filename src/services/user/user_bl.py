from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.user.user_dal import UserDAL
from src.services.user.user_models import User

class UserBL:
    """Business Logic Layer for managing users"""
    
    @classmethod
    async def get_user(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Optional[User]:
        """Get a user by ID"""
        return await UserDAL.get_by_id(db, user_id)

    @classmethod
    async def get_user_by_email(
        cls,
        db: AsyncSession,
        email: str
    ) -> Optional[User]:
        """Get a user by email"""
        return await UserDAL.get_by_email(db, email)

    @classmethod
    async def get_all_users(
        cls,
        db: AsyncSession
    ) -> List[User]:
        """Get all users"""
        return await UserDAL.get_all(db)

    @classmethod
    async def get_active_users(
        cls,
        db: AsyncSession
    ) -> List[User]:
        """Get all active users"""
        return await UserDAL.get_active(db)

    @classmethod
    async def create_user(
        cls,
        db: AsyncSession,
        email: str,
        password: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> User:
        """Create a new user"""
        return await UserDAL.add(
            db=db,
            email=email,
            password=password,
            name=name,
            metadata=metadata
        )

    @classmethod
    async def update_user(
        cls,
        db: AsyncSession,
        user_id: int,
        **kwargs
    ) -> Optional[User]:
        """Update a user"""
        return await UserDAL.update(db, user_id, **kwargs)

    @classmethod
    async def delete_user(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> bool:
        """Delete a user"""
        return await UserDAL.delete(db, user_id)