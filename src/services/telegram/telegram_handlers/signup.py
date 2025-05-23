"""
Telegram bot signup handlers
Manages user registration and authentication
"""
from aiogram import types, Router
from aiogram.filters import Command

from src.services.telegram.telegram_bl import TelegramBL
from src.services.user.user_dal import UserDAL
from src.services.user.user_models import User
from src.db.sql_database import SQL_DB_MANAGER

router = Router()

@router.message(Command("start"))
async def start_command(message: types.Message):
    """Handle /start command"""
    if not message.from_user:
        return

    async with SQL_DB_MANAGER.get_session_with_transaction() as session:
        # Check if user already exists
        telegram_user = await TelegramBL.get_telegram_user(session, int(message.from_user.id))
        if telegram_user:
            await message.reply(
                "You are already registered!\n\n"
                "Available commands:\n"
                "/preferences - Set your apartment preferences\n"
                "/help - Show help message"
            )
            return

        # Create new user
        user = await UserDAL.add(
            session,
            email=f"telegram_{message.from_user.id}@example.com",  # Temporary email
            password="telegram",  # Temporary password
            name=message.from_user.full_name,
            telegram_id=str(message.from_user.id),
            notify_telegram=True
        )

        if not user:
            await message.reply("Something went wrong. Please try again later.")
            return

        # Create Telegram user
        telegram_user = await TelegramBL.create_telegram_user(
            session,
            user_id=int(user.id),  # Convert INTPK to int
            telegram_id=int(message.from_user.id)
        )

        if not telegram_user:
            await message.reply("Something went wrong. Please try again later.")
            return

        await message.reply(
            "Welcome to the Apartment Notifier bot!\n\n"
            "Available commands:\n"
            "/preferences - Set your apartment preferences\n"
            "/help - Show help message"
        )

def register_handlers(dp):
    """Register signup-related handlers"""
    dp.include_router(router) 