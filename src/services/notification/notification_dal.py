from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.notification.notification_models import Notification

async def send_notification(
    session: AsyncSession,
    channel: str,
    recipient: str,
    message: str,
    status: str = "sent"
) -> Notification:
    notification = Notification(
        channel=channel,
        recipient=recipient,
        message=message,
        created_at=datetime.utcnow(),
        status=status
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification 