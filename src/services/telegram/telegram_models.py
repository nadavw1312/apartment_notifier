from sqlalchemy import String, Boolean, Integer, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from src.db.model import Base, INTPK
from src.db.sql.sql_mixins import TimestampMixin

class TelegramUser(Base, TimestampMixin):
    """Model for Telegram users"""
    __tablename__ = "telegram_users"
    
    # Auto-incrementing ID as primary key
    id: Mapped[INTPK]
    
    # Foreign key to User model
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    # Telegram-specific fields
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    
    def __repr__(self):
        return f"<TelegramUser {self.id} (User {self.user_id} - Telegram {self.telegram_id})>" 