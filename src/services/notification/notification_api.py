# TODO: implement notification_api.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.sql_database import SQL_DB_MANAGER
from src.services.notification.notification_api_schemas import NotificationResponse
from src.services.notification.notification_bl import notify_users

router = APIRouter()

@router.post("/test", response_model=list[NotificationResponse])
async def test_notifications(
    message: str = "This is a test notification!",
    session: AsyncSession = Depends(SQL_DB_MANAGER.get_session_with_transaction),
):
    notifications = await notify_users(session, message)
    return [NotificationResponse.model_validate(notif) for notif in notifications]
