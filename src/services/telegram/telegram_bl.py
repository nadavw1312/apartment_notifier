from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.telegram.telegram_dal import TelegramDAL
from src.services.telegram.telegram_models import TelegramUser

class TelegramBL:
    """Business Logic Layer for managing Telegram users"""
    
    @classmethod
    async def get_telegram_user(
        cls,
        db: AsyncSession,
        telegram_id: int
    ) -> Optional[TelegramUser]:
        """Get a Telegram user by ID"""
        return await TelegramDAL.get_by_id(db, telegram_id)

    @classmethod
    async def get_telegram_user_by_user_id(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> Optional[TelegramUser]:
        """Get a Telegram user by user ID"""
        return await TelegramDAL.get_by_user_id(db, user_id)

    @classmethod
    async def get_all_telegram_users(
        cls,
        db: AsyncSession
    ) -> List[TelegramUser]:
        """Get all Telegram users"""
        return await TelegramDAL.get_all(db)

    @classmethod
    async def get_active_telegram_users(
        cls,
        db: AsyncSession
    ) -> List[TelegramUser]:
        """Get all active Telegram users"""
        return await TelegramDAL.get_active(db)

    @classmethod
    async def create_telegram_user(
        cls,
        db: AsyncSession,
        user_id: int,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> TelegramUser:
        """Create a new Telegram user"""
        return await TelegramDAL.add(
            db=db,
            user_id=user_id,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            metadata=metadata,
            is_active=is_active
        )

    @classmethod
    async def update_telegram_user(
        cls,
        db: AsyncSession,
        telegram_id: int,
        **kwargs
    ) -> Optional[TelegramUser]:
        """Update a Telegram user"""
        return await TelegramDAL.update(db, telegram_id, **kwargs)

    @classmethod
    async def set_telegram_user_active(
        cls,
        db: AsyncSession,
        telegram_id: int,
        is_active: bool
    ) -> Optional[TelegramUser]:
        """Set a Telegram user's active status"""
        return await TelegramDAL.update_active_status(db, telegram_id, is_active)

    @classmethod
    async def delete_telegram_user(
        cls,
        db: AsyncSession,
        telegram_id: int
    ) -> bool:
        """Delete a Telegram user"""
        return await TelegramDAL.delete(db, telegram_id) 