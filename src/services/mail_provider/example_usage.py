import asyncio
from src.services.mail_provider.managers.mail_provider_factory import MailProviderFactory, MailProviderType

async def main():
    # Create provider instance
    provider = MailProviderFactory.create_provider(
        MailProviderType.GMAIL,
        credentials_path='credentials.json'
    )
    
    # Authenticate
    await provider.authenticate()
    
    # Start monitoring emails
    search_query = ""
    await provider.watch_inbox(search_query)

if __name__ == "__main__":
    asyncio.run(main()) 