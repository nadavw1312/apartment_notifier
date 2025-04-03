import asyncio
from services.mail_provider.mail_provider_factory import MailProviderFactory, MailProviderType

async def main():
    # Create provider instance
    provider = MailProviderFactory.create_provider(
        MailProviderType.GMAIL,
        credentials_path='path/to/your/credentials.json'
    )
    
    # Authenticate
    await provider.authenticate()
    
    # Start monitoring emails
    search_query = "from:marketplace@example.com subject:new listing"
    await provider.watch_inbox(search_query)

if __name__ == "__main__":
    asyncio.run(main()) 