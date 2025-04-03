import logging
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from src.config import DATABASE_URL

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class MongoDatabase:
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None

    async def init(self):
        """Initialize MongoDB and register Beanie document models."""
        if not isinstance(DATABASE_URL, str):
            raise ValueError("DATABASE_URL must be a string")
        logger.info(f"Initializing MongoDB at: {DATABASE_URL}")
        self.client = AsyncIOMotorClient(DATABASE_URL)
        db_name = DATABASE_URL.rsplit("/", 1)[-1] or "default_db"
        self.db = self.client[db_name]
        await init_beanie(
            database=self.db,
            document_models=[]  # <-- Add your Beanie models here
        )
        logger.info("✅ MongoDB (Beanie) initialized successfully")

    async def close(self):
        """Close the MongoDB client."""
        if self.client is not None:
            self.client.close()
            logger.info("❌ MongoDB client connection closed")
        else:
            raise Exception("MongoDB client is not initialized")

    async def get_session(self) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
        """Yield MongoDB database object (no transaction)."""
        if self.db is None:
            raise Exception("MongoDB not initialized")
        yield self.db

    async def get_session_with_transaction(self) -> AsyncGenerator:
        """Yield MongoDB session wrapped in a transaction."""
        if not self.client:
            raise Exception("MongoDB client not initialized")
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    yield session
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(f"❌ MongoDB Transaction failed: {e}")
                    raise e

MONGO_DB_MANAGER = MongoDatabase()
