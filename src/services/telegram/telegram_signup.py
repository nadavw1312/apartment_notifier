"""
Telegram bot signup handlers
Manages user registration process
"""
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.user.user_dal import add_user
from src.db.sql_database import SQL_DB_MANAGER
from functools import partial

class SignupStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_name = State()

async def handle_start(message: types.Message, state: FSMContext):
    """Handle /start command to begin registration"""
    if not message.text:
        return
    await message.answer(
        "Welcome to Apartment Notifier! Let's get you signed up.\n"
        "Please enter your email address:"
    )
    await state.set_state(SignupStates.waiting_for_email)

async def handle_email(message: types.Message, state: FSMContext):
    """Handle email input"""
    if not message.text:
        return
    email = message.text.strip()
    if not "@" in email or not "." in email:
        await message.answer("Please enter a valid email address:")
        return

    await state.update_data(email=email)
    await message.answer("Great! Now please enter your name:")
    await state.set_state(SignupStates.waiting_for_name)

async def handle_name(message: types.Message, state: FSMContext, preferences_state):
    """Handle name input and complete basic registration"""
    if not message.text or not message.from_user:
        return

    name = message.text.strip()
    data = await state.get_data()

    # Create user with basic information
    error = None
    try:
        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
            # Create the user with minimal information
            await add_user(
                session,
                name=name,
                email=data["email"],
                telegram_id=str(message.from_user.id),
                password="",
                notify_telegram=True,
            )
    except Exception as e:
        error = str(e)

    if error:
        await message.answer(
            "Sorry, there was an error completing your signup.\n"
            "Please try again later."
        )
        await state.clear()
        return

    # Basic registration complete, offer to set preferences
    await message.answer(
        f"Great! You're now registered, {name}.\n\n"
        "Would you like to set your apartment preferences now?\n"
        "This will help us send you relevant notifications.\n\n"
        "Type 'yes' to set preferences now, or 'skip' to do it later."
    )
    await state.set_state(preferences_state.confirm_preferences)

def register_handlers(dp, preferences_states):
    """Register all signup handlers"""
    dp.message.register(handle_start, Command("start"))
    dp.message.register(handle_email, SignupStates.waiting_for_email)
    
    # Create a partial function with the preferences_state parameter
    name_handler = partial(handle_name, preferences_state=preferences_states)
    dp.message.register(name_handler, SignupStates.waiting_for_name)
