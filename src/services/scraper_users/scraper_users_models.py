from sqlalchemy import String, Boolean, Text, Column, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.db.model import Base, INTPK
from src.db.sql.sql_mixins import TimestampMixin

class ScraperUser(Base, TimestampMixin):
    """Generic scraper user model for storing sessions in the database"""
    __tablename__ = "scraper_users"
    
    # Auto-incrementing ID as primary key
    id: Mapped[INTPK]
    # Email and source fields
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    # Other fields
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    session_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # Stored as JSON string
    last_login: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    
    
    # Make email + source unique
    __table_args__ = (
        UniqueConstraint('email', 'source', name='uix_email_source'),
    ) 