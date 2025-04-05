"""
Factory module for telegram message providers
Provides a way to get the appropriate message provider based on language
"""
from enum import Enum
from src.services.telegram.telegram_messaging.base import TelegramMessages
from src.services.telegram.telegram_messaging.english import EnglishMessages
from src.services.telegram.telegram_messaging.hebrew import HebrewMessages

class Language(Enum):
    """Supported languages enum"""
    ENGLISH = "en"
    HEBREW = "he"

def get_messages(language: Language = Language.ENGLISH) -> TelegramMessages:
    """
    Get the appropriate message provider for the specified language
    
    Args:
        language: Language enum value (default: ENGLISH)
        
    Returns:
        TelegramMessages implementation for the requested language
    """
    if language == Language.HEBREW:
        return HebrewMessages()
    # Default to English
    return EnglishMessages() 