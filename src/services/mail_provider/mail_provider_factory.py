from enum import Enum
from .mail_provider import MailProvider
from .gmail_provider import GmailProvider

class MailProviderType(Enum):
    GMAIL = "gmail"
    # Add other providers here as needed
    # OUTLOOK = "outlook"
    # YAHOO = "yahoo"

class MailProviderFactory:
    @staticmethod
    def create_provider(provider_type: MailProviderType, **kwargs) -> MailProvider:
        if provider_type == MailProviderType.GMAIL:
            return GmailProvider(**kwargs)
        # Add other providers as needed
        raise ValueError(f"Unsupported mail provider: {provider_type}") 