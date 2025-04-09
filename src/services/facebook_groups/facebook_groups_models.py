from sqlalchemy import String, Text, Column, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from src.db.model import Base

class FacebookGroup(Base):
    """Model for Facebook groups that can be scraped"""
    __tablename__ = "facebook_groups"
    
    # Group ID as primary key (Facebook's unique identifier for the group)
    group_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    is_private: Mapped[bool] = mapped_column(Boolean,default=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self):
        return f"<FacebookGroup {self.group_id} ('{self.name}')>" 