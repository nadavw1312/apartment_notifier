"""
Telegram context module
Provides middleware and context management for the Telegram bot
"""
from typing import Dict, Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from src.services.telegram.telegram_messaging import TelegramMessages, get_messages, Language

class MessageMiddleware(BaseMiddleware):
    """
    Middleware that injects the message provider into handlers
    
    This middleware is responsible for providing the appropriate message
    provider to handlers based on the user's preferred language. It adds
    a 'messages' key to the handler data dictionary.
    """
    
    def __init__(self, default_language: Language = Language.ENGLISH):
        """
        Initialize the middleware with a default language
        
        Args:
            default_language: The default language to use if no user preference is found
        """
        self.default_language = default_language
        self.default_messages = get_messages(default_language)
        # In a real implementation, you might want to cache message providers
        self.message_providers: Dict[Language, TelegramMessages] = {
            default_language: self.default_messages
        }
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """
        Process event and inject message provider
        
        This method is called by the dispatcher for each event before
        it's passed to the handler. It adds the message provider to the
        handler data dictionary.
        
        Args:
            handler: The handler function
            event: The event to process (message or callback query)
            data: The handler data dictionary
            
        Returns:
            The result of the handler function
        """
        # Here you would get the user's language preference from the database
        # For now, we'll just use the default language
        # In a real implementation, you would look up the user's preferred language
        # based on their user ID
        
        # Add message provider to handler data
        data["messages"] = self.default_messages
        
        # Call the original handler with the updated data
        return await handler(event, data) 