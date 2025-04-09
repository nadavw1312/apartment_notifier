from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy import and_

from src.services.notification.notification_models import Notification

class NotificationDAL:
    """Data Access Layer for managing notifications"""
    