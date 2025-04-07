"""
Telegram bot help handlers
Provides help and information about available commands
"""
from aiogram import types, Router
from aiogram.filters import Command

from src.services.telegram.telegram_bl import TelegramBL
from src.services.user.user_bl import UserBL
from src.db.sql_database import SQL_DB_MANAGER
from src.services.user.user_dal import UserDAL

router = Router()

@router.message(Command("help"))
async def help_command(message: types.Message):
    """Handle /help command"""
    if not message.from_user:
        return

    try:
        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
            # Check if user exists
            telegram_user = await TelegramBL.get_telegram_user(session, int(message.from_user.id))
            if not telegram_user:
                try:
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
                        print(f"Error: Failed to create user for telegram_id {message.from_user.id}")
                        await message.reply("Something went wrong. Please try again later.")
                        return

                    # Create Telegram user
                    telegram_user = await TelegramBL.create_telegram_user(
                        session,
                        user_id=int(user.id),  # Convert INTPK to int
                        telegram_id=int(message.from_user.id)
                    )

                    if not telegram_user:
                        print(f"Error: Failed to create telegram user for user_id {user.id}")
                        await message.reply("Something went wrong. Please try again later.")
                        return

                    await message.reply(
                        "Welcome to the Apartment Notifier bot!\n\n"
                        "Available commands:\n"
                        "/preferences - Set your apartment preferences\n"
                        "/help - Show this help message"
                    )
                    return
                except Exception as e:
                    print(f"Error creating new user: {e}")
                    await message.reply("Something went wrong during user creation. Please try again later.")
                    return

            try:
                # Get user preferences
                user = await UserBL.get_user(session, telegram_user.user_id)
                if not user:
                    print(f"Error: User not found for telegram_user_id {telegram_user.user_id}")
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

                # Format help message
                help_message = (
                    "Available commands:\n"
                    "/start - Register to receive apartment notifications\n"
                    "/preferences - Set your apartment preferences\n"
                    "/help - Show this help message\n\n"
                    "Current preferences:\n"
                )
                if preferences:
                    help_message += "\n".join(preferences)
                else:
                    help_message += "No preferences set yet. Use /preferences to set them."

                await message.reply(help_message)
            except Exception as e:
                print(f"Error getting user preferences: {e}")
                await message.reply("Something went wrong while getting your preferences. Please try again later.")
                return

    except Exception as e:
        print(f"Error in help command: {e}")
        await message.reply("Something went wrong. Please try again later.")
        return

def register_handlers(dp):
    """Register help-related handlers"""
    dp.include_router(router) 