"""
Telegram bot implementation using aiogram 3.x.
Handles bot initialization, message sending, and graceful shutdown.
"""

from typing import Optional
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import AsyncSession

# Import the separate modules
from src.services.telegram.telegram_signup import register_handlers as register_signup_handlers
from src.services.telegram.telegram_preferences import register_handlers as register_preference_handlers, PreferenceStates
from src.services.telegram.telegram_apartment_message import register_handlers as register_apartment_handlers

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self._bot: Optional[Bot] = None
        self._dp: Optional[Dispatcher] = None
        self._session: Optional[AsyncSession] = None

    async def start(self):
        """Initialize and start the bot"""
        if not self._bot:
            self._bot = Bot(token=self.token)
        
        # Add in-memory FSM storage here
        self._dp = Dispatcher(storage=MemoryStorage(), bot=self._bot)
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup command and message handlers from separate modules"""
        if not self._dp:
            return

        # Register handlers from separate modules - each module handles its own functionality
        register_preference_handlers(self._dp)
        register_signup_handlers(self._dp)
        register_apartment_handlers(self._dp)

    async def send_message(self, chat_id: str, message: str) -> bool:
        """
        Send a message to a specific chat.
        Returns True if successful, False otherwise.
        """
        if not self._bot:
            await self.start()
        
        if not self._bot:  # Double check after start()
            return False
            
        try:
            await self._bot.send_message(chat_id=chat_id, text=message)
            return True
        except TelegramAPIError as e:
            print(f"Failed to send message: {e}")
            return False

    async def stop(self):
        """Stop the bot and close the session"""
        if self._dp:
            await self._dp.storage.close()
        if self._bot:
            await self._bot.session.close()
        self._bot = None
        self._dp = None

    def set_session(self, session: AsyncSession):
        """Set the database session for user operations"""
        self._session = session 

    async def set_webhook(self, domain: str):
        """Set the webhook for the bot"""
        if not self._bot:
            await self.start()
        if not self._bot:
            return
        webhook_url = f"https://4ef4-85-250-220-244.ngrok-free.app/webhook"
        await self._bot.set_webhook(webhook_url)

    async def process_update(self, update_data: dict):
        """Process an incoming update"""
        if not self._dp:
            return
        if not self._bot:
            await self.start()
        if not self._bot:
            return
        update = types.Update(**update_data)
        print("📦 Incoming Update:", update.model_dump())
        await self._dp.feed_update(self._bot, update) 