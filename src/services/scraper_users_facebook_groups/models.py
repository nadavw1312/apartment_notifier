from sqlalchemy import String, ForeignKey, Text, Column, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.model import Base, INTPK
from src.db.sql.sql_mixins import TimestampMixin

class ScraperUserFacebookGroup(Base, TimestampMixin):
    """
    Association model for mapping between ScraperUser and FacebookGroup
    Represents which users are scraping which Facebook groups
    """
    __tablename__ = "scraper_users_facebook_groups"
    
    # Auto-incrementing ID as primary key
    id: Mapped[INTPK]
    
    # Foreign keys
    scraper_user_id: Mapped[int] = mapped_column(ForeignKey("scraper_users.id", ondelete="CASCADE"))
    facebook_group_id: Mapped[str] = mapped_column(ForeignKey("facebook_groups.group_id", ondelete="CASCADE"))
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Enforce unique constraint on user_id and group_id combination
    __table_args__ = (
        UniqueConstraint('scraper_user_id', 'facebook_group_id', name='uix_user_group'),
    )
    
    def __repr__(self):
        return f"<ScraperUserFacebookGroup {self.id} (User {self.scraper_user_id} - Group {self.facebook_group_id})>" 