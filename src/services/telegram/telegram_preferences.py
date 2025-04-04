"""
Telegram bot preference handlers
Manages apartment preferences collection and updates
"""
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.sql_database import SQL_DB_MANAGER
from src.services.user.user_dal import update_user_preferences_by_telegram_id, get_user_by_telegram_id

class PreferenceStates(StatesGroup):
    confirm_preferences = State()
    waiting_for_min_price = State() 
    waiting_for_max_price = State()
    waiting_for_min_rooms = State()
    waiting_for_max_rooms = State()
    waiting_for_min_area = State()
    waiting_for_max_area = State()

async def handle_confirm_preferences(message: types.Message, state: FSMContext):
    """Handle user's decision to set preferences now or later"""
    if not message.text:
        return
    
    response = message.text.strip().lower()
    
    if response == 'yes':
        await message.answer(
            "Let's set up your apartment preferences.\n\n"
            "What's the minimum price you're looking for? (in NIS)\n"
            "Type 0 for no minimum."
        )
        await state.set_state(PreferenceStates.waiting_for_min_price)
    elif response == 'skip':
        await message.answer(
            "No problem! You can set your preferences later using the /preferences command.\n"
            "You'll receive all apartment notifications until you set specific preferences."
        )
        await state.clear()
    else:
        await message.answer("Please type 'yes' to set preferences now, or 'skip' to do it later.")

async def handle_preferences_command(message: types.Message, state: FSMContext):
    """Handle /preferences command to update preferences"""
    if not message.text:
        return
    
    await message.answer(
        "Let's update your apartment preferences.\n\n"
        "What's the minimum price you're looking for? (in NIS)\n"
        "Type 0 for no minimum."
    )
    await state.set_state(PreferenceStates.waiting_for_min_price)

async def handle_min_price(message: types.Message, state: FSMContext):
    """Handle minimum price input"""
    if not message.text:
        return
    
    try:
        min_price = int(message.text.strip())
        if min_price < 0:
            await message.answer("Price should be a positive number. Please try again:")
            return
        
        await state.update_data(min_price=min_price)
        await message.answer(
            "What's the maximum price you're looking for? (in NIS)\n"
            "Type 0 for no maximum."
        )
        await state.set_state(PreferenceStates.waiting_for_max_price)
    except ValueError:
        await message.answer("Please enter a valid number for the minimum price:")

async def handle_max_price(message: types.Message, state: FSMContext):
    """Handle maximum price input"""
    if not message.text:
        return
    
    try:
        max_price = int(message.text.strip())
        if max_price < 0:
            await message.answer("Price should be a positive number. Please try again:")
            return
        
        await state.update_data(max_price=max_price)
        await message.answer(
            "How many rooms do you need at minimum?\n"
            "Type 0 for no minimum."
        )
        await state.set_state(PreferenceStates.waiting_for_min_rooms)
    except ValueError:
        await message.answer("Please enter a valid number for the maximum price:")

async def handle_min_rooms(message: types.Message, state: FSMContext):
    """Handle minimum rooms input"""
    if not message.text:
        return
    
    try:
        min_rooms = float(message.text.strip())
        if min_rooms < 0:
            await message.answer("Number of rooms should be a positive number. Please try again:")
            return
        
        await state.update_data(min_rooms=min_rooms)
        await message.answer(
            "What's the maximum number of rooms you're looking for?\n"
            "Type 0 for no maximum."
        )
        await state.set_state(PreferenceStates.waiting_for_max_rooms)
    except ValueError:
        await message.answer("Please enter a valid number for minimum rooms:")

async def handle_max_rooms(message: types.Message, state: FSMContext):
    """Handle maximum rooms input"""
    if not message.text:
        return
    
    try:
        max_rooms = float(message.text.strip())
        if max_rooms < 0:
            await message.answer("Number of rooms should be a positive number. Please try again:")
            return
        
        await state.update_data(max_rooms=max_rooms)
        await message.answer(
            "What's the minimum apartment size you're looking for? (in square meters)\n"
            "Type 0 for no minimum."
        )
        await state.set_state(PreferenceStates.waiting_for_min_area)
    except ValueError:
        await message.answer("Please enter a valid number for maximum rooms:")

