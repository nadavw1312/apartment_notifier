from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy import and_

from src.services.notification.notification_models import Notification

class NotificationDAL:
    """Data Access Layer for managing notifications"""
    
    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        notification_id: int
    ) -> Optional[Notification]:
        """Get a notification by ID"""
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalars().first()

    @classmethod
    async def get_all(
        cls,
        db: AsyncSession
    ) -> List[Notification]:
        """Get all notifications"""
        result = await db.execute(select(Notification))
        return list(result.scalars().all())

    @classmethod
    async def get_active(
        cls,
        db: AsyncSession
    ) -> List[Notification]:
        """Get all active notifications"""
        result = await db.execute(
            select(Notification).where(Notification.is_active == True)
        )
        return list(result.scalars().all())

    @classmethod
    async def add(
        cls,
        db: AsyncSession,
        user_id: int,
        message: str,
        notification_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> Notification:
        """Add a new notification"""
        notification = Notification(
            user_id=user_id,
            message=message,
            notification_type=notification_type,
            metadata=metadata,
            is_active=is_active
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        notification_id: int,
        **kwargs
    ) -> Optional[Notification]:
        """Update a notification"""
        notification = await cls.get_by_id(db, notification_id)
        
        if not notification:
            return None
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(notification, key):
                setattr(notification, key, value)
        
        await db.commit()
        await db.refresh(notification)
        return notification

    @classmethod
    async def update_active_status(
        cls,
        db: AsyncSession,
        notification_id: int,
        is_active: bool
    ) -> Optional[Notification]:
        """Update a notification's active status"""
        return await cls.update(db, notification_id, is_active=is_active)

    @classmethod
    async def delete(
        cls,
        db: AsyncSession,
        notification_id: int
    ) -> bool:
        """Delete a notification"""
        result = await db.execute(
            delete(Notification).where(Notification.id == notification_id)
        )
        await db.commit()
        return result.rowcount > 0

    @classmethod
    async def get_by_user(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> List[Notification]:
        """Get all notifications for a user"""
        result = await db.execute(
            select(Notification).where(Notification.user_id == user_id)
        )
        return list(result.scalars().all())

    @classmethod
    async def get_active_by_user(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> List[Notification]:
        """Get all active notifications for a user"""
        result = await db.execute(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_active == True
                )
            )
        )
        return list(result.scalars().all()) 