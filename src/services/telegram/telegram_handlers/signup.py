"""
Telegram bot signup handlers
Manages user registration process ONLY
"""
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.telegram.telegram_bl import TelegramBL
from src.services.user.user_bl import UserBL
from src.db.sql_database import SQL_DB_MANAGER

router = Router()

class SignupStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_name = State()

@router.message(Command("start"))
async def start_signup(message: types.Message, state: FSMContext):
    """Start the signup process"""
    if not message.from_user:
        return

    async with SQL_DB_MANAGER.get_session_with_transaction() as session:
        # Check if user already exists by checking for a Telegram user
        telegram_user = await TelegramBL.get_telegram_user(session, int(message.from_user.id))
        if telegram_user:
            await message.reply("You are already registered!")
            return

        await message.reply("Welcome! Please enter your email address:")
        await state.set_state(SignupStates.waiting_for_email)

@router.message(SignupStates.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    """Process the email input"""
    if not message.text:
        await message.reply("Please enter a valid email address.")
        return

    await state.update_data(email=message.text)
    await state.set_state(SignupStates.waiting_for_name)
    await message.reply("Great! Now please enter your name:")

@router.message(SignupStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Process the name input and complete signup"""
    if not message.from_user or not message.text:
        return

    data = await state.get_data()
    email = data.get('email')
    if not email:
        await message.reply("Something went wrong. Please start over with /start")
        await state.clear()
        return

    name = message.text

    async with SQL_DB_MANAGER.get_session_with_transaction() as session:
        # Create user
        user = await UserBL.create_user(
            session,
            email=email,
            name=name,
            password='',  # Empty password for Telegram users
            metadata={
                'telegram_id': str(message.from_user.id),
                'telegram_username': message.from_user.username or '',
                'telegram_first_name': message.from_user.first_name or '',
                'telegram_last_name': message.from_user.last_name or ''
            }
        )

        # Create Telegram user
        telegram_user = await TelegramBL.create_telegram_user(
            session,
            user_id=user.id,
            telegram_id=int(message.from_user.id),
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

        await message.reply(
            f"Thanks {name}! You're all set up. Use /help to see available commands."
        )
        await state.clear()

async def handle_signup_button(callback: types.CallbackQuery, state: FSMContext):
    """Handle the signup button callback"""
    if not callback.from_user:
        return

    await start_signup(callback.message, state)
    await callback.answer()

def register_handlers(dp):
    """Register signup-related handlers"""
    dp.include_router(router)
    
    # Register signup button handler
    dp.callback_query.register(
        handle_signup_button,
        lambda c: c.data == "signup"
    ) 