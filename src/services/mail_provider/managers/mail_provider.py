from abc import ABC, abstractmethod
from typing import Optional, List, Dict

class MailProvider(ABC):
    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> None:
        pass
    
    @abstractmethod
    async def watch_inbox(self, query: str = "") -> None:
        """Monitor inbox for new emails matching the query"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> None:
        """Authenticate with the email provider"""
        pass
    
    @abstractmethod
    async def process_message(self, message_id: str) -> Dict:
        """Process a single email message and return its contents"""
        pass
