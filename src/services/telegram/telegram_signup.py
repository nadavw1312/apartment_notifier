"""
Telegram bot signup handlers
Manages user registration process ONLY
"""
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.services.user.user_dal import add_user, get_user_by_telegram_id
from src.db.sql_database import SQL_DB_MANAGER

class SignupStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_name = State()

async def handle_start(message: types.Message, state: FSMContext):
    """Handle /start command to begin registration"""
    if not message.text or not message.from_user:
        return
    
    # Check if user already exists
    user = None
    try:
        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
            user = await get_user_by_telegram_id(session, str(message.from_user.id))
    except Exception as e:
        print(f"Error checking user: {e}")
    
    # Create keyboard with buttons
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    
    # Add signup button only if user doesn't exist
    if not user:
        signup_button = types.InlineKeyboardButton(text="Sign Up", callback_data="signup")
        keyboard.inline_keyboard.append([signup_button])
    
    # Add preferences button for all users
    preferences_button = types.InlineKeyboardButton(text="Set Preferences", callback_data="preferences")
    keyboard.inline_keyboard.append([preferences_button])
    
    welcome_text = "Welcome to Apartment Notifier!"
    if user:
        welcome_text += f" Welcome back, {user.name}!"
    
    await message.answer(welcome_text, reply_markup=keyboard)

async def handle_signup_button(callback: types.CallbackQuery, state: FSMContext):
    """Handle signup button press"""
    if callback.message is None:
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await callback.message.answer("Let's get you signed up.\nPlease enter your email address:")
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

async def handle_name(message: types.Message, state: FSMContext):
    """Handle name input and complete registration"""
    if not message.text or not message.from_user:
        return

    name = message.text.strip()
    data = await state.get_data()

    # Create user with basic information
    error = None
    try:
        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
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
        await message.answer("Sorry, there was an error completing your signup.\nPlease try again later.")
        await state.clear()
        return

    # Registration complete
    await message.answer(f"Great! You're now registered, {name}. Use the /preferences command to set up your preferences.")
    await state.clear()

def register_handlers(dp):
    """Register signup-related handlers only"""
    dp.message.register(handle_start, Command("start"))
    dp.message.register(handle_email, SignupStates.waiting_for_email)
    dp.message.register(handle_name, SignupStates.waiting_for_name)
    
    # Register signup button handler
    dp.callback_query.register(
        handle_signup_button,
        lambda c: c.data == "signup"
    )
