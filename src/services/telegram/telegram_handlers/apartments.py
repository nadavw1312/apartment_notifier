"""
Telegram bot apartment handlers
Manages apartment-related commands and callbacks
"""
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.services.apartment.apartment_bl import get_apartment
from src.db.sql_database import SQL_DB_MANAGER 
from src.services.telegram.telegram_messaging import TelegramMessages

async def format_apartment_message(apartment, messages: TelegramMessages) -> str:
    """
    Format apartment details into a nice message
    
    Args:
        apartment: Apartment data object
        messages: TelegramMessages instance for localization
    """
    if not apartment:
        return messages.apartment_not_found()
    
    # Create a well-formatted message with emojis
    message = f"{messages.apartment_details_title()}\n\n"
    
    if apartment.location:
        message += f"{messages.apartment_location()} {apartment.location}\n"
    
    if apartment.price:
        message += f"{messages.apartment_price()} {apartment.price} NIS\n"
    
    if apartment.user:
        message += f"{messages.apartment_posted_by()} {apartment.user}\n"
    
    if apartment.timestamp:
        message += f"{messages.apartment_posted_on()} {apartment.timestamp}\n"
    
    # Add phone numbers if available
    if apartment.phone_numbers and len(apartment.phone_numbers) > 0:
        message += f"{messages.apartment_contact()} {', '.join(apartment.phone_numbers)}\n"
    
    # Add summary
    if apartment.summary:
        message += f"\n{messages.apartment_summary()}\n{apartment.summary}\n"
    
    # Add original text (truncated if too long)
    if apartment.text:
        truncated_text = apartment.text[:500] + "..." if len(apartment.text) > 500 else apartment.text
        message += f"\n{messages.apartment_original_post()}\n{truncated_text}\n"
    
    # Add link to original post
    if apartment.post_link:
        message += f"\n{messages.apartment_view_original()}({apartment.post_link})\n"
    
    return message

async def handle_apartment_command(message: types.Message, state: FSMContext, messages: TelegramMessages):
    """
    Handle the /apartment command which shows apartment details
    
    Format: /apartment <id> - Show details of a specific apartment
    """
    if not message.text or not message.from_user:
        return
    
    # Extract apartment ID from command
    # Format should be: /apartment 123 or just /apartment (which will show an error)
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer(messages.apartment_id_required())
        return
    
    # Try to parse the apartment ID
    try:
        apartment_id = int(parts[1])
    except ValueError:
        await message.answer(messages.apartment_invalid_id())
        return
    
    # Send a "loading" message
    loading_message = await message.answer(messages.loading_message())
    
    try:
        # Get the apartment from the database
        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
            apartment = await get_apartment(session, apartment_id)
            
            if not apartment:
                await message.answer(messages.apartment_not_found())
                return
            
            # Format the apartment details into a message
            formatted_message = await format_apartment_message(apartment, messages)
            
            # Send the formatted message
            await message.answer(formatted_message)
            
    except Exception as e:
        print(f"Error sending apartment details: {e}")
        await message.answer(messages.apartment_fetch_error())
    finally:
        # Delete the loading message
        await loading_message.delete()

def register_handlers(dp):
    """Register apartment-related handlers"""
    dp.message.register(handle_apartment_command, Command("apartment")) 