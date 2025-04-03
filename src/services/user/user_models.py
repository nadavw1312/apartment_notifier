from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.db.model import Base, INTPK
from src.db.sql.sql_mixins import TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[INTPK]
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))
    telegram_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # New boolean fields for notification preferences
    notify_telegram: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_email: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # user preferences
    min_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_area: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_area: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
