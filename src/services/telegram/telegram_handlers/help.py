"""
Telegram bot help handlers
Provides help and information about available commands
"""
from aiogram import types, Router
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def help_command(message: types.Message):
    """Handle /help command"""
    if not message.from_user:
        return

    try:
        # Format help message
        help_message = (
                    "Available commands:\n"
                    "/start - Register to receive apartment notifications\n"
                    "/preferences - Set your apartment preferences\n"
                    "/help - Show this help message\n\n"
                    "Current preferences:\n"
                )

        await message.reply(help_message)

    except Exception as e:
        print(f"Error in help command: {e}")
        await message.reply("Something went wrong. Please try again later.")
        return

def register_handlers(dp):
    """Register help-related handlers"""
    dp.include_router(router) 