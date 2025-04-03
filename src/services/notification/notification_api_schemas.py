from pydantic import BaseModel
from datetime import datetime

class NotificationCreateRequest(BaseModel):
    channel: str
    recipient: str
    message: str

class NotificationResponse(BaseModel):
    id: int
    channel: str
    recipient: str
    message: str
    created_at: datetime
    status: str 