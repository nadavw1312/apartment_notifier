"""
Functions for sending apartment details via Telegram
"""
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.apartment.apartment_bl import get_apartment
from typing import Optional
from src.db.sql_database import SQL_DB_MANAGER
from aiogram import types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import re

async def format_apartment_message(apartment) -> str:
    """Format apartment details into a nice message"""
    if not apartment:
        return "Apartment not found."
    
    # Create a well-formatted message with emojis
    message = f"🏠 *Apartment Details* 🏠\n\n"
    
    if apartment.location:
        message += f"📍 *Location:* {apartment.location}\n"
    
    if apartment.price:
        message += f"💰 *Price:* {apartment.price} NIS\n"
    
    if apartment.user:
        message += f"👤 *Posted by:* {apartment.user}\n"
    
    if apartment.timestamp:
        message += f"🕒 *Posted on:* {apartment.timestamp}\n"
    
    # Add phone numbers if available
    if apartment.phone_numbers and len(apartment.phone_numbers) > 0:
        message += f"📱 *Contact:* {', '.join(apartment.phone_numbers)}\n"
    
    # Add summary
    if apartment.summary:
        message += f"\n📝 *Summary:*\n{apartment.summary}\n"
    
    # Add original text (truncated if too long)
    if apartment.text:
        truncated_text = apartment.text[:500] + "..." if len(apartment.text) > 500 else apartment.text
        message += f"\n📄 *Original Post:*\n{truncated_text}\n"
    
    # Add link to original post
    if apartment.post_link:
        message += f"\n🔗 [View Original Post]({apartment.post_link})\n"
    
    return message

async def send_apartment_to_user(bot: Bot, telegram_user_id: str, apartment_id: int) -> bool:
    """
    Fetch apartment by ID and send it to a Telegram user
    
    Args:
        bot: The Telegram bot instance to use for sending messages
        telegram_user_id: Telegram user ID to send the message to
        apartment_id: ID of the apartment to fetch and send
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Get the apartment from the database
        async with SQL_DB_MANAGER.get_session_with_transaction() as session:
            apartment = await get_apartment(session, apartment_id)
            
            if not apartment:
                await bot.send_message(chat_id=telegram_user_id, text="Sorry, I couldn't find that apartment.")
                return False
            
            # Format the apartment details into a message
            message = await format_apartment_message(apartment)
            
            # Send the message to the user
            await bot.send_message(chat_id=telegram_user_id, text=message)
            return True
    
    except Exception as e:
        print(f"Error sending apartment details: {e}")
        await bot.send_message(chat_id=telegram_user_id, text="Sorry, there was an error getting apartment details.")
        return False

async def handle_apartment_command(message: types.Message, state: FSMContext):
    """
    Handle the /apartment command which shows apartment details
    
    Format: /apartment <id> - Show details of a specific apartment
    """
    if not message.text or not message.from_user or not message.bot:
        return
    
    # Extract apartment ID from command
    # Format should be: /apartment 123 or just /apartment (which will show an error)
    parts = message.text.split()
    
    if len(parts) < 2:
        await message.answer("Please provide an apartment ID. Usage: /apartment <id>")
        return
    
    # Try to parse the apartment ID
    try:
        apartment_id = int(parts[1])
    except ValueError:
        await message.answer("Invalid apartment ID. Please provide a valid number.")
        return
    
    # Get user's telegram ID
    telegram_user_id = str(message.from_user.id)
    
    # Send a "loading" message
    loading_message = await message.answer("Loading apartment details...")
    
    # Try to send the apartment details
    success = await send_apartment_to_user(message.bot, telegram_user_id, apartment_id)
    
    # Delete the loading message if we were successful
    if success:
        await loading_message.delete()

def register_handlers(dp):
    """Register apartment-related handlers"""
    dp.message.register(handle_apartment_command, Command("apartment")) 