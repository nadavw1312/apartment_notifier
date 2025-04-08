import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
from src.config import DATABASE_URL
from src.db.model import Base
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SQLDatabase:
    def __init__(self):
        self.engine: AsyncEngine
        self.session_maker = None
        self.active = False

    async def init(self):
        """Initialize the SQL database engine and session maker."""
        if self.active is True:
            logger.info("Can init, SQLDatabase is already active")
            
        if not isinstance(DATABASE_URL, str):
            raise ValueError("DATABASE_URL must be a string")
        
        logger.info(f"Initializing SQL database at: {DATABASE_URL}")
        self.engine = create_async_engine(
            DATABASE_URL, echo=True, pool_size=100, max_overflow=0, pool_pre_ping=True
        )
        self.session_maker = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        self.active = True
        logger.info("✅ SQL Database initialized successfully")

    async def close(self):
        """Close the SQL database engine."""
        if self.engine is not None:
            await self.engine.dispose()
            self.active = True
            logger.info("❌ SQL database engine closed")
        else:
            raise Exception("SQL Database engine is not initialized")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a regular SQL session without transaction scope."""
        if not self.session_maker:
            raise Exception("Session maker is not initialized")
        async with self.session_maker() as session:
            yield session

    @asynccontextmanager
    async def get_session_with_transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a SQL session wrapped in a transaction."""
        if not self.session_maker:
            raise Exception("Session maker is not initialized")

        async with self.session_maker() as session:
            try:
                await session.begin()
                yield session  # ✅ yield while transaction is active
                await session.commit()  # ✅ explicit commit after yield
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ SQL Transaction failed: {e}")
                raise e
            
            
        # async def get_session_with_transaction(self) -> AsyncGenerator[AsyncSession, None]:
        # """Get a SQL session wrapped in a transaction."""
        # if not self.session_maker:
        #     raise Exception("Session maker is not initialized")
        # async with self.session_maker() as session:
        #     async with session.begin():
        #         try:
        #             yield session
        #         except Exception as e:
        #             await session.rollback()
        #             logger.error(f"❌ SQL Transaction failed: {e}")
        #             raise e



SQL_DB_MANAGER = SQLDatabase()
