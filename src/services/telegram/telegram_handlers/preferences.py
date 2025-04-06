"""
Telegram bot preference handlers
Manages apartment preferences collection and updates
"""
from aiogram import types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.sql_database import SQL_DB_MANAGER
from src.services.user.user_dal import update_user_preferences_by_telegram_id, get_user_by_telegram_id
from src.services.telegram.telegram_messaging import TelegramMessages
from src.services.telegram.telegram_bl import TelegramBL
from src.services.user.user_bl import UserBL

router = Router()

class PreferencesStates(StatesGroup):
    waiting_for_min_price = State()
    waiting_for_max_price = State()
    waiting_for_min_area = State()
    waiting_for_max_area = State()
    waiting_for_min_rooms = State()
    waiting_for_max_rooms = State()

@router.message(Command("preferences"))
async def start_preferences(message: types.Message, state: FSMContext):
    """Start the preferences update process"""
    if not message.from_user:
        return

    async with SQL_DB_MANAGER.get_session_with_transaction() as session:
        # Check if user exists
        telegram_user = await TelegramBL.get_telegram_user(session, int(message.from_user.id))
        if not telegram_user:
            await message.reply("You need to register first! Use /start to register.")
            return

        # Get user preferences
        user = await UserBL.get_user(session, telegram_user.user_id)
        if not user:
            await message.reply("Something went wrong. Please try again later.")
            return

        # Store current preferences in state
        await state.update_data(
            min_price=user.min_price,
            max_price=user.max_price,
            min_area=user.min_area,
            max_area=user.max_area,
            min_rooms=user.min_rooms,
            max_rooms=user.max_rooms
        )

        await message.reply("Please enter minimum price (in ILS) or 'skip' to keep current value:")
        await state.set_state(PreferencesStates.waiting_for_min_price)

@router.message(PreferencesStates.waiting_for_min_price)
async def process_min_price(message: types.Message, state: FSMContext):
    """Process minimum price input"""
    if not message.text:
        await message.reply("Please enter a valid number or 'skip'.")
        return

    if message.text.lower() != 'skip':
        try:
            min_price = int(message.text)
            await state.update_data(min_price=min_price)
        except ValueError:
            await message.reply("Please enter a valid number or 'skip'.")
            return

    await message.reply("Please enter maximum price (in ILS) or 'skip' to keep current value:")
    await state.set_state(PreferencesStates.waiting_for_max_price)

@router.message(PreferencesStates.waiting_for_max_price)
async def process_max_price(message: types.Message, state: FSMContext):
    """Process maximum price input"""
    if not message.text:
        await message.reply("Please enter a valid number or 'skip'.")
        return

    if message.text.lower() != 'skip':
        try:
            max_price = int(message.text)
            await state.update_data(max_price=max_price)
        except ValueError:
            await message.reply("Please enter a valid number or 'skip'.")
            return

    await message.reply("Please enter minimum area (in square meters) or 'skip' to keep current value:")
    await state.set_state(PreferencesStates.waiting_for_min_area)

@router.message(PreferencesStates.waiting_for_min_area)
async def process_min_area(message: types.Message, state: FSMContext):
    """Process minimum area input"""
    if not message.text:
        await message.reply("Please enter a valid number or 'skip'.")
        return

    if message.text.lower() != 'skip':
        try:
            min_area = int(message.text)
            await state.update_data(min_area=min_area)
        except ValueError:
            await message.reply("Please enter a valid number or 'skip'.")
            return

    await message.reply("Please enter maximum area (in square meters) or 'skip' to keep current value:")
    await state.set_state(PreferencesStates.waiting_for_max_area)

@router.message(PreferencesStates.waiting_for_max_area)
async def process_max_area(message: types.Message, state: FSMContext):
    """Process maximum area input"""
    if not message.text:
        await message.reply("Please enter a valid number or 'skip'.")
        return

    if message.text.lower() != 'skip':
        try:
            max_area = int(message.text)
            await state.update_data(max_area=max_area)
        except ValueError:
            await message.reply("Please enter a valid number or 'skip'.")
            return

    await message.reply("Please enter minimum number of rooms or 'skip' to keep current value:")
    await state.set_state(PreferencesStates.waiting_for_min_rooms)

@router.message(PreferencesStates.waiting_for_min_rooms)
async def process_min_rooms(message: types.Message, state: FSMContext):
    """Process minimum rooms input"""
    if not message.text:
        await message.reply("Please enter a valid number or 'skip'.")
        return

    if message.text.lower() != 'skip':
        try:
            min_rooms = int(message.text)
            await state.update_data(min_rooms=min_rooms)
        except ValueError:
            await message.reply("Please enter a valid number or 'skip'.")
            return

    await message.reply("Please enter maximum number of rooms or 'skip' to keep current value:")
    await state.set_state(PreferencesStates.waiting_for_max_rooms)

@router.message(PreferencesStates.waiting_for_max_rooms)
async def process_max_rooms(message: types.Message, state: FSMContext):
    """Process maximum rooms input and complete preferences update"""
    if not message.from_user or not message.text:
        return

    if message.text.lower() != 'skip':
        try:
            max_rooms = int(message.text)
            await state.update_data(max_rooms=max_rooms)
        except ValueError:
            await message.reply("Please enter a valid number or 'skip'.")
            return

    data = await state.get_data()
    async with SQL_DB_MANAGER.get_session_with_transaction() as session:
        # Get user
        telegram_user = await TelegramBL.get_telegram_user(session, int(message.from_user.id))
        if not telegram_user:
            await message.reply("Something went wrong. Please try again later.")
            await state.clear()
            return

        # Update user preferences
        user = await UserBL.update_user(
            session,
            telegram_user.user_id,
            min_price=data.get('min_price'),
            max_price=data.get('max_price'),
            min_area=data.get('min_area'),
            max_area=data.get('max_area'),
            min_rooms=data.get('min_rooms'),
            max_rooms=data.get('max_rooms')
        )

        if not user:
            await message.reply("Something went wrong. Please try again later.")
            await state.clear()
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

        await message.reply(
            "Your preferences have been updated!\n\n"
            "Current preferences:\n" + "\n".join(preferences)
        )
        await state.clear()

def register_handlers(dp):
    """Register preferences-related handlers"""
    dp.include_router(router) 