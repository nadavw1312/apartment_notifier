from aiogram import types, Router
from aiogram.filters import Command

from src.services.telegram.telegram_bl import TelegramBL
from src.services.user.user_bl import UserBL
from src.db.sql_database import SQL_DB_MANAGER

router = Router()

@router.message(Command("help"))
async def help_command(message: types.Message):
    """Handle /help command"""
    if not message.from_user:
        return

    async with SQL_DB_MANAGER.get_session_with_transaction() as session:
        # Check if user exists
        telegram_user = await TelegramBL.get_telegram_user(session, int(message.from_user.id))
        if not telegram_user:
            await message.reply(
                "Welcome to the Apartment Notifier bot!\n\n"
                "Available commands:\n"
                "/start - Register to receive apartment notifications\n"
                "/help - Show this help message"
            )
            return

        # Get user preferences
        user = await UserBL.get_user(session, telegram_user.user_id)
        if not user:
            await message.reply("Something went wrong. Please try again later.")
            return

        # Format current preferences
        preferences = []
        if user.min_price is not None:
            preferences.append(f"Minimum price: {user.min_price:,} ILS")
        if user.max_price is not None:
            preferences.append(f"Maximum price: {user.max_price:,} ILS")
        if user.min_area is not None:
            preferences.append(f"Minimum area: {user.min_area} m²")
        if user.max_area is not None:
            preferences.append(f"Maximum area: {user.max_area} m²")
        if user.min_rooms is not None:
            preferences.append(f"Minimum rooms: {user.min_rooms}")
        if user.max_rooms is not None:
            preferences.append(f"Maximum rooms: {user.max_rooms}")

        preferences_text = (
            "\n\nCurrent preferences:\n" + "\n".join(preferences)
            if preferences else
            "\n\nNo preferences set yet. Use /preferences to set your preferences."
        )

        await message.reply(
            "Welcome to the Apartment Notifier bot!\n\n"
            "Available commands:\n"
            "/preferences - Update your apartment preferences\n"
            "/help - Show this help message"
            f"{preferences_text}"
        )

def register_handlers(dp):
    """Register help-related handlers"""
    dp.include_router(router) 