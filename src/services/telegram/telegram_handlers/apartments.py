"""
Telegram bot apartment handlers
Manages apartment-related commands and notifications
"""
from aiogram import types, Router
from aiogram.filters import Command

from src.services.telegram.telegram_bl import TelegramBL
from src.services.user.user_bl import UserBL
from src.services.apartment.apartment_bl import ApartmentBL
from src.db.sql_database import SQL_DB_MANAGER

router = Router()

def register_handlers(dp):
    """Register apartment-related handlers"""