async def handle_min_area(message: types.Message, state: FSMContext):
    """Handle minimum area input"""
    if not message.text:
        return
    
    try:
        min_area = int(message.text.strip())
        if min_area < 0:
            await message.answer("Area should be a positive number. Please try again:")
            return
        
        await state.update_data(min_area=min_area)
        await message.answer(
            "What's the maximum apartment size you're looking for? (in square meters)\n"
            "Type 0 for no maximum."
        )
        await state.set_state(PreferenceStates.waiting_for_max_area)
    except ValueError:
        await message.answer("Please enter a valid number for minimum area:")

async def handle_max_area(message: types.Message, state: FSMContext):
    """Handle maximum area input and update preferences"""
    if not message.text or not message.from_user:
        return
    
    try:
        max_area = int(message.text.strip())
        if max_area < 0:
            await message.answer("Area should be a positive number. Please try again:")
            return
        
        data = await state.get_data()
        
        # Update user preferences in database
        error = None
        try:
            async with SQL_DB_MANAGER.get_session_with_transaction() as session:
                # Update user preferences
                await update_user_preferences_by_telegram_id(
                    session,
                    telegram_id=str(message.from_user.id),
                    min_price=data.get('min_price', 0),
                    max_price=data.get('max_price', 0),
                    min_rooms=data.get('min_rooms', 0),
                    max_rooms=data.get('max_rooms', 0),
                    min_area=data.get('min_area', 0),
                    max_area=max_area
                )
        except Exception as e:
            error = str(e)
            print(f"Error updating preferences: {e}")
        
        if error:
            await message.answer(
                "Sorry, there was an error saving your preferences.\n"
                "Please try again later using the /preferences command."
            )
        else:
            await message.answer(
                "Perfect! Your apartment preferences have been saved.\n"
                "You'll now receive notifications about apartments that match your criteria."
            )
        
        await state.clear()
    except ValueError:
        await message.answer("Please enter a valid number for maximum area:")

async def handle_preferences_button(callback: types.CallbackQuery, state: FSMContext):
    """Handle preferences button press"""
    if callback.message is None or callback.from_user is None:
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Check if user exists first
    user = None
    try:
        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
            user = await get_user_by_telegram_id(session, str(callback.from_user.id))
    except Exception as e:
        print(f"Error checking user: {e}")
    
    if not user:
        await callback.message.answer(
            "You need to sign up first before setting preferences.\n"
            "Please click the Sign Up button."
        )
        return
    
    # Start preferences flow
    await callback.message.answer("Let's set up your apartment preferences.")
    await callback.message.answer(
        "What's the minimum price you're looking for? (in NIS)\n"
        "Type 0 for no minimum."
    )
    # Set the state to waiting_for_min_price to start the flow
    await state.set_state(PreferenceStates.waiting_for_min_price)
    print(f"✅ State set to waiting_for_min_price for user {callback.from_user.id}")

def register_handlers(dp):
    """Register all preference handlers"""
    # Register command handler
    dp.message.register(handle_preferences_command, Command("preferences"))
    
    # Register all state handlers for the preference flow
    dp.message.register(handle_confirm_preferences, PreferenceStates.confirm_preferences)
    dp.message.register(handle_min_price, PreferenceStates.waiting_for_min_price)
    dp.message.register(handle_max_price, PreferenceStates.waiting_for_max_price)
    dp.message.register(handle_min_rooms, PreferenceStates.waiting_for_min_rooms)
    dp.message.register(handle_max_rooms, PreferenceStates.waiting_for_max_rooms)
    dp.message.register(handle_min_area, PreferenceStates.waiting_for_min_area)
    dp.message.register(handle_max_area, PreferenceStates.waiting_for_max_area)
    
    # Register the preferences button handler
    dp.callback_query.register(
        handle_preferences_button, 
        lambda c: c.data == "preferences"
    )