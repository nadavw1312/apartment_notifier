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
        telegram_id: int
    ) -> TelegramUser:
        """Create a new Telegram user"""
        return await TelegramDAL.add(
            db=db,
            user_id=user_id,
            telegram_id=telegram_id
        )