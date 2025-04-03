from sqlalchemy import String, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from src.db.model import Base, INTPK

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[INTPK]
    channel: Mapped[str] = mapped_column(String(50))  # e.g., "telegram", "email"
    recipient: Mapped[str] = mapped_column(String(255))  # e.g., telegram_id or email
    message: Mapped[str] = mapped_column(String(1000))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50))  # e.g., "sent", "failed" 