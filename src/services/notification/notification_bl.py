# TODO: implement notification_bl.py

from sqlalchemy.ext.asyncio import AsyncSession
from src.services.notification.notification_dal import send_notification

# Dummy users for testing
TEST_USERS = [
    {"channel": "telegram", "recipient": "123456789", "name": "Test User 1"},
    {"channel": "email", "recipient": "test1@example.com", "name": "Test User 2"},
]

async def notify_users(session: AsyncSession, message: str):
    notifications = []
    for user in TEST_USERS:
        notification = await send_notification(
            session,
            channel=user["channel"],
            recipient=user["recipient"],
            message=f"Hello {user['name']}! {message}"
        )
        notifications.append(notification)
    return notifications
