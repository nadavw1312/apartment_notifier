from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from src.services.telegram.telegram_models import TelegramUser

class TelegramDAL:
    """Data Access Layer for managing Telegram users"""
    
    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        telegram_id: int
    ) -> Optional[TelegramUser]:
        """Get a Telegram user by ID"""
        result = await db.execute(
            select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_active(
        cls,
        db: AsyncSession
    ) -> List[TelegramUser]:
        """Get all active Telegram users"""
        result = await db.execute(
            select(TelegramUser).where(TelegramUser.is_active == True)
        )
        return list(result.scalars().all())

    @classmethod
    async def add(
        cls,
        db: AsyncSession,
        user_id: int,
        telegram_id: int
    ) -> TelegramUser:
        """Add a new Telegram user"""
        telegram_user = TelegramUser(
            user_id=user_id,
            telegram_id=telegram_id
        )
        db.add(telegram_user)
        await db.commit()
        await db.refresh(telegram_user)
        return telegram_user

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        telegram_id: int,
        **kwargs
    ) -> Optional[TelegramUser]:
        """Update a Telegram user"""
        telegram_user = await cls.get_by_id(db, telegram_id)
        
        if not telegram_user:
            return None
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(telegram_user, key):
                setattr(telegram_user, key, value)
        
        await db.commit()
        await db.refresh(telegram_user)
        return telegram_user

    @classmethod
    async def update_active_status(
        cls,
        db: AsyncSession,
        telegram_id: int,
        is_active: bool
    ) -> Optional[TelegramUser]:
        """Update a Telegram user's active status"""
        return await cls.update(db, telegram_id, is_active=is_active)

    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        telegram_id: int
    ) -> bool:
        """Delete a Telegram user"""
        result = await db.execute(
            delete(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        )
        await db.commit()
        return result.rowcount > 0 