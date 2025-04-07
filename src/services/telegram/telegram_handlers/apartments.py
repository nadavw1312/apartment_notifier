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

@router.message(Command("apartments"))
async def list_apartments(message: types.Message):
    """Handle /apartments command"""
    if not message.from_user:
        return

    async with SQL_DB_MANAGER.get_session_with_transaction() as session:
        try:
            # Check if user exists
            telegram_user = await TelegramBL.get_telegram_user(session, int(message.from_user.id))
            if not telegram_user:
                await message.reply("Please register first using /start")
                return

            # Get user's apartments
            user = await UserBL.get_user(session, telegram_user.user_id)
            if not user:
                await message.reply("Something went wrong. Please try again later.")
                return

            # Get apartments for this user only
            apartments = await ApartmentBL.get_user_apartments(session, user.id)
            if not apartments:
                await message.reply("You haven't saved any apartments yet.")
                return

            # Format apartments list
            message_parts = ["Your saved apartments:\n"]
            for apartment in apartments:
                message_parts.append(f"🏠 {apartment.location}")
                if apartment.price:
                    message_parts.append(f"💰 Price: {apartment.price} ILS")
                if apartment.summary:
                    message_parts.append(f"📝 Summary: {apartment.summary}")
                if apartment.post_link:
                    message_parts.append(f"🔗 [View listing]({apartment.post_link})")
                message_parts.append("")

            await message.reply("\n".join(message_parts), parse_mode="Markdown")
        except Exception as e:
            print(f"Error in apartments handler: {e}")
            await message.reply("Something went wrong. Please try again later.")

def register_handlers(dp):
    """Register apartment-related handlers"""
    dp.message.register(list_apartments, Command("apartments")) 