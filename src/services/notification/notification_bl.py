# TODO: implement notification_bl.py

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.notification.notification_dal import NotificationDAL
from src.services.notification.notification_models import Notification

class NotificationBL:
    """Business Logic Layer for managing notifications"""
    
    @classmethod
    async def get_notification(
        cls,
        db: AsyncSession,
        notification_id: int
    ) -> Optional[Notification]:
        """Get a notification by ID"""
        return await NotificationDAL.get_by_id(db, notification_id)

    @classmethod
    async def get_all_notifications(
        cls,
        db: AsyncSession
    ) -> List[Notification]:
        """Get all notifications"""
        return await NotificationDAL.get_all(db)

    @classmethod
    async def get_active_notifications(
        cls,
        db: AsyncSession
    ) -> List[Notification]:
        """Get all active notifications"""
        return await NotificationDAL.get_active(db)

    @classmethod
    async def create_notification(
        cls,
        db: AsyncSession,
        user_id: int,
        message: str,
        notification_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> Notification:
        """Create a new notification"""
        return await NotificationDAL.add(
            db=db,
            user_id=user_id,
            message=message,
            notification_type=notification_type,
            metadata=metadata,
            is_active=is_active
        )

    @classmethod
    async def update_notification(
        cls,
        db: AsyncSession,
        notification_id: int,
        **kwargs
    ) -> Optional[Notification]:
        """Update a notification"""
        return await NotificationDAL.update(db, notification_id, **kwargs)

    @classmethod
    async def set_notification_active(
        cls,
        db: AsyncSession,
        notification_id: int,
        is_active: bool
    ) -> Optional[Notification]:
        """Set a notification's active status"""
        return await NotificationDAL.update_active_status(db, notification_id, is_active)

    @classmethod
    async def delete_notification(
        cls,
        db: AsyncSession,
        notification_id: int
    ) -> bool:
        """Delete a notification"""
        return await NotificationDAL.delete(db, notification_id)

    @classmethod
    async def get_user_notifications(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> List[Notification]:
        """Get all notifications for a user"""
        return await NotificationDAL.get_by_user(db, user_id)

    @classmethod
    async def get_active_user_notifications(
        cls,
        db: AsyncSession,
        user_id: int
    ) -> List[Notification]:
        """Get all active notifications for a user"""
        return await NotificationDAL.get_active_by_user(db, user_id)
