from sqlalchemy import String, Float, ARRAY, TEXT, Column, Identity, Boolean, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from pgvector.sqlalchemy import Vector
from src.db.model import Base, INTPK
from src.db.sql.sql_mixins import TimestampMixin
from typing import Optional
class Apartment(Base, TimestampMixin):
    __tablename__ = "apartments"

    id: Mapped[INTPK]
    post_link: Mapped[str] = mapped_column(TEXT, unique=True)
    user: Mapped[str] = mapped_column(TEXT)
    timestamp: Mapped[str] = mapped_column(TEXT)
    text: Mapped[str] = mapped_column(TEXT)
    text_embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)
    price: Mapped[Optional[str]] = mapped_column(TEXT, nullable=True)
    location: Mapped[str] = mapped_column(TEXT)
    phone_numbers: Mapped[list[str]] = mapped_column(ARRAY(String))
    image_urls: Mapped[list[str]] = mapped_column(ARRAY(String))
    mentions: Mapped[list[str]] = mapped_column(ARRAY(String))
    summary: Mapped[str] = mapped_column(TEXT)
    source: Mapped[str] = mapped_column(TEXT)
    group_id: Mapped[str] = mapped_column(TEXT)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
